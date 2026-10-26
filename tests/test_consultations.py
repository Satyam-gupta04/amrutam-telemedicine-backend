def test_consultation_lifecycle_and_prescription(
    client,
    patient_token,
    doctor_token,
    test_doctor,
    doctor_slot
):
    booking_res = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "doctor_id": test_doctor.doctor_profile.id,
            "slot_id": doctor_slot.id,
            "notes": "Joint pain"
        }
    )
    assert booking_res.status_code == 201
    consultation_id = booking_res.json()["id"]

    start_res = client.post(
        f"/api/v1/consultations/{consultation_id}/start",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "in_progress"

    rx_res = client.post(
        f"/api/v1/consultations/{consultation_id}/prescriptions",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "diagnosis": "Vata Imbalance / Arthritis",
            "medicines": "Amrutam Orthokey Gold Malt - 1 spoon twice daily",
            "instructions": "Take with warm milk after meals."
        }
    )
    assert rx_res.status_code == 201
    assert rx_res.json()["diagnosis"] == "Vata Imbalance / Arthritis"

    complete_res = client.post(
        f"/api/v1/consultations/{consultation_id}/complete",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    view_rx = client.get(
        f"/api/v1/consultations/{consultation_id}/prescriptions",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert view_rx.status_code == 200
    assert "Amrutam Orthokey" in view_rx.json()["medicines"]

def test_patient_cannot_issue_prescription(client, patient_token, test_doctor, doctor_slot):
    booking_res = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "doctor_id": test_doctor.doctor_profile.id,
            "slot_id": doctor_slot.id,
            "notes": "Testing unauthorized rx"
        }
    )
    consultation_id = booking_res.json()["id"]

    rx_res = client.post(
        f"/api/v1/consultations/{consultation_id}/prescriptions",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "diagnosis": "Self diagnosed",
            "medicines": "Unverified medication"
        }
    )
    assert rx_res.status_code == 403
