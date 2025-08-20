from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

timescale_engine = create_engine(
    settings.TIMESCALE_URL,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
TimescaleSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=timescale_engine)

Base = declarative_base()
metadata = MetaData()

async def init_db():
    try:
        # Create tables in the main database
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Note: TimescaleDB tables are created separately via SQL scripts
        # The vital_signs table should be created in TimescaleDB, not PostgreSQL
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # Don't fail if vital_signs table can't be created (it's in TimescaleDB)
        if "vital_signs" not in str(e):
            raise

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_timescale_db() -> Session:
    db = TimescaleSessionLocal()
    try:
        yield db
    finally:
        db.close()