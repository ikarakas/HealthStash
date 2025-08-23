import asyncio
import os
import pytest
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from testcontainers.postgres import PostgresContainer
from testcontainers.compose import DockerCompose
from minio import Minio
from datetime import datetime, timedelta
import json
import tempfile
from pathlib import Path

os.environ["TESTING"] = "true"

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.health_record import HealthRecord

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing"""
    with PostgresContainer("postgres:15-alpine") as postgres:
        postgres.start()
        yield postgres

@pytest.fixture(scope="session")
def timescale_container():
    """Start TimescaleDB container for testing"""
    with PostgresContainer("timescale/timescaledb:latest-pg15") as timescale:
        timescale.start()
        yield timescale

@pytest.fixture(scope="function")
def test_db(postgres_container):
    """Create test database"""
    engine = create_engine(
        postgres_container.get_connection_url(),
        connect_args={"check_same_thread": False} if "sqlite" in postgres_container.get_connection_url() else {},
        poolclass=StaticPool,
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    return TestClient(app)

@pytest.fixture(scope="function")
def async_client(test_db):
    """Create async test client"""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")

@pytest.fixture
def test_user(test_db):
    """Create test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def admin_user(test_db):
    """Create admin user"""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(admin_user):
    """Create admin authentication headers"""
    access_token = create_access_token(data={"sub": admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def sample_health_record(test_db, test_user):
    """Create sample health record"""
    record = HealthRecord(
        user_id=test_user.id,
        record_type="lab_result",
        record_date=datetime.now(),
        title="Blood Test Results",
        description="Annual blood work",
        category="laboratory",
        metadata={"test_type": "complete_blood_count"}
    )
    test_db.add(record)
    test_db.commit()
    test_db.refresh(record)
    return record

@pytest.fixture
def temp_file():
    """Create temporary file for testing uploads"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(b"Test file content")
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)

@pytest.fixture
def minio_client():
    """Create MinIO client for testing"""
    client = Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    
    bucket_name = "test-healthstash"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    
    yield client
    
    objects = client.list_objects(bucket_name, recursive=True)
    for obj in objects:
        client.remove_object(bucket_name, obj.object_name)
    client.remove_bucket(bucket_name)

@pytest.fixture(scope="session")
def docker_compose():
    """Start full docker-compose stack for E2E tests"""
    compose = DockerCompose(
        filepath="../",
        compose_file_name="docker-compose.test.yml",
        pull=True
    )
    compose.start()
    compose.wait_for("http://localhost:8000/health")
    yield compose
    compose.stop()

@pytest.fixture
def mock_email(monkeypatch):
    """Mock email sending"""
    sent_emails = []
    
    def mock_send_email(to, subject, body):
        sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
            "timestamp": datetime.now()
        })
        return True
    
    monkeypatch.setattr("app.utils.email.send_email", mock_send_email)
    return sent_emails

@pytest.fixture
def performance_tracker():
    """Track performance metrics"""
    metrics = {
        "start_time": None,
        "end_time": None,
        "duration": None,
        "memory_usage": [],
        "cpu_usage": []
    }
    
    import psutil
    import time
    
    def start():
        metrics["start_time"] = time.time()
        process = psutil.Process()
        metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)
        metrics["cpu_usage"].append(process.cpu_percent())
    
    def stop():
        metrics["end_time"] = time.time()
        metrics["duration"] = metrics["end_time"] - metrics["start_time"]
        process = psutil.Process()
        metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)
        metrics["cpu_usage"].append(process.cpu_percent())
    
    metrics["start"] = start
    metrics["stop"] = stop
    
    return metrics