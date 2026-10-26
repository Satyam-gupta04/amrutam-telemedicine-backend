def test_admin_list_users(client, admin_token, test_patient, test_doctor):
    res = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 3

def test_admin_analytics(client, admin_token):
    res = client.get(
        "/api/v1/admin/analytics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_consultations" in data
    assert "total_revenue" in data

def test_admin_audit_logs(client, admin_token):
    res = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_payment_confirmation(client, patient_token, test_doctor, doctor_slot):
    booking_res = client.post(
        "/api/v1/bookings",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "doctor_id": test_doctor.doctor_profile.id,
            "slot_id": doctor_slot.id
        }
    )
    consultation_id = booking_res.json()["id"]

    payment_get = client.get(
        f"/api/v1/payments/{consultation_id}",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert payment_get.status_code == 200
    assert payment_get.json()["status"] == "pending"

    confirm_res = client.post(
        f"/api/v1/payments/{consultation_id}/confirm",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "completed"
