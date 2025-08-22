from sqlalchemy import Column, String, DateTime, Integer, Float, Enum, Text, Boolean
from datetime import datetime, timezone
import enum

from app.core.database import Base

class BackupType(enum.Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    USER_DATA = "user_data"

class BackupStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class BackupHistory(Base):
    __tablename__ = "backup_history"
    
    id = Column(String, primary_key=True, index=True)
    backup_type = Column(Enum(BackupType), nullable=False)
    status = Column(Enum(BackupStatus), nullable=False, default=BackupStatus.PENDING)
    
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    size_mb = Column(Float, nullable=True)  # Size in MB for display
    checksum = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Duration in seconds
    
    includes_database = Column(Boolean, default=True)
    includes_files = Column(Boolean, default=True)
    includes_config = Column(Boolean, default=False)
    
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)