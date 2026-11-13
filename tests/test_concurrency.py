"""
test_concurrency.py – Graded acceptance test.

Fire 10 simultaneous POST /appointments for the SAME doctor and slot.
Expect exactly ONE 201 Created and NINE 409 Conflict.
This proves the partial unique index prevents double-booking under concurrency.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import httpx
import pytest

from tests.conftest import get_token


# We need a real running server for true concurrency, so we use httpx
# against the TestClient in thread-safe mode.

def test_concurrent_booking(client, seed_data):
    """
    10 threads try to book the same doctor+slot simultaneously.
    Exactly 1 should succeed (201), 9 should get 409.
    """
    token = get_token(client, "admin", "admin123")
    start = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(minutes=30)
    payload = {
        "doctor_id": seed_data["doctor1"].id,
        "patient_id": seed_data["patient1"].id,
        "slot_start": start.isoformat(),
        "slot_end": end.isoformat(),
    }
    headers = {"Authorization": f"Bearer {token}"}

    results = []
    barrier = threading.Barrier(10)  # sync all threads

    def book():
        barrier.wait()  # all threads start together
        resp = client.post("/appointments/", json=payload, headers=headers)
        return resp.status_code

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(book) for _ in range(10)]
        for f in as_completed(futures):
            results.append(f.result())

    created = results.count(201)
    conflict = results.count(409)

    print(f"\n{'='*60}")
    print(f"CONCURRENCY TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total requests:  10")
    print(f"201 Created:     {created}")
    print(f"409 Conflict:    {conflict}")
    print(f"Other:           {10 - created - conflict}")
    print(f"{'='*60}")
    print(f"PASS" if created == 1 and conflict == 9 else "FAIL")
    print(f"{'='*60}\n")

    assert created == 1, f"Expected exactly 1 x 201, got {created}"
    assert conflict == 9, f"Expected exactly 9 x 409, got {conflict}"
