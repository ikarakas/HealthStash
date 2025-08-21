from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import get_password_hash, generate_user_encryption_key
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog, AuditAction
from app.api.auth import get_admin_user
from app.schemas.auth import UserCreate, UserResponse
from app.core.config import settings

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create new user
    user_id = str(uuid.uuid4())
    encryption_key, salt = generate_user_encryption_key(user_id, user_data.password)
    
    new_user = User(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.USER,
        encryption_salt=salt,
        storage_quota_mb=settings.DEFAULT_USER_QUOTA_MB
    )
    
    db.add(new_user)
    
    # Add audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=admin_user.id,
        action=AuditAction.USER_CREATE,
        resource_type="user",
        resource_id=user_id,
        details=f"Created user {user_data.username}"
    )
    db.add(audit)
    db.commit()
    
    # Return user data with proper serialization
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": new_user.role.value,
        "is_active": new_user.is_active,
        "storage_quota_mb": new_user.storage_quota_mb,
        "storage_used_mb": new_user.storage_used_mb,
        "created_at": new_user.created_at,
        "last_login": new_user.last_login
    }

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate new encryption key with new password
    encryption_key, salt = generate_user_encryption_key(user_id, new_password)
    
    user.hashed_password = get_password_hash(new_password)
    user.encryption_salt = salt
    user.password_changed_at = datetime.utcnow()
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_until = None
    
    # Add audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=admin_user.id,
        action=AuditAction.PASSWORD_CHANGE,
        resource_type="user",
        resource_id=user_id,
        details=f"Admin reset password for {user.username}"
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/stats")
async def get_system_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    stats = {}
    
    # User statistics
    stats["users"] = {
        "total": db.query(User).count(),
        "active": db.query(User).filter(User.is_active == True).count(),
        "locked": db.query(User).filter(User.is_locked == True).count(),
        "admins": db.query(User).filter(User.role == UserRole.ADMIN).count()
    }
    
    # Storage statistics
    total_storage = db.query(func.sum(User.storage_used_mb)).scalar() or 0
    total_quota = db.query(func.sum(User.storage_quota_mb)).scalar() or 0
    
    stats["storage"] = {
        "total_used_mb": total_storage,
        "total_quota_mb": total_quota,
        "percentage": (total_storage / total_quota * 100) if total_quota > 0 else 0
    }
    
    # Activity statistics
    last_24h = datetime.utcnow() - timedelta(hours=24)
    last_7d = datetime.utcnow() - timedelta(days=7)
    
    stats["activity"] = {
        "logins_24h": db.query(AuditLog).filter(
            AuditLog.action == AuditAction.LOGIN,
            AuditLog.created_at >= last_24h
        ).count(),
        "uploads_7d": db.query(AuditLog).filter(
            AuditLog.action == AuditAction.FILE_UPLOAD,
            AuditLog.created_at >= last_7d
        ).count(),
        "failed_logins_24h": db.query(AuditLog).filter(
            AuditLog.action == AuditAction.LOGIN_FAILED,
            AuditLog.created_at >= last_24h
        ).count()
    }
    
    return stats

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: Optional[AuditAction] = None,
    user_id: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "logs": logs,
        "limit": limit,
        "offset": offset
    }

@router.post("/maintenance/cleanup")
async def cleanup_deleted_records(
    days_old: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Permanently delete soft-deleted records older than cutoff
    from app.models.health_record import HealthRecord
    
    deleted_count = db.query(HealthRecord).filter(
        HealthRecord.is_deleted == True,
        HealthRecord.deleted_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {"message": f"Cleaned up {deleted_count} deleted records"}