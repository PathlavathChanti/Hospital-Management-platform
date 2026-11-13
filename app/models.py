import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Index, func, text,
)
from sqlalchemy.orm import relationship
from app.db import Base


class UserRole(str, enum.Enum):
    patient = "patient"
    receptionist = "receptionist"
    admin = "admin"


class AppointmentStatus(str, enum.Enum):
    confirmed = "CONFIRMED"
    cancelled = "CANCELLED"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    patient = relationship("Patient", back_populates="user")


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=True)

    appointments = relationship("Appointment", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    user = relationship("User", back_populates="patient", uselist=False)
    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    slot_start = Column(DateTime(timezone=True), nullable=False)
    slot_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum(AppointmentStatus),
        nullable=False,
        server_default=text("'CONFIRMED'"),
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    __table_args__ = (
        # Partial unique index prevents double-booking of confirmed slots
        Index(
            "uq_doctor_slot_confirmed",
            "doctor_id",
            "slot_start",
            unique=True,
            postgresql_where=text("status = 'CONFIRMED'"),
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # create, reschedule, cancel
    entity = Column(String(50), nullable=False)  # appointment
    entity_id = Column(Integer, nullable=False)
    details = Column(String, nullable=True)  # JSON text
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    actor = relationship("User")
