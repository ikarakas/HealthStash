from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, users, files, health_records, vitals, admin, backup
from app.core.security import verify_encryption_setup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting HealthStash application...")
    verify_encryption_setup()
    await init_db()
    yield
    logger.info("Shutting down HealthStash application...")

app = FastAPI(
    title="HealthStash",
    description="Privacy-first personal health data vault",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(health_records.router, prefix="/api/records", tags=["Health Records"])
app.include_router(vitals.router, prefix="/api/vitals", tags=["Vital Signs"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(backup.router, prefix="/api/backup", tags=["Backup"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "HealthStash"}

@app.get("/")
async def root():
    return {"message": "HealthStash API", "version": "1.0.0"}