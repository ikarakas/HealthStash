from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db, get_timescale_db
from app.models.user import User
from app.models.vital_signs import VitalSign, VitalType
from app.api.auth import get_current_user

router = APIRouter()

@router.post("/")
async def add_vital_sign(
    vital_type: VitalType,
    value: float,
    unit: str,
    recorded_at: datetime = None,
    notes: Optional[str] = None,
    source: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    vital = VitalSign(
        id=str(uuid.uuid4()),
        user_id=str(current_user.id),  # Convert to string
        vital_type=vital_type,
        value=value,
        unit=unit,
        notes=notes,
        source=source,
        recorded_at=recorded_at or datetime.utcnow()
    )
    
    db.add(vital)
    db.commit()
    
    return {"message": "Vital sign recorded", "id": vital.id}

@router.get("/")
async def list_vital_signs(
    vital_type: Optional[VitalType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    query = db.query(VitalSign).filter(VitalSign.user_id == str(current_user.id))
    
    if vital_type:
        query = query.filter(VitalSign.vital_type == vital_type)
    
    if start_date:
        query = query.filter(VitalSign.recorded_at >= start_date)
    else:
        # Default to last 30 days
        query = query.filter(VitalSign.recorded_at >= datetime.utcnow() - timedelta(days=30))
    
    if end_date:
        query = query.filter(VitalSign.recorded_at <= end_date)
    
    vitals = query.order_by(VitalSign.recorded_at.desc()).limit(limit).all()
    
    return vitals

@router.get("/latest")
async def get_latest_vitals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    latest = {}
    
    for vital_type in VitalType:
        latest_vital = db.query(VitalSign).filter(
            VitalSign.user_id == str(current_user.id),
            VitalSign.vital_type == vital_type
        ).order_by(VitalSign.recorded_at.desc()).first()
        
        if latest_vital:
            latest[vital_type.value] = {
                "value": latest_vital.value,
                "unit": latest_vital.unit,
                "recorded_at": latest_vital.recorded_at.isoformat(),
                "source": latest_vital.source
            }
    
    return latest

@router.get("/trends/{vital_type}")
async def get_vital_trends(
    vital_type: VitalType,
    period: str = "week",  # week, month, year
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    if period == "week":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == "month":
        start_date = datetime.utcnow() - timedelta(days=30)
    elif period == "year":
        start_date = datetime.utcnow() - timedelta(days=365)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    vitals = db.query(VitalSign).filter(
        VitalSign.user_id == str(current_user.id),
        VitalSign.vital_type == vital_type,
        VitalSign.recorded_at >= start_date
    ).order_by(VitalSign.recorded_at).all()
    
    data = [{
        "timestamp": v.recorded_at.isoformat(),
        "value": v.value,
        "unit": v.unit
    } for v in vitals]
    
    # Calculate statistics
    if vitals:
        values = [v.value for v in vitals]
        stats = {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values),
            "latest": values[-1]
        }
    else:
        stats = None
    
    return {
        "data": data,
        "stats": stats,
        "period": period
    }

@router.post("/import/apple-health")
async def import_apple_health(
    file: bytes,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    # Parse Apple Health export
    # This would parse the XML export file
    # For now, return a placeholder
    return {"message": "Apple Health import functionality to be implemented"}

@router.post("/import/google-fit")
async def import_google_fit(
    file: bytes,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    # Parse Google Fit export
    # This would parse the JSON export file
    # For now, return a placeholder
    return {"message": "Google Fit import functionality to be implemented"}