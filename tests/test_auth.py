"""
test_auth.py – Authentication and authorization tests.
"""
from tests.conftest import get_token, auth_header


def test_401_without_token(client, seed_data):
    """Endpoints should return 401 when no token is provided."""
    resp = client.get("/appointments/")
    assert resp.status_code == 401


def test_401_with_invalid_token(client, seed_data):
    """Invalid JWT should return 401."""
    resp = client.get("/appointments/", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


def test_login_success(client, seed_data):
    """Valid credentials should return a JWT."""
    resp = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, seed_data):
    resp = client.post("/auth/login", data={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_403_patient_cannot_see_others_appointments(client, seed_data):
    """A patient cannot create an appointment for another patient."""
    from datetime import datetime, timedelta
    token = get_token(client, "patient01", "patient123")

    # Try to book for patient2 – should be 403
    future = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    resp = client.post(
        "/appointments/",
        json={
            "doctor_id": seed_data["doctor1"].id,
            "patient_id": seed_data["patient2"].id,  # not their own
            "slot_start": future.isoformat(),
            "slot_end": (future + timedelta(minutes=30)).isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 403
