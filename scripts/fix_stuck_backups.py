#!/usr/bin/env python3
import sys
import os
sys.path.append('/app')

from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.backup import BackupHistory, BackupStatus

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://healthstash:changeme-strong-password@postgres:5432/healthstash')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fix_stuck_backups():
    """Fix backups stuck in IN_PROGRESS status"""
    db = SessionLocal()
    try:
        # Find all IN_PROGRESS backups
        stuck_backups = db.query(BackupHistory).filter(
            BackupHistory.status == BackupStatus.IN_PROGRESS
        ).all()
        
        for backup in stuck_backups:
            print(f"Found stuck backup: {backup.id}")
            
            # Check if there's a matching file in /backups
            backup_dir = "/backups"
            if backup.started_at:
                # Try to find a file with a similar timestamp
                timestamp_str = backup.started_at.strftime("%Y%m%d_%H%M")
                
                import os
                import glob
                
                # Look for files that might match this backup
                pattern = f"{backup_dir}/backup_{timestamp_str}*.sql.gz"
                matching_files = glob.glob(pattern)
                
                if matching_files:
                    # Found a matching file, mark as completed
                    backup.file_path = matching_files[0]
                    backup.status = BackupStatus.COMPLETED
                    backup.completed_at = backup.started_at  # Use started_at as approximation
                    backup.notes = "Recovered from interrupted backup"
                    
                    # Calculate file size
                    if os.path.exists(backup.file_path):
                        file_size_bytes = os.path.getsize(backup.file_path)
                        backup.size_mb = round(file_size_bytes / (1024 * 1024), 2)
                    
                    print(f"  ✅ Recovered backup with file: {backup.file_path}")
                else:
                    # No file found, mark as failed
                    backup.status = BackupStatus.FAILED
                    backup.error_message = "Backup interrupted by server reload"
                    backup.completed_at = backup.started_at
                    print(f"  ❌ No file found, marking as failed")
            else:
                # No start time, just mark as failed
                backup.status = BackupStatus.FAILED
                backup.error_message = "Backup interrupted - no start time recorded"
                print(f"  ❌ No start time, marking as failed")
        
        db.commit()
        print(f"\nFixed {len(stuck_backups)} stuck backup(s)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_stuck_backups()