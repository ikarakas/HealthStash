from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Union
import secrets

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://healthstash:changeme@postgres:5432/healthstash"
    TIMESCALE_URL: str = "postgresql://healthstash:changeme@timescaledb:5432/healthstash_vitals"
    REDIS_URL: str = "redis://:changeme@redis:6379/0"
    
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "healthstash-files"
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".txt", ".rtf",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
        ".dcm", ".dicom",
        ".xls", ".xlsx", ".csv",
        ".xml", ".json", ".hl7"
    ]
    
    CORS_ORIGINS: Union[str, List[str]] = Field(default=["http://localhost:3000", "http://localhost", "http://localhost:5173"])
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    DEFAULT_USER_QUOTA_MB: int = 5000
    MAX_FILE_SIZE_MB: int = 500
    
    MIN_PASSWORD_LENGTH: int = 12
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_NUMBERS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    
    BACKUP_ENABLED: bool = True
    BACKUP_RETENTION_DAYS: int = 30
    
    ENABLE_AUDIT_LOG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()