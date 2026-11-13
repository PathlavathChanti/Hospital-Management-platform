"""
Shared pytest fixtures. Tests run against a REAL PostgreSQL database.
The DATABASE_URL env var must point to a test Postgres instance.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_pass")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")

from app.main import app
from app.db import Base, engine, get_db
from app import models
from app.auth import get_password_hash, create_access_token

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables at the start and drop them at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables between tests for isolation."""
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE;"))
        conn.commit()


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with overridden DB dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_data(db_session):
    """Create doctors, patients, and users for testing."""
    # Doctors
    d1 = models.Doctor(name="Dr. Test One", specialty="Cardiology")
    d2 = models.Doctor(name="Dr. Test Two", specialty="Neurology")
    db_session.add_all([d1, d2])
    db_session.flush()

    # Patients
    p1 = models.Patient(name="Test Patient 01")
    p2 = models.Patient(name="Test Patient 02")
    db_session.add_all([p1, p2])
    db_session.flush()

    # Users
    admin = models.User(
        username="admin", password_hash=get_password_hash("admin123"),
        role=models.UserRole.admin,
    )
    receptionist = models.User(
        username="reception", password_hash=get_password_hash("reception123"),
        role=models.UserRole.receptionist,
    )
    patient_user1 = models.User(
        username="patient01", password_hash=get_password_hash("patient123"),
        role=models.UserRole.patient, patient_id=p1.id,
    )
    patient_user2 = models.User(
        username="patient02", password_hash=get_password_hash("patient123"),
        role=models.UserRole.patient, patient_id=p2.id,
    )
    db_session.add_all([admin, receptionist, patient_user1, patient_user2])
    db_session.commit()

    return {
        "doctor1": d1, "doctor2": d2,
        "patient1": p1, "patient2": p2,
        "admin": admin, "receptionist": receptionist,
        "patient_user1": patient_user1, "patient_user2": patient_user2,
    }


def get_token(client, username, password):
    """Helper: login and return the bearer token string."""
    resp = client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
