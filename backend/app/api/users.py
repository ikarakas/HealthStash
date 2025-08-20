from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user, get_admin_user
from app.schemas.auth import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    # Convert the user object to dict and ensure role is serialized as string
    user_dict = {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,  # Get the string value of the enum
        "is_active": current_user.is_active,
        "storage_quota_mb": current_user.storage_quota_mb,
        "storage_used_mb": current_user.storage_used_mb,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }
    return user_dict

@router.get("/", response_model=List[UserResponse])
async def list_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users

@router.put("/{user_id}/quota")
async def update_user_quota(
    user_id: str,
    quota_mb: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.storage_quota_mb = quota_mb
    db.commit()
    
    return {"message": "Quota updated successfully"}

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    if admin_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}