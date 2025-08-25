from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import json
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.health_record import HealthRecord, RecordCategory
from app.models.payment_record import PaymentRecord
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class UpdateCategoriesRequest(BaseModel):
    categories: List[str]

class UpdateTitleRequest(BaseModel):
    title: str

class UpdateLocationRequest(BaseModel):
    location: str

class UpdateBodyPartsRequest(BaseModel):
    body_parts: List[str]

class CreateRecordRequest(BaseModel):
    title: str
    category: str  # Changed to str to accept string values
    description: Optional[str] = ""
    provider_name: Optional[str] = ""
    location: Optional[str] = ""
    service_date: Optional[datetime] = None
    content_text: Optional[str] = ""

@router.post("/")
async def create_record(
    record_data: CreateRecordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import uuid
    
    logger.info(f"Creating record with data: {record_data.dict()}")
    
    # Convert string category to enum
    try:
        category_enum = RecordCategory(record_data.category)
    except ValueError as e:
        logger.warning(f"Invalid category '{record_data.category}', using OTHER. Error: {e}")
        # Fallback to OTHER if invalid category
        category_enum = RecordCategory.OTHER
    
    # Create new health record
    new_record = HealthRecord(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=record_data.title,
        category=category_enum,
        description=record_data.description or "",
        provider_name=record_data.provider_name or "",
        location=record_data.location or "",
        service_date=record_data.service_date,
        content_text=record_data.content_text or "",
        is_deleted=False
    )
    
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    
    return {
        "id": new_record.id,
        "title": new_record.title,
        "category": new_record.category.value if new_record.category else None,
        "description": new_record.description,
        "provider_name": new_record.provider_name,
        "location": new_record.location,
        "service_date": new_record.service_date.isoformat() if new_record.service_date else None,
        "content_text": new_record.content_text,
        "created_at": new_record.created_at.isoformat() if new_record.created_at else None
    }

@router.get("/")
async def list_records(
    category: Optional[RecordCategory] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=1000),
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
    records = query.order_by(HealthRecord.created_at.desc()).offset(offset).limit(limit).all()
    
    # Serialize records to include dates properly
    serialized_records = []
    for record in records:
        # Count associated payments
        payment_count = db.query(PaymentRecord).filter(
            PaymentRecord.health_record_id == record.id,
            PaymentRecord.is_deleted == False
        ).count()
        
        serialized_records.append({
            "id": record.id,
            "title": record.title,
            "description": record.description,
            "category": record.category.value if record.category else None,
            "file_name": record.file_name,
            "file_type": record.file_type,
            "file_size": record.file_size,
            "provider_name": record.provider_name,
            "location": record.location,
            "body_parts": record.body_parts.split(',') if record.body_parts and record.body_parts.strip() else [],
            "service_date": record.service_date.isoformat() if record.service_date else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
            "is_deleted": record.is_deleted,
            "categories": record.categories.split(',') if record.categories and record.categories.strip() else [record.category.value if record.category else None],
            "has_thumbnail": record.has_thumbnail if hasattr(record, 'has_thumbnail') else False,
            "payment_count": payment_count
        })
    
    return {
        "total": total,
        "records": serialized_records,
        "limit": limit,
        "offset": offset
    }

@router.get("/timeline")
async def get_timeline(
    months: int = 12,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
    
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

@router.patch("/{record_id}/title")
async def update_record_title(
    record_id: str,
    request: UpdateTitleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Validate title
    if not request.title or len(request.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    
    if len(request.title) > 255:
        raise HTTPException(status_code=400, detail="Title too long (max 255 characters)")
    
    # Update title
    record.title = request.title.strip()
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Title updated successfully", "title": record.title}

@router.patch("/{record_id}/location")
async def update_record_location(
    record_id: str,
    request: UpdateLocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update location (can be empty)
    record.location = request.location.strip() if request.location else None
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Location updated successfully", "location": record.location}

@router.patch("/{record_id}/body-parts")
async def update_record_body_parts(
    record_id: str,
    request: UpdateBodyPartsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update body parts (store as JSON)
    record.body_parts = json.dumps(request.body_parts) if request.body_parts else None
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    
    return {"message": "Body parts updated successfully", "body_parts": request.body_parts}

@router.patch("/{record_id}/categories")
async def update_record_categories(
    record_id: str,
    request: UpdateCategoriesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Validate categories
    valid_categories = [cat.value for cat in RecordCategory]
    for cat in request.categories:
        if cat not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Invalid category: {cat}")
    
    # Update categories
    record.categories = json.dumps(request.categories)
    # Keep the primary category as the first one
    if request.categories:
        try:
            record.category = RecordCategory(request.categories[0])
        except:
            pass
    
    db.commit()
    
    return {"message": "Categories updated successfully"}

@router.get("/{record_id}/thumbnail")
async def get_record_thumbnail(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Getting thumbnail for record {record_id} for user {current_user.id}")
    
    record = db.query(HealthRecord).options(
        joinedload(HealthRecord.user)
    ).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id,
        HealthRecord.is_deleted == False
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if not record.has_thumbnail or not record.thumbnail_data:
        # Try to generate thumbnail if it's an image
        if record.file_type and record.file_type.startswith('image/'):
            # Generate thumbnail on the fly
            from app.services.thumbnail import generate_thumbnail
            try:
                thumbnail = await generate_thumbnail(record)
                if thumbnail:
                    record.thumbnail_data = thumbnail
                    record.has_thumbnail = True
                    db.commit()
                    return {"thumbnail": thumbnail}
            except Exception as e:
                logger.error(f"Failed to generate thumbnail: {e}")
                # Return a placeholder for images that fail
                return {"thumbnail": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICAgIDxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjZjhmOWZhIi8+CiAgICA8dGV4dCB4PSIxMDAiIHk9IjEwMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjYwIiBmaWxsPSIjY2JkNWUwIj7wn5ayPC90ZXh0Pgo8L3N2Zz4="}
        
        raise HTTPException(status_code=404, detail="No thumbnail available")
    
    return {"thumbnail": record.thumbnail_data}