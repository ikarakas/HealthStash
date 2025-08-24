from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from datetime import datetime, date
import uuid
import json
import hashlib
from decimal import Decimal

from app.core.database import get_db
from app.core.security import (
    encrypt_file_content, decrypt_file_content,
    generate_file_checksum, derive_key_from_password
)
from app.core.config import settings
from app.api.auth import get_current_user
from app.models import User, PaymentRecord, PaymentFile, PaymentStatus, PaymentMethod, HealthRecord
from app.services.storage import StorageService
from app.services.thumbnail import generate_image_thumbnail, generate_pdf_thumbnail

router = APIRouter()
storage_service = StorageService()

@router.get("/")
async def get_payments(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[PaymentStatus] = None,
    health_record_id: Optional[str] = None,
    provider: Optional[str] = None,
    date_from: Optional[Union[date, datetime]] = None,
    date_to: Optional[Union[date, datetime]] = None,
    sort_by: str = Query("expense_date_desc", regex="^(expense_date|invoice_date|amount|created_at)_(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payment records for the current user with filtering and sorting"""
    query = db.query(PaymentRecord).filter(
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    )
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (PaymentRecord.invoice_number.ilike(search_filter)) |
            (PaymentRecord.provider_name.ilike(search_filter)) |
            (PaymentRecord.service_description.ilike(search_filter)) |
            (PaymentRecord.notes.ilike(search_filter))
        )
    
    if status:
        query = query.filter(PaymentRecord.payment_status == status)
    
    if health_record_id:
        query = query.filter(PaymentRecord.health_record_id == health_record_id)
    
    if provider:
        query = query.filter(PaymentRecord.provider_name.ilike(f"%{provider}%"))
    
    if date_from:
        if isinstance(date_from, date) and not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, datetime.min.time())
        query = query.filter(PaymentRecord.expense_date >= date_from)
    
    if date_to:
        if isinstance(date_to, date) and not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, datetime.max.time())  # End of day
        query = query.filter(PaymentRecord.expense_date <= date_to)
    
    # Apply sorting - use rsplit to handle fields with underscores
    sort_field, sort_order = sort_by.rsplit("_", 1)
    if sort_field == "expense_date":
        sort_field = "expense_date"
    elif sort_field == "invoice_date":
        sort_field = "invoice_date"
    elif sort_field == "created_at":
        sort_field = "created_at"
    elif sort_field == "amount":
        sort_field = "amount"
    
    order_by = getattr(PaymentRecord, sort_field)
    if sort_order == "desc":
        order_by = order_by.desc()
    
    query = query.order_by(order_by)
    
    total = query.count()
    payments = query.offset(skip).limit(limit).all()
    
    # Decrypt file information for each payment
    result = []
    for payment in payments:
        payment_dict = {
            "id": payment.id,
            "health_record_id": payment.health_record_id,
            "invoice_number": payment.invoice_number,
            "invoice_date": payment.invoice_date.isoformat() if payment.invoice_date else None,
            "expense_date": payment.expense_date.isoformat() if payment.expense_date else None,
            "amount": float(payment.amount),
            "currency": payment.currency,
            "payment_status": payment.payment_status.value if payment.payment_status else None,
            "payment_method": payment.payment_method.value if payment.payment_method else None,
            "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
            "provider_name": payment.provider_name,
            "provider_address": payment.provider_address,
            "service_description": payment.service_description,
            "insurance_claim_number": payment.insurance_claim_number,
            "insurance_paid_amount": float(payment.insurance_paid_amount) if payment.insurance_paid_amount else None,
            "patient_responsibility": float(payment.patient_responsibility) if payment.patient_responsibility else None,
            "notes": payment.notes,
            "created_at": payment.created_at.isoformat(),
            "updated_at": payment.updated_at.isoformat(),
            "files": []
        }
        
        # Add linked health record info if exists
        if payment.health_record:
            payment_dict["health_record"] = {
                "id": payment.health_record.id,
                "title": payment.health_record.title,
                "service_date": payment.health_record.service_date.isoformat() if payment.health_record.service_date else None
            }
        
        # Add file information
        for file in payment.files:
            payment_dict["files"].append({
                "id": file.id,
                "file_name": file.file_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "is_invoice": file.is_invoice,
                "is_receipt": file.is_receipt,
                "thumbnail_data": file.thumbnail_data,
                "uploaded_at": file.uploaded_at.isoformat()
            })
        
        result.append(payment_dict)
    
    return {
        "payments": result,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific payment record"""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    payment_dict = {
        "id": payment.id,
        "health_record_id": payment.health_record_id,
        "invoice_number": payment.invoice_number,
        "invoice_date": payment.invoice_date.isoformat() if payment.invoice_date else None,
        "expense_date": payment.expense_date.isoformat() if payment.expense_date else None,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "payment_status": payment.payment_status.value if payment.payment_status else None,
        "payment_method": payment.payment_method.value if payment.payment_method else None,
        "payment_date": payment.payment_date.isoformat() if payment.payment_date else None,
        "provider_name": payment.provider_name,
        "provider_address": payment.provider_address,
        "service_description": payment.service_description,
        "insurance_claim_number": payment.insurance_claim_number,
        "insurance_paid_amount": float(payment.insurance_paid_amount) if payment.insurance_paid_amount else None,
        "patient_responsibility": float(payment.patient_responsibility) if payment.patient_responsibility else None,
        "notes": payment.notes,
        "metadata": json.loads(payment.metadata_json) if payment.metadata_json else {},
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
        "files": []
    }
    
    # Add linked health record info if exists
    if payment.health_record:
        payment_dict["health_record"] = {
            "id": payment.health_record.id,
            "title": payment.health_record.title,
            "service_date": payment.health_record.service_date.isoformat() if payment.health_record.service_date else None,
            "category": payment.health_record.category.value if payment.health_record.category else None
        }
    
    # Add file information
    for file in payment.files:
        payment_dict["files"].append({
            "id": file.id,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "is_invoice": file.is_invoice,
            "is_receipt": file.is_receipt,
            "thumbnail_data": file.thumbnail_data,
            "uploaded_at": file.uploaded_at.isoformat()
        })
    
    return payment_dict

@router.post("/")
async def create_payment(
    amount: float = Form(...),
    currency: str = Form("EUR"),
    invoice_number: Optional[str] = Form(None),
    invoice_date: Optional[Union[date, datetime]] = Form(None),
    expense_date: Optional[Union[date, datetime]] = Form(None),
    payment_status: Optional[str] = Form("pending"),
    payment_method: Optional[str] = Form(None),
    payment_date: Optional[Union[date, datetime]] = Form(None),
    provider_name: Optional[str] = Form(None),
    provider_address: Optional[str] = Form(None),
    service_description: Optional[str] = Form(None),
    health_record_id: Optional[str] = Form(None),
    insurance_claim_number: Optional[str] = Form(None),
    insurance_paid_amount: Optional[float] = Form(None),
    patient_responsibility: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    files: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment record with optional file uploads"""
    
    # Validate health record if provided
    if health_record_id:
        health_record = db.query(HealthRecord).filter(
            HealthRecord.id == health_record_id,
            HealthRecord.user_id == current_user.id,
            HealthRecord.is_deleted == False
        ).first()
        if not health_record:
            raise HTTPException(status_code=404, detail="Health record not found")
    
    # Convert date to datetime if needed
    if isinstance(invoice_date, date) and not isinstance(invoice_date, datetime):
        invoice_date = datetime.combine(invoice_date, datetime.min.time())
    if isinstance(expense_date, date) and not isinstance(expense_date, datetime):
        expense_date = datetime.combine(expense_date, datetime.min.time())
    if isinstance(payment_date, date) and not isinstance(payment_date, datetime):
        payment_date = datetime.combine(payment_date, datetime.min.time())
    
    # Create payment record
    payment_id = str(uuid.uuid4())
    payment = PaymentRecord(
        id=payment_id,
        user_id=current_user.id,
        health_record_id=health_record_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        expense_date=expense_date,
        amount=Decimal(str(amount)),
        currency=currency,
        payment_status=PaymentStatus(payment_status) if payment_status else PaymentStatus.PENDING,
        payment_method=PaymentMethod(payment_method) if payment_method else None,
        payment_date=payment_date,
        provider_name=provider_name,
        provider_address=provider_address,
        service_description=service_description,
        insurance_claim_number=insurance_claim_number,
        insurance_paid_amount=Decimal(str(insurance_paid_amount)) if insurance_paid_amount else None,
        patient_responsibility=Decimal(str(patient_responsibility)) if patient_responsibility else None,
        notes=notes
    )
    
    db.add(payment)
    
    # Process uploaded files
    if files:
        for file in files:
            if file.filename:
                # Read file content
                content = await file.read()
                
                # Generate checksum
                file_checksum = generate_file_checksum(content)
                
                # Generate user encryption key
                user_key = derive_key_from_password(
                    f"{current_user.id}:{current_user.hashed_password}:{settings.ENCRYPTION_KEY}",
                    current_user.encryption_salt
                )
                
                # Encrypt file content
                encrypted_content = encrypt_file_content(content, user_key)
                
                # Generate unique object name for MinIO
                object_name = f"payments/{current_user.id}/{payment_id}/{uuid.uuid4()}_{file.filename}"
                
                # Upload to MinIO
                success = await storage_service.upload_file(encrypted_content, object_name)
                
                if success:
                    # Generate thumbnail if applicable
                    thumbnail_data = None
                    if file.content_type and file.content_type.startswith('image/'):
                        thumbnail_data = generate_image_thumbnail(content)
                    elif file.content_type == 'application/pdf':
                        thumbnail_data = generate_pdf_thumbnail(content)
                    
                    # Create payment file record
                    payment_file = PaymentFile(
                        id=str(uuid.uuid4()),
                        payment_record_id=payment_id,
                        file_name=file.filename,
                        file_type=file.content_type,
                        file_size=len(content),
                        file_checksum=file_checksum,
                        encrypted_file_key="",  # Key is derived from user password
                        minio_object_name=object_name,
                        thumbnail_data=thumbnail_data,
                        is_invoice=True,  # Default to invoice, can be updated later
                        is_receipt=False
                    )
                    
                    db.add(payment_file)
    
    db.commit()
    db.refresh(payment)
    
    return {"id": payment.id, "message": "Payment record created successfully"}

@router.put("/{payment_id}")
async def update_payment(
    payment_id: str,
    amount: Optional[float] = Form(None),
    currency: Optional[str] = Form(None),
    invoice_number: Optional[str] = Form(None),
    invoice_date: Optional[Union[date, datetime]] = Form(None),
    expense_date: Optional[Union[date, datetime]] = Form(None),
    payment_status: Optional[str] = Form(None),
    payment_method: Optional[str] = Form(None),
    payment_date: Optional[Union[date, datetime]] = Form(None),
    provider_name: Optional[str] = Form(None),
    provider_address: Optional[str] = Form(None),
    service_description: Optional[str] = Form(None),
    health_record_id: Optional[str] = Form(None),
    insurance_claim_number: Optional[str] = Form(None),
    insurance_paid_amount: Optional[float] = Form(None),
    patient_responsibility: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing payment record"""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    # Validate health record if provided
    if health_record_id is not None:
        if health_record_id:  # If not empty string
            health_record = db.query(HealthRecord).filter(
                HealthRecord.id == health_record_id,
                HealthRecord.user_id == current_user.id,
                HealthRecord.is_deleted == False
            ).first()
            if not health_record:
                raise HTTPException(status_code=404, detail="Health record not found")
        payment.health_record_id = health_record_id if health_record_id else None
    
    # Update fields
    if amount is not None:
        payment.amount = Decimal(str(amount))
    if currency is not None:
        payment.currency = currency
    if invoice_number is not None:
        payment.invoice_number = invoice_number
    if invoice_date is not None:
        if isinstance(invoice_date, date) and not isinstance(invoice_date, datetime):
            invoice_date = datetime.combine(invoice_date, datetime.min.time())
        payment.invoice_date = invoice_date
    if expense_date is not None:
        if isinstance(expense_date, date) and not isinstance(expense_date, datetime):
            expense_date = datetime.combine(expense_date, datetime.min.time())
        payment.expense_date = expense_date
    if payment_status is not None:
        payment.payment_status = PaymentStatus(payment_status)
    if payment_method is not None:
        payment.payment_method = PaymentMethod(payment_method) if payment_method else None
    if payment_date is not None:
        if isinstance(payment_date, date) and not isinstance(payment_date, datetime):
            payment_date = datetime.combine(payment_date, datetime.min.time())
        payment.payment_date = payment_date
    if provider_name is not None:
        payment.provider_name = provider_name
    if provider_address is not None:
        payment.provider_address = provider_address
    if service_description is not None:
        payment.service_description = service_description
    if insurance_claim_number is not None:
        payment.insurance_claim_number = insurance_claim_number
    if insurance_paid_amount is not None:
        payment.insurance_paid_amount = Decimal(str(insurance_paid_amount)) if insurance_paid_amount else None
    if patient_responsibility is not None:
        payment.patient_responsibility = Decimal(str(patient_responsibility)) if patient_responsibility else None
    if notes is not None:
        payment.notes = notes
    
    payment.updated_at = datetime.now()
    
    db.commit()
    db.refresh(payment)
    
    return {"message": "Payment record updated successfully"}

@router.post("/{payment_id}/files")
async def add_payment_files(
    payment_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add files to an existing payment record"""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    uploaded_files = []
    
    for file in files:
        if file.filename:
            # Read file content
            content = await file.read()
            
            # Generate checksum
            file_checksum = generate_file_checksum(content)
            
            # Generate user encryption key
            user_key = derive_key_from_password(
                f"{current_user.id}:{current_user.hashed_password}:{settings.ENCRYPTION_KEY}",
                current_user.encryption_salt
            )
            
            # Encrypt file content
            encrypted_content = encrypt_file_content(content, user_key)
            
            # Generate unique object name for MinIO
            object_name = f"payments/{current_user.id}/{payment_id}/{uuid.uuid4()}_{file.filename}"
            
            # Upload to MinIO
            success = await storage_service.upload_file(encrypted_content, object_name)
            
            if success:
                # Generate thumbnail if applicable
                thumbnail_data = None
                if file.content_type and file.content_type.startswith('image/'):
                    thumbnail_data = thumbnail_service.generate_thumbnail(content, file.content_type)
                elif file.content_type == 'application/pdf':
                    thumbnail_data = thumbnail_service.generate_pdf_thumbnail(content)
                
                # Create payment file record
                payment_file = PaymentFile(
                    id=str(uuid.uuid4()),
                    payment_record_id=payment_id,
                    file_name=file.filename,
                    file_type=file.content_type,
                    file_size=len(content),
                    file_checksum=file_checksum,
                    encrypted_file_key="",  # Key is derived from user password
                    minio_object_name=object_name,
                    thumbnail_data=thumbnail_data,
                    is_invoice=True,
                    is_receipt=False
                )
                
                db.add(payment_file)
                uploaded_files.append(file.filename)
    
    db.commit()
    
    return {"message": f"Successfully uploaded {len(uploaded_files)} files", "files": uploaded_files}

@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a payment record"""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    payment.is_deleted = True
    payment.deleted_at = datetime.now()
    
    db.commit()
    
    return {"message": "Payment record deleted successfully"}

@router.get("/{payment_id}/files/{file_id}/download")
async def download_payment_file(
    payment_id: str,
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a file from a payment record"""
    payment = db.query(PaymentRecord).filter(
        PaymentRecord.id == payment_id,
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    
    payment_file = db.query(PaymentFile).filter(
        PaymentFile.id == file_id,
        PaymentFile.payment_record_id == payment_id
    ).first()
    
    if not payment_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Download from MinIO
    encrypted_content = await storage_service.download_file(payment_file.minio_object_name)
    
    if not encrypted_content:
        raise HTTPException(status_code=404, detail="File content not found in storage")
    
    # Generate user encryption key
    user_key = derive_key_from_password(
        f"{current_user.id}:{current_user.hashed_password}:{settings.ENCRYPTION_KEY}",
        current_user.encryption_salt
    )
    
    # Decrypt content
    decrypted_content = decrypt_file_content(encrypted_content, user_key)
    
    from fastapi.responses import Response
    
    return Response(
        content=decrypted_content,
        media_type=payment_file.file_type or 'application/octet-stream',
        headers={
            "Content-Disposition": f"attachment; filename={payment_file.file_name}"
        }
    )

@router.get("/stats/summary")
async def get_payment_summary(
    date_from: Optional[Union[date, datetime]] = None,
    date_to: Optional[Union[date, datetime]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment summary statistics for the current user"""
    query = db.query(PaymentRecord).filter(
        PaymentRecord.user_id == current_user.id,
        PaymentRecord.is_deleted == False
    )
    
    if date_from:
        if isinstance(date_from, date) and not isinstance(date_from, datetime):
            date_from = datetime.combine(date_from, datetime.min.time())
        query = query.filter(PaymentRecord.expense_date >= date_from)
    
    if date_to:
        if isinstance(date_to, date) and not isinstance(date_to, datetime):
            date_to = datetime.combine(date_to, datetime.max.time())
        query = query.filter(PaymentRecord.expense_date <= date_to)
    
    payments = query.all()
    
    total_amount = sum(p.amount for p in payments)
    total_insurance_paid = sum(p.insurance_paid_amount for p in payments if p.insurance_paid_amount)
    total_patient_responsibility = sum(p.patient_responsibility for p in payments if p.patient_responsibility)
    
    # Group by status
    status_summary = {}
    for status in PaymentStatus:
        status_payments = [p for p in payments if p.payment_status == status]
        status_summary[status.value] = {
            "count": len(status_payments),
            "total": float(sum(p.amount for p in status_payments))
        }
    
    # Group by provider
    provider_summary = {}
    for payment in payments:
        if payment.provider_name:
            if payment.provider_name not in provider_summary:
                provider_summary[payment.provider_name] = {
                    "count": 0,
                    "total": 0
                }
            provider_summary[payment.provider_name]["count"] += 1
            provider_summary[payment.provider_name]["total"] += float(payment.amount)
    
    return {
        "total_amount": float(total_amount),
        "total_insurance_paid": float(total_insurance_paid),
        "total_patient_responsibility": float(total_patient_responsibility),
        "total_payments": len(payments),
        "status_summary": status_summary,
        "provider_summary": provider_summary
    }