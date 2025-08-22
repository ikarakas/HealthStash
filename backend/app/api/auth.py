from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import uuid

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, validate_password_strength,
    generate_user_encryption_key
)
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog, AuditAction
from app.schemas.auth import Token, TokenData, UserCreate, UserLogin, PasswordChange
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    if user.is_locked and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Account is locked")
    
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    user_id = str(uuid.uuid4())
    encryption_key, salt = generate_user_encryption_key(user_id, user_data.password)
    
    first_user = db.query(User).first() is None
    
    db_user = User(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        role=UserRole.ADMIN if first_user else UserRole.USER,
        encryption_salt=salt,
        storage_quota_mb=settings.DEFAULT_USER_QUOTA_MB
    )
    
    db.add(db_user)
    
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=AuditAction.USER_CREATE,
        resource_type="user",
        resource_id=user_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_locked and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account locked until {user.locked_until}",
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.now(timezone.utc)
        
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            action=AuditAction.LOGIN_FAILED,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.is_locked = False
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user.id,
        action=AuditAction.LOGIN,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = verify_token(refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    is_valid, message = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    encryption_key, salt = generate_user_encryption_key(current_user.id, password_data.new_password)
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.encryption_salt = salt
    current_user.password_changed_at = datetime.now(timezone.utc)
    
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action=AuditAction.PASSWORD_CHANGE,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    audit_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action=AuditAction.LOGOUT,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Logged out successfully"}