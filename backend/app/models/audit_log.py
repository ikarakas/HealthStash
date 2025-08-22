from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.core.database import Base

class AuditAction(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    FILE_VIEW = "file_view"
    RECORD_CREATE = "record_create"
    RECORD_UPDATE = "record_update"
    RECORD_DELETE = "record_delete"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SETTINGS_CHANGE = "settings_change"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    
    resource_type = Column(String, nullable=True)
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    user = relationship("User", back_populates="audit_logs")