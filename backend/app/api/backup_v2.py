"""
Enhanced backup API that integrates with the backup container
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import subprocess
import uuid
import os
import asyncio
from datetime import datetime, timezone
import logging
from enum import Enum

from app.core.database import get_db
from app.models.user import User
from app.models.backup import BackupHistory, BackupType, BackupStatus
from app.api.auth import get_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

class BackupSource(str, Enum):
    MANUAL = "manual"      # User-triggered via web UI
    AUTOMATIC = "automatic" # Cron-triggered
    API = "api"            # API-triggered

async def trigger_backup_container(backup_id: str, source: BackupSource):
    """Trigger the backup container's backup.sh script"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        backup = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
        if not backup:
            logger.error(f"Backup {backup_id} not found")
            return
        
        try:
            # Create a trigger file for the backup container to detect
            trigger_dir = "/backups/triggers"
            os.makedirs(trigger_dir, exist_ok=True)
            
            trigger_file = f"{trigger_dir}/{backup_id}.trigger"
            with open(trigger_file, 'w') as f:
                f.write(f"BACKUP_ID={backup_id}\n")
                f.write(f"BACKUP_TYPE=FULL\n")
                f.write(f"BACKUP_SOURCE={source}\n")
                f.write(f"TIMESTAMP={datetime.now(timezone.utc).isoformat()}\n")
            
            logger.info(f"Created trigger file: {trigger_file}")
            
            # Wait for backup to complete (check for completion file)
            completion_file = f"{trigger_dir}/{backup_id}.complete"
            max_wait = 600  # 10 minutes
            wait_interval = 2  # Check every 2 seconds
            elapsed = 0
            
            while elapsed < max_wait:
                if os.path.exists(completion_file):
                    # Read completion status
                    with open(completion_file, 'r') as f:
                        status_data = f.read().strip()
                    
                    if "SUCCESS" in status_data:
                        backup.status = BackupStatus.COMPLETED
                        backup.notes = f"{source.value.capitalize()} backup completed (Full: PostgreSQL + TimescaleDB + MinIO + Encryption)"
                        
                        # Try to get backup file info
                        info_file = f"{trigger_dir}/{backup_id}.info"
                        if os.path.exists(info_file):
                            with open(info_file, 'r') as f:
                                for line in f:
                                    if line.startswith("FILE="):
                                        backup.file_path = line.split("=", 1)[1].strip()
                                    elif line.startswith("SIZE_MB="):
                                        try:
                                            backup.size_mb = float(line.split("=", 1)[1].strip())
                                        except:
                                            pass
                    else:
                        backup.status = BackupStatus.FAILED
                        backup.error_message = status_data
                    
                    # Clean up trigger files
                    try:
                        os.remove(completion_file)
                        if os.path.exists(info_file):
                            os.remove(info_file)
                    except:
                        pass
                    
                    break
                
                await asyncio.sleep(wait_interval)
                elapsed += wait_interval
            
            if elapsed >= max_wait:
                backup.status = BackupStatus.FAILED
                backup.error_message = "Backup timed out after 10 minutes"
                # Clean up trigger file
                try:
                    os.remove(trigger_file)
                except:
                    pass
            
            backup.completed_at = datetime.now(timezone.utc)
            
            # Calculate duration
            if backup.started_at and backup.completed_at:
                started = backup.started_at
                completed = backup.completed_at
                
                # Ensure both are timezone-aware
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                if completed.tzinfo is None:
                    completed = completed.replace(tzinfo=timezone.utc)
                
                duration = (completed - started).total_seconds()
                backup.duration_seconds = int(duration)
        
        except asyncio.TimeoutError:
            backup.status = BackupStatus.FAILED
            backup.error_message = "Backup timed out after 10 minutes"
            backup.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            backup.completed_at = datetime.now(timezone.utc)
            logger.error(f"Backup {backup_id} failed with exception: {e}")
        
        db.commit()
        logger.info(f"Backup {backup_id} completed with status: {backup.status}")
        
    except Exception as e:
        logger.error(f"Error processing backup {backup_id}: {e}")
    finally:
        db.close()

@router.post("/create")
async def create_backup(
    background_tasks: BackgroundTasks,
    backup_type: BackupType = BackupType.FULL,
    _admin_user: User = Depends(get_admin_user),  # Authentication check only
    db: Session = Depends(get_db)
):
    """Create a new backup using the backup container"""
    
    # Create backup history record
    backup = BackupHistory(
        id=str(uuid.uuid4()),
        backup_type=backup_type,
        status=BackupStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc),
        notes="Manual backup initiated from web UI",
        includes_database=True,
        includes_files=True,
        includes_config=False
    )
    db.add(backup)
    db.commit()
    
    # Trigger backup in background using backup container
    background_tasks.add_task(trigger_backup_container, backup.id, BackupSource.MANUAL)
    
    return {
        "message": "Backup started successfully",
        "backup_id": str(backup.id),
        "type": "comprehensive",
        "includes": ["PostgreSQL", "TimescaleDB", "MinIO Files", "Encryption"]
    }

@router.get("/history")
async def get_backup_history(
    limit: int = 50,
    include_automatic: bool = True,
    _admin_user: User = Depends(get_admin_user),  # Authentication check only
    db: Session = Depends(get_db)
):
    """Get backup history including both manual and automatic backups"""
    
    # Get backups from database
    db_backups = db.query(BackupHistory).order_by(
        BackupHistory.created_at.desc()
    ).limit(limit).all()
    
    # If we should include automatic backups, scan the backup directory
    all_backups = []
    
    if include_automatic:
        try:
            # Check for backup files that aren't in the database (automatic backups)
            result = subprocess.run(
                ["docker", "compose", "exec", "-T", "backup", "ls", "-la", "/backups/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                known_files = {b.file_path for b in db_backups if b.file_path}
                
                for line in lines:
                    # Parse backup files created by backup.sh
                    if 'healthstash_backup_' in line and '.tar.gz' in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            filename = parts[-1]
                            file_path = f"/backups/{filename}"
                            
                            # Check if this file is already in database
                            if file_path not in known_files:
                                # Extract timestamp from filename
                                try:
                                    # Format: healthstash_backup_YYYYMMDD_HHMMSS.tar.gz[.enc]
                                    timestamp_str = filename.split('_')[2] + filename.split('_')[3].split('.')[0]
                                    created_at = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                                    
                                    # Get file size
                                    size_bytes = int(parts[4])
                                    size_mb = round(size_bytes / (1024 * 1024), 2)
                                    
                                    # Create a pseudo backup record for automatic backup
                                    auto_backup = {
                                        "id": f"auto_{timestamp_str}",
                                        "backup_type": "full",
                                        "status": "completed",
                                        "file_path": file_path,
                                        "size_mb": size_mb,
                                        "created_at": created_at.isoformat(),
                                        "completed_at": created_at.isoformat(),
                                        "notes": "Automatic backup (cron)",
                                        "source": "automatic",
                                        "includes_database": True,
                                        "includes_files": True,
                                        "includes_config": False
                                    }
                                    all_backups.append(auto_backup)
                                except Exception as e:
                                    logger.warning(f"Failed to parse automatic backup {filename}: {e}")
                                    
        except Exception as e:
            logger.error(f"Failed to scan backup directory: {e}")
    
    # Convert database backups to dict format
    for db_backup in db_backups:
        backup_dict = {
            "id": str(db_backup.id),
            "backup_type": db_backup.backup_type.value if db_backup.backup_type else "full",
            "status": db_backup.status.value if db_backup.status else "unknown",
            "file_path": db_backup.file_path,
            "size_mb": db_backup.size_mb,
            "duration_seconds": db_backup.duration_seconds,
            "created_at": db_backup.created_at.isoformat() if db_backup.created_at else None,
            "started_at": db_backup.started_at.isoformat() if db_backup.started_at else None,
            "completed_at": db_backup.completed_at.isoformat() if db_backup.completed_at else None,
            "error_message": db_backup.error_message,
            "notes": db_backup.notes or "Manual backup",
            "source": "manual" if "Manual" in (db_backup.notes or "") else "unknown",
            "includes_database": db_backup.includes_database,
            "includes_files": db_backup.includes_files,
            "includes_config": db_backup.includes_config
        }
        all_backups.append(backup_dict)
    
    # Sort all backups by created_at
    all_backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return all_backups[:limit]

@router.post("/scan")
async def scan_backup_directory(
    _admin_user: User = Depends(get_admin_user),  # Authentication check only
    db: Session = Depends(get_db)
):
    """Scan backup directory and sync with database"""
    
    try:
        # List all backup files in the container
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backup", "find", "/backups", "-name", "*.tar.gz*", "-o", "-name", "*.sql*"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to scan backup directory")
        
        files = result.stdout.strip().split('\n')
        synced_count = 0
        
        for file_path in files:
            if not file_path:
                continue
                
            # Check if this backup is already in database
            existing = db.query(BackupHistory).filter(
                BackupHistory.file_path == file_path
            ).first()
            
            if not existing:
                # Get file stats
                stat_result = subprocess.run(
                    ["docker", "compose", "exec", "-T", "backup", "stat", "-c", "%s %Y", file_path],
                    capture_output=True,
                    text=True
                )
                
                if stat_result.returncode == 0:
                    parts = stat_result.stdout.strip().split()
                    size_bytes = int(parts[0])
                    mtime = int(parts[1])
                    
                    # Create backup record
                    backup = BackupHistory(
                        id=str(uuid.uuid4()),
                        backup_type=BackupType.FULL,
                        status=BackupStatus.COMPLETED,
                        file_path=file_path,
                        size_mb=round(size_bytes / (1024 * 1024), 2),
                        created_at=datetime.fromtimestamp(mtime, tz=timezone.utc),
                        completed_at=datetime.fromtimestamp(mtime, tz=timezone.utc),
                        notes="Discovered during directory scan",
                        includes_database=True,
                        includes_files='.tar.gz' in file_path,
                        includes_config=False
                    )
                    db.add(backup)
                    synced_count += 1
        
        db.commit()
        
        return {
            "message": f"Scan completed. Synced {synced_count} new backups.",
            "total_files": len(files),
            "new_records": synced_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

@router.get("/status")
async def get_backup_status(
    _admin_user: User = Depends(get_admin_user)  # Authentication check only
):
    """Get overall backup system status"""
    
    try:
        # Check if backup container is running
        container_result = subprocess.run(
            ["docker", "compose", "ps", "backup", "--format", "json"],
            capture_output=True,
            text=True
        )
        
        container_running = "running" in container_result.stdout.lower()
        
        # Check cron schedule
        cron_result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backup", "crontab", "-l"],
            capture_output=True,
            text=True
        )
        
        cron_schedule = None
        if cron_result.returncode == 0:
            lines = cron_result.stdout.strip().split('\n')
            for line in lines:
                if 'backup.sh' in line:
                    cron_schedule = line.split()[0:5]
                    cron_schedule = ' '.join(cron_schedule)
                    break
        
        # Check disk space
        space_result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backup", "df", "-h", "/backups"],
            capture_output=True,
            text=True
        )
        
        disk_usage = {}
        if space_result.returncode == 0:
            lines = space_result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    disk_usage = {
                        "total": parts[1],
                        "used": parts[2],
                        "available": parts[3],
                        "percent": parts[4]
                    }
        
        return {
            "container_running": container_running,
            "cron_schedule": cron_schedule,
            "cron_enabled": cron_schedule is not None,
            "next_scheduled_backup": calculate_next_cron_run(cron_schedule) if cron_schedule else None,
            "disk_usage": disk_usage,
            "backup_directory": "/backups"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "container_running": False,
            "cron_enabled": False
        }

def calculate_next_cron_run(cron_schedule: str) -> str:
    """Calculate next cron run time (simplified)"""
    # For "0 2 * * *" format (daily at 2 AM)
    if cron_schedule == "0 2 * * *":
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if next_run <= now:
            from datetime import timedelta
            next_run += timedelta(days=1)
        return next_run.isoformat()
    return "Unknown"

# Keep existing restore and download endpoints as they are
@router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    _admin_user: User = Depends(get_admin_user),  # Authentication check only
    db: Session = Depends(get_db)
):
    """Restore a backup"""
    backup = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
    
    if not backup:
        # Check if it's an automatic backup
        if backup_id.startswith("auto_"):
            raise HTTPException(status_code=400, detail="Cannot restore automatic backups through this endpoint. Use backup container directly.")
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot restore incomplete backup")
    
    if not backup.file_path:
        raise HTTPException(status_code=400, detail="Backup file path not found")
    
    try:
        # Use the backup container's restore script
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backup", "/backup/restore.sh", backup.file_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Restore failed: {result.stderr}"
            )
        
        return {"message": "Backup restored successfully"}
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Restore timed out after 10 minutes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    _admin_user: User = Depends(get_admin_user),  # Authentication check only
    db: Session = Depends(get_db)
):
    """Delete a backup"""
    
    # Handle automatic backup deletion
    if backup_id.startswith("auto_"):
        # Extract timestamp and reconstruct filename
        timestamp = backup_id.replace("auto_", "")
        filename = f"healthstash_backup_{timestamp}.tar.gz.enc"
        file_path = f"/backups/{filename}"
        
        try:
            subprocess.run(
                ["docker", "compose", "exec", "-T", "backup", "rm", "-f", file_path],
                check=True
            )
            return {"message": "Automatic backup deleted successfully"}
        except:
            raise HTTPException(status_code=500, detail="Failed to delete backup file")
    
    # Handle database-tracked backups
    backup = db.query(BackupHistory).filter(BackupHistory.id == backup_id).first()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Delete backup file if it exists
    if backup.file_path:
        try:
            subprocess.run(
                ["docker", "compose", "exec", "-T", "backup", "rm", "-f", backup.file_path],
                check=True
            )
        except:
            pass
    
    db.delete(backup)
    db.commit()
    
    return {"message": "Backup deleted successfully"}