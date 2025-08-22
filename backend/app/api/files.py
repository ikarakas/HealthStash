from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
import io
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    encrypt_file_content, decrypt_file_content,
    generate_secure_filename, generate_file_checksum,
    derive_key_from_password, sanitize_filename
)
from app.models.user import User
from app.models.health_record import HealthRecord, RecordCategory
from app.models.audit_log import AuditLog, AuditAction
from app.api.auth import get_current_user
from app.services.storage import storage_service

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = "other",
    title: str = None,
    description: str = None,
    provider_name: str = None,
    service_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check file size
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB")
    
    # Check user quota
    if current_user.storage_used_mb + (file_size / 1024 / 1024) > current_user.storage_quota_mb:
        raise HTTPException(status_code=507, detail="Storage quota exceeded")
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")
    
    # Generate user encryption key
    user_key = derive_key_from_password(
        f"{current_user.id}:{current_user.hashed_password}:{settings.ENCRYPTION_KEY}",
        current_user.encryption_salt
    )
    
    # Encrypt file content
    encrypted_content = encrypt_file_content(contents, user_key)
    
    # Generate secure filename
    secure_name = generate_secure_filename(file.filename)
    
    # Calculate checksum
    checksum = generate_file_checksum(contents)
    
    # Upload to MinIO
    object_name = f"{current_user.id}/{secure_name}"
    success = await storage_service.upload_file(encrypted_content, object_name)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload file")
    
    # Create database record
    # Convert string category to enum
    try:
        if category.upper() == "LAB_RESULTS":
            category_enum = RecordCategory.LAB_RESULTS
        elif category.upper() == "IMAGING":
            category_enum = RecordCategory.IMAGING
        elif category.upper() == "CLINICAL_NOTES":
            category_enum = RecordCategory.CLINICAL_NOTES
        elif category.upper() == "PRESCRIPTIONS":
            category_enum = RecordCategory.PRESCRIPTIONS
        elif category.upper() == "VACCINATIONS":
            category_enum = RecordCategory.VACCINATIONS
        elif category.upper() == "PERSONAL_NOTES":
            category_enum = RecordCategory.PERSONAL_NOTES
        elif category.upper() == "VITAL_SIGNS":
            category_enum = RecordCategory.VITAL_SIGNS
        else:
            category_enum = RecordCategory.OTHER
    except:
        category_enum = RecordCategory.OTHER
    
    record = HealthRecord(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=title or sanitize_filename(file.filename),
        description=description,
        category=category_enum,
        file_name=sanitize_filename(file.filename),
        file_type=file.content_type,
        file_size=file_size,
        file_checksum=checksum,
        minio_object_name=object_name,
        provider_name=provider_name,
        service_date=service_date
    )
    
    db.add(record)
    
    # Generate thumbnail for images
    if file.content_type and file.content_type.startswith('image/'):
        try:
            from app.services.thumbnail import generate_image_thumbnail
            thumbnail = generate_image_thumbnail(contents, size=(200, 200))
            if thumbnail:
                record.thumbnail_data = thumbnail
                record.has_thumbnail = True
        except:
            pass
    
    # Update user storage
    current_user.storage_used_mb += file_size / 1024 / 1024
    
    # Add audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action=AuditAction.FILE_UPLOAD,
        resource_type="file",
        resource_id=record.id,
        details=f"Uploaded {file.filename}"
    )
    db.add(audit)
    
    db.commit()
    
    return {"message": "File uploaded successfully", "record_id": record.id}

@router.get("/download/{record_id}")
async def download_file(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get file from MinIO
    encrypted_content = await storage_service.download_file(record.minio_object_name)
    
    if not encrypted_content:
        raise HTTPException(status_code=404, detail="File content not found")
    
    # Generate user encryption key
    user_key = derive_key_from_password(
        f"{current_user.id}:{current_user.hashed_password}:{settings.ENCRYPTION_KEY}",
        current_user.encryption_salt
    )
    
    # Decrypt file content
    decrypted_content = decrypt_file_content(encrypted_content, user_key)
    
    # Add audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action=AuditAction.FILE_DOWNLOAD,
        resource_type="file",
        resource_id=record.id
    )
    db.add(audit)
    db.commit()
    
    # Return file as streaming response
    return StreamingResponse(
        io.BytesIO(decrypted_content),
        media_type=record.file_type or 'application/octet-stream',
        headers={
            "Content-Disposition": f'attachment; filename="{record.file_name}"'
        }
    )

@router.delete("/{record_id}")
async def delete_file(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(HealthRecord).filter(
        HealthRecord.id == record_id,
        HealthRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from MinIO
    await storage_service.delete_file(record.minio_object_name)
    
    # Update user storage
    current_user.storage_used_mb -= record.file_size / 1024 / 1024
    
    # Soft delete record
    record.is_deleted = True
    record.deleted_at = datetime.now(timezone.utc)
    
    # Add audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        action=AuditAction.FILE_DELETE,
        resource_type="file",
        resource_id=record.id
    )
    db.add(audit)
    db.commit()
    
    return {"message": "File deleted successfully"}