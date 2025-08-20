from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.health_record import HealthRecord, RecordCategory
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/")
async def list_records(
    category: Optional[RecordCategory] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    )
    
    if category:
        query = query.filter(HealthRecord.category == category)
    
    if start_date:
        query = query.filter(HealthRecord.service_date >= start_date)
    
    if end_date:
        query = query.filter(HealthRecord.service_date <= end_date)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (HealthRecord.title.ilike(search_term)) |
            (HealthRecord.description.ilike(search_term)) |
            (HealthRecord.provider_name.ilike(search_term)) |
            (HealthRecord.content_text.ilike(search_term))
        )
    
    total = query.count()
    records = query.order_by(HealthRecord.service_date.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "records": records,
        "limit": limit,
        "offset": offset
    }

@router.get("/timeline")
async def get_timeline(
    months: int = 12,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    records = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False,
        HealthRecord.service_date >= start_date
    ).order_by(HealthRecord.service_date.desc()).all()
    
    # Group by month
    timeline = {}
    for record in records:
        if record.service_date:
            month_key = record.service_date.strftime("%Y-%m")
            if month_key not in timeline:
                timeline[month_key] = []
            timeline[month_key].append({
                "id": record.id,
                "title": record.title,
                "category": record.category.value,
                "date": record.service_date.isoformat(),
                "provider": record.provider_name
            })
    
    return timeline

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = {}
    
    # Count by category
    from sqlalchemy import func
    categories = db.query(
        HealthRecord.category,
        func.count(HealthRecord.id)
    ).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).group_by(HealthRecord.category).all()
    
    stats["categories"] = {cat.value: count for cat, count in categories}
    
    # Storage usage
    stats["storage"] = {
        "used_mb": current_user.storage_used_mb,
        "quota_mb": current_user.storage_quota_mb,
        "percentage": (current_user.storage_used_mb / current_user.storage_quota_mb * 100) if current_user.storage_quota_mb > 0 else 0
    }
    
    # Recent uploads
    stats["recent_uploads"] = db.query(HealthRecord).filter(
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).order_by(HealthRecord.created_at.desc()).limit(5).all()
    
    return stats