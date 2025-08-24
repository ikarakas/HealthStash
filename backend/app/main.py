from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, users, files, health_records, vitals, admin, backup, mobile, payments
from app.core.security import verify_encryption_setup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HealthStash application...")
    verify_encryption_setup()
    await init_db()
    
    # Clean up any stuck backups from previous runs
    from app.core.database import SessionLocal
    from app.models.backup import BackupHistory, BackupStatus
    from datetime import datetime, timezone
    
    db = SessionLocal()
    try:
        stuck_backups = db.query(BackupHistory).filter(
            BackupHistory.status == BackupStatus.IN_PROGRESS
        ).all()
        
        for backup in stuck_backups:
            logger.warning(f"Found stuck backup {backup.id}, marking as failed")
            backup.status = BackupStatus.FAILED
            backup.error_message = "Backup interrupted by server restart"
            backup.completed_at = datetime.now(timezone.utc)
            
            if backup.started_at:
                started = backup.started_at
                completed = backup.completed_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                if completed.tzinfo is None:
                    completed = completed.replace(tzinfo=timezone.utc)
                backup.duration_seconds = int((completed - started).total_seconds())
        
        if stuck_backups:
            db.commit()
            logger.info(f"Cleaned up {len(stuck_backups)} stuck backups")
    finally:
        db.close()
    
    # Start background task to monitor stuck backups
    async def monitor_stuck_backups():
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                db = SessionLocal()
                try:
                    # Find backups that have been in progress for more than 5 minutes
                    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
                    
                    stuck_backups = db.query(BackupHistory).filter(
                        BackupHistory.status == BackupStatus.IN_PROGRESS,
                        BackupHistory.started_at < cutoff_time
                    ).all()
                    
                    for backup in stuck_backups:
                        logger.warning(f"Found stuck backup {backup.id} (running for >5 min), marking as failed")
                        backup.status = BackupStatus.FAILED
                        backup.error_message = "Backup timeout - took longer than 5 minutes"
                        backup.completed_at = datetime.now(timezone.utc)
                        
                        if backup.started_at:
                            started = backup.started_at
                            completed = backup.completed_at
                            if started.tzinfo is None:
                                started = started.replace(tzinfo=timezone.utc)
                            if completed.tzinfo is None:
                                completed = completed.replace(tzinfo=timezone.utc)
                            backup.duration_seconds = int((completed - started).total_seconds())
                    
                    if stuck_backups:
                        db.commit()
                        logger.info(f"Cleaned up {len(stuck_backups)} timed-out backups")
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in backup monitor task: {e}")
    
    # Start the monitoring task
    monitor_task = asyncio.create_task(monitor_stuck_backups())
    
    yield
    
    # Cancel the monitoring task on shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Shutting down HealthStash application...")

app = FastAPI(
    title="HealthStash",
    description="Privacy-first personal health data vault",
    version="0.0.3",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    logger.error(f"Request body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)}
    )

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(health_records.router, prefix="/api/records", tags=["Health Records"])
app.include_router(vitals.router, prefix="/api/vitals", tags=["Vital Signs"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])
app.include_router(mobile.router, prefix="/api/mobile", tags=["Mobile Upload"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "HealthStash"}

@app.get("/")
async def root():
    return {"message": "HealthStash API", "version": "0.0.3"}