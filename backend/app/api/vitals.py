from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import json

from app.core.database import get_timescale_db
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()

class VitalSignCreate(BaseModel):
    vital_type: str
    value: float
    unit: str
    recorded_at: Optional[datetime] = None
    notes: Optional[str] = None
    source: Optional[str] = None

@router.post("/")
async def add_vital_sign(
    vital_data: VitalSignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        vital_id = str(uuid.uuid4())
        recorded_time = vital_data.recorded_at or datetime.utcnow()
        
        # Use raw SQL for TimescaleDB
        query = text("""
            INSERT INTO vital_signs (id, user_id, vital_type, value, unit, notes, source, recorded_at, time)
            VALUES (:id, :user_id, :vital_type, :value, :unit, :notes, :source, :recorded_at, :time)
        """)
        
        db.execute(query, {
            "id": vital_id,
            "user_id": str(current_user.id),
            "vital_type": vital_data.vital_type,
            "value": vital_data.value,
            "unit": vital_data.unit,
            "notes": vital_data.notes,
            "source": vital_data.source,
            "recorded_at": recorded_time,
            "time": recorded_time
        })
        db.commit()
        
        return {"message": "Vital sign recorded", "id": vital_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_vital_signs(
    vital_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=100, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        # Build query
        conditions = ["user_id = :user_id"]
        params = {"user_id": str(current_user.id)}
        
        if vital_type:
            conditions.append("vital_type = :vital_type")
            params["vital_type"] = vital_type
        
        if start_date:
            conditions.append("recorded_at >= :start_date")
            params["start_date"] = start_date
        else:
            # Default to last 30 days
            conditions.append("recorded_at >= :start_date")
            params["start_date"] = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            conditions.append("recorded_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(conditions)
        
        query = text(f"""
            SELECT id, user_id, vital_type, value, unit, notes, source, recorded_at, created_at
            FROM vital_signs
            WHERE {where_clause}
            ORDER BY recorded_at DESC
            LIMIT :limit
        """)
        params["limit"] = limit
        
        result = db.execute(query, params)
        vitals = []
        for row in result:
            vitals.append({
                "id": row[0],
                "user_id": row[1],
                "vital_type": row[2],
                "value": row[3],
                "unit": row[4],
                "notes": row[5],
                "source": row[6],
                "recorded_at": row[7].isoformat() if row[7] else None,
                "created_at": row[8].isoformat() if row[8] else None
            })
        
        return vitals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
async def get_latest_vitals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        vital_types = [
            "heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic",
            "weight", "temperature", "blood_glucose", "oxygen_saturation"
        ]
        
        latest = {}
        for vtype in vital_types:
            query = text("""
                SELECT value, unit, recorded_at, source
                FROM vital_signs
                WHERE user_id = :user_id AND vital_type = :vital_type
                ORDER BY recorded_at DESC
                LIMIT 1
            """)
            
            result = db.execute(query, {
                "user_id": str(current_user.id),
                "vital_type": vtype
            }).first()
            
            if result:
                latest[vtype] = {
                    "value": result[0],
                    "unit": result[1],
                    "recorded_at": result[2].isoformat() if result[2] else None,
                    "source": result[3]
                }
        
        return latest
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{vital_type}")
async def get_vital_trends(
    vital_type: str,
    period: str = "week",  # week, month, year
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        if period == "week":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "month":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "year":
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        query = text("""
            SELECT recorded_at, value, unit
            FROM vital_signs
            WHERE user_id = :user_id 
                AND vital_type = :vital_type
                AND recorded_at >= :start_date
            ORDER BY recorded_at ASC
        """)
        
        result = db.execute(query, {
            "user_id": str(current_user.id),
            "vital_type": vital_type,
            "start_date": start_date
        })
        
        data = []
        values = []
        for row in result:
            data.append({
                "timestamp": row[0].isoformat() if row[0] else None,
                "value": row[1],
                "unit": row[2]
            })
            values.append(row[1])
        
        # Calculate statistics
        stats = None
        if values:
            stats = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values),
                "latest": values[-1] if values else None
            }
        
        return {
            "data": data,
            "stats": stats,
            "period": period
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/all")
async def delete_all_vitals(
    vital_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        if vital_type:
            # Delete specific vital type
            query = text("""
                DELETE FROM vital_signs 
                WHERE user_id = :user_id AND vital_type = :vital_type
            """)
            result = db.execute(query, {
                "user_id": str(current_user.id),
                "vital_type": vital_type
            })
        else:
            # Delete all vitals for user
            query = text("""
                DELETE FROM vital_signs 
                WHERE user_id = :user_id
            """)
            result = db.execute(query, {
                "user_id": str(current_user.id)
            })
        
        db.commit()
        deleted_count = result.rowcount
        
        return {
            "message": f"Deleted {deleted_count} vital signs",
            "count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{vital_id}")
async def delete_vital_sign(
    vital_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_timescale_db)
):
    try:
        # Delete specific vital sign
        query = text("""
            DELETE FROM vital_signs 
            WHERE id = :id AND user_id = :user_id
        """)
        result = db.execute(query, {
            "id": vital_id,
            "user_id": str(current_user.id)
        })
        
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vital sign not found")
        
        return {"message": "Vital sign deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))