from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, Enum, Table, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

record_tags = Table(
    'record_tags',
    Base.metadata,
    Column('record_id', String, ForeignKey('health_records.id')),
    Column('tag_id', String, ForeignKey('tags.id'))
)

class RecordCategory(enum.Enum):
    LAB_RESULTS = "lab_results"
    IMAGING = "imaging"
    CLINICAL_NOTES = "clinical_notes"
    PRESCRIPTIONS = "prescriptions"
    VACCINATIONS = "vaccinations"
    PERSONAL_NOTES = "personal_notes"
    VITAL_SIGNS = "vital_signs"
    OTHER = "other"

class HealthRecord(Base):
    __tablename__ = "health_records"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(RecordCategory, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_checksum = Column(String, nullable=True)
    encrypted_file_key = Column(String, nullable=True)
    minio_object_name = Column(String, nullable=True)
    
    provider_name = Column(String, nullable=True)
    service_date = Column(DateTime, nullable=True, index=True)
    
    content_text = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="health_records")
    tags = relationship("RecordTag", secondary=record_tags, back_populates="records")

class RecordTag(Base):
    __tablename__ = "tags"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    color = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    records = relationship("HealthRecord", secondary=record_tags, back_populates="tags")