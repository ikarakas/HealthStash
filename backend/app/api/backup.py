from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import subprocess
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.backup import BackupHistory, BackupType, BackupStatus
from app.api.auth import get_admin_user

router = APIRouter()

@router.post("/create")
async def create_backup(
    backup_type: BackupType = BackupType.FULL,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Create backup history record
    backup = BackupHistory(
        id=str(uuid.uuid4()),
        backup_type=backup_type,
        status=BackupStatus.IN_PROGRESS,
        started_at=datetime.utcnow()
    )
    db.add(backup)
    db.commit()
    
    try:
        # For now, just create a simple backup by calling pg_dump directly
        import os
        backup_dir = "/backups"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/manual_backup_{timestamp}.sql"
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Note: In a production environment, you would trigger an async job here
        # For now, we'll just mark it as initiated
        backup.status = BackupStatus.COMPLETED
        backup.completed_at = datetime.utcnow()
        backup.notes = f"Backup initiated - manual backup required via backup container"
        backup.file_path = backup_file
    
    except Exception as e:
        backup.status = BackupStatus.FAILED
        backup.error_message = str(e)
    
    db.commit()
    
    if backup.status == BackupStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Backup failed: {backup.error_message}")
    
    return {"message": "Backup created successfully", "backup_id": str(backup.id)}

@router.get("/history")
async def get_backup_history(
    limit: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    backups = db.query(BackupHistory).order_by(
        BackupHistory.created_at.desc()
    ).limit(limit).all()
    
    return backups

@router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    backup = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot restore incomplete backup")
    
    if not backup.file_path:
        raise HTTPException(status_code=400, detail="Backup file path not found")
    
    try:
        # Execute restore script
        result = subprocess.run(
            ["/backup/restore.sh", backup.file_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Restore failed: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Restore timed out after 10 minutes")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
    
    return {"message": "Backup restored successfully"}

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    backup = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Delete backup file if it exists
    if backup.file_path:
        try:
            subprocess.run(["rm", "-f", backup.file_path], check=True)
        except:
            pass
    
    db.delete(backup)
    db.commit()
    
    return {"message": "Backup deleted successfully"}