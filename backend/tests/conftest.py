"""
Pytest konfigürasyonu ve test fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Company, UserRole
from datetime import datetime
import pytz

# Test veritabanı (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Test veritabanı session'ı"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Test client"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_company(db):
    """Test şirketi oluştur"""
    company = Company(
        vkn="1234567890",
        company_name="Test Şirketi",
        full_company_name="Test Şirketi San. Tic. Ltd. Şti.",
        is_active=True,
        sms_enabled=True,
        sms_username="test_user",
        sms_password="test_pass",
        sms_header="TEST"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def test_admin_user(db, test_company):
    """Test admin kullanıcısı oluştur"""
    import bcrypt
    hashed_password = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = User(
        company_id=test_company.id,
        vkn_tckn="12345678901",
        username="test_admin",
        hashed_password=hashed_password,
        full_name="Test Admin",
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_admin_user):
    """Auth token ile header'lar"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "test_admin",
            "password": "123456"
        }
    )
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

