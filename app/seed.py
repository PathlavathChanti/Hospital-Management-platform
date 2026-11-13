"""
Seed script: populate the database with synthetic demo data.
Run with: python -m app.seed

Demo credentials (seed-only, never used in production):
  admin    / admin123
  reception/ reception123
  patient01 through patient08 / patient123
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import engine, SessionLocal, Base
from app import models
from app.auth import get_password_hash


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # -- Doctors --
    doctors_data = [
        ("Dr. Alice Smith", "Cardiology"),
        ("Dr. Bob Johnson", "Dermatology"),
        ("Dr. Carol Williams", "Neurology"),
        ("Dr. David Brown", "Pediatrics"),
    ]
    doctors = []
    for name, spec in doctors_data:
        d = models.Doctor(name=name, specialty=spec)
        db.add(d)
        doctors.append(d)
    db.flush()

    # -- Patients --
    patients = []
    for i in range(1, 9):
        p = models.Patient(name=f"Test Patient {i:02d}")
        db.add(p)
        patients.append(p)
    db.flush()

    # -- Users --
    # Admin
    db.add(models.User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role=models.UserRole.admin,
    ))
    # Receptionist
    db.add(models.User(
        username="reception",
        password_hash=get_password_hash("reception123"),
        role=models.UserRole.receptionist,
    ))
    # Patient users
    for i, patient in enumerate(patients, start=1):
        db.add(models.User(
            username=f"patient{i:02d}",
            password_hash=get_password_hash("patient123"),
            role=models.UserRole.patient,
            patient_id=patient.id,
        ))

    db.commit()
    db.close()
    print("Database seeded successfully with synthetic data.")


if __name__ == "__main__":
    seed()
