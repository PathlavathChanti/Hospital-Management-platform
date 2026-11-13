"""
test_appointments.py – Appointment CRUD, validation, and audit.
"""
from datetime import datetime, timedelta
from tests.conftest import get_token, auth_header
from app import models


def _future_slot():
    """Return a valid future slot (tomorrow 10:00–10:30)."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    return tomorrow, tomorrow + timedelta(minutes=30)


def test_create_appointment(client, seed_data, db_session):
    token = get_token(client, "patient01", "patient123")
    start, end = _future_slot()
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "CONFIRMED"

    # Check audit event was written
    audit = db_session.query(models.AuditEvent).filter_by(
        entity="appointment", action="create"
    ).first()
    assert audit is not None
    assert audit.entity_id == data["id"]


def test_cancel_appointment(client, seed_data, db_session):
    token = get_token(client, "patient01", "patient123")
    start, end = _future_slot()
    create_resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=auth_header(token),
    )
    appt_id = create_resp.json()["id"]

    # Cancel
    resp = client.delete(f"/appointments/{appt_id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"

    # Check audit
    audit = db_session.query(models.AuditEvent).filter_by(
        entity="appointment", action="cancel"
    ).first()
    assert audit is not None


def test_reschedule_appointment(client, seed_data, db_session):
    token = get_token(client, "patient01", "patient123")
    start, end = _future_slot()
    create_resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=auth_header(token),
    )
    appt_id = create_resp.json()["id"]

    # Reschedule to 11:00
    new_start = start.replace(hour=11)
    new_end = new_start + timedelta(minutes=30)
    resp = client.patch(
        f"/appointments/{appt_id}",
        json={"slot_start": new_start.isoformat(), "slot_end": new_end.isoformat()},
        headers=auth_header(token),
    )
    assert resp.status_code == 200

    # Check audit
    audit = db_session.query(models.AuditEvent).filter_by(
        entity="appointment", action="reschedule"
    ).first()
    assert audit is not None


def test_validation_past_slot(client, seed_data):
    token = get_token(client, "admin", "admin123")
    past = datetime(2020, 1, 1, 10, 0)
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": past.isoformat(),
            "slot_end": (past + timedelta(minutes=30)).isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_validation_outside_hours(client, seed_data):
    token = get_token(client, "admin", "admin123")
    future = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=20, minute=0, second=0, microsecond=0  # 8 PM – outside hours
    )
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": future.isoformat(),
            "slot_end": (future + timedelta(minutes=30)).isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_validation_bad_boundary(client, seed_data):
    token = get_token(client, "admin", "admin123")
    future = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=10, minute=15, second=0, microsecond=0  # 10:15 – not on boundary
    )
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient1"].id,
            "slot_start": future.isoformat(),
            "slot_end": (future + timedelta(minutes=30)).isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 422


def test_validation_unknown_doctor(client, seed_data):
    token = get_token(client, "admin", "admin123")
    start, end = _future_slot()
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": 9999,
            "patient_id": seed_data["patient1"].id,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 404


def test_validation_unknown_patient(client, seed_data):
    token = get_token(client, "admin", "admin123")
    start, end = _future_slot()
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": 9999,
            "slot_start": start.isoformat(),
            "slot_end": end.isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 404
