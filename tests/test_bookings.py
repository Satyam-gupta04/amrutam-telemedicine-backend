def test_book_appointment_success(client, patient_token, test_doctor, doctor_slot):
    payload = {
        "doctor_id": test_doctor.doctor_profile.id,
        "slot_id": doctor_slot.id,
        "notes": "Frequent headache and acidity"
    }
    response = client.post(
        "/api/v1/bookings",
        headers={
            "Authorization": f"Bearer {patient_token}",
            "Idempotency-Key": "test-key-001"
        },
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "booked"
    assert data["slot_id"] == doctor_slot.id
    assert "meet_link" in data

def test_duplicate_booking_fails(client, patient_token, test_doctor, doctor_slot):
    payload = {
        "doctor_id": test_doctor.doctor_profile.id,
        "slot_id": doctor_slot.id,
        "notes": "First booking"
    }
    first_res = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json=payload
    )
    assert first_res.status_code == 201

    second_res = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json=payload
    )
    assert second_res.status_code == 409

def test_idempotency_returns_original_booking(client, patient_token, test_doctor, doctor_slot):
    payload = {
        "doctor_id": test_doctor.doctor_profile.id,
        "slot_id": doctor_slot.id,
        "notes": "Testing idempotency retry"
    }
    headers = {
        "Authorization": f"Bearer {patient_token}",
        "Idempotency-Key": "idemp-safe-retry-999"
    }

    first = client.post("/api/v1/bookings", headers=headers, json=payload)
    assert first.status_code == 201
    booking_id = first.json()["id"]

    retry = client.post("/api/v1/bookings", headers=headers, json=payload)
    assert retry.status_code == 201
    assert retry.json()["id"] == booking_id

def test_idempotency_key_mismatch_fails(client, patient_token, test_doctor, doctor_slot):
    headers = {
        "Authorization": f"Bearer {patient_token}",
        "Idempotency-Key": "conflict-key-123"
    }

    first = client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"doctor_id": test_doctor.doctor_profile.id, "slot_id": doctor_slot.id, "notes": "Initial"}
    )
    assert first.status_code == 201

    conflict = client.post(
        "/api/v1/bookings",
        headers=headers,
        json={"doctor_id": test_doctor.doctor_profile.id, "slot_id": doctor_slot.id, "notes": "Altered Payload"}
    )
    assert conflict.status_code == 400

def test_cancel_booking(client, patient_token, test_doctor, doctor_slot):
    payload = {
        "doctor_id": test_doctor.doctor_profile.id,
        "slot_id": doctor_slot.id,
        "notes": "Booking to cancel"
    }
    booking = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json=payload
    ).json()

    cancel_res = client.patch(
        f"/api/v1/bookings/{booking['id']}/cancel",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
