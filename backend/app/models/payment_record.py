from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, Enum, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.core.database import Base

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    INSURANCE = "insurance"
    CHECK = "check"
    WIRE_TRANSFER = "wire_transfer"
    OTHER = "other"

class PaymentRecord(Base):
    __tablename__ = "payment_records"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    health_record_id = Column(String, ForeignKey("health_records.id"), nullable=True, index=True)
    
    # Invoice details
    invoice_number = Column(String, nullable=True, index=True)
    invoice_date = Column(DateTime, nullable=True, index=True)
    expense_date = Column(DateTime, nullable=True, index=True)
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    payment_status = Column(
        Enum(PaymentStatus, values_callable=lambda x: [e.value for e in x]), 
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_method = Column(
        Enum(PaymentMethod, values_callable=lambda x: [e.value for e in x]),
        nullable=True
    )
    payment_date = Column(DateTime, nullable=True)
    
    # Provider details
    provider_name = Column(String, nullable=True, index=True)
    provider_address = Column(Text, nullable=True)
    service_description = Column(Text, nullable=True)
    
    # File storage (encrypted)
    encrypted_files_json = Column(Text, nullable=True)  # JSON array of encrypted file info
    
    # Additional fields
    insurance_claim_number = Column(String, nullable=True)
    insurance_paid_amount = Column(Numeric(10, 2), nullable=True)
    patient_responsibility = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    
    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="payment_records")
    health_record = relationship("HealthRecord", back_populates="payment_records")

class PaymentFile(Base):
    __tablename__ = "payment_files"
    
    id = Column(String, primary_key=True, index=True)
    payment_record_id = Column(String, ForeignKey("payment_records.id"), nullable=False, index=True)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_checksum = Column(String, nullable=True)
    encrypted_file_key = Column(String, nullable=True)
    minio_object_name = Column(String, nullable=True)
    thumbnail_data = Column(Text, nullable=True)  # Base64 encoded thumbnail for images/PDFs
    
    is_receipt = Column(Boolean, default=False, nullable=False)
    is_invoice = Column(Boolean, default=True, nullable=False)
    
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship
    payment_record = relationship("PaymentRecord", backref="files")