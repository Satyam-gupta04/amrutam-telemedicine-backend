from datetime import datetime, timedelta

def test_list_doctors_with_filters(client, test_doctor):
    response = client.get("/api/v1/doctors?specialization=Ayurveda")
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) >= 1
    assert doctors[0]["specialization"] == "Ayurveda"

def test_get_doctor_by_id(client, test_doctor):
    doc_id = test_doctor.doctor_profile.id
    response = client.get(f"/api/v1/doctors/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id
    assert data["consultation_fee"] == 750.0

def test_create_and_view_slot(client, test_doctor, doctor_token):
    doc_id = test_doctor.doctor_profile.id
    start = (datetime.utcnow() + timedelta(days=2)).isoformat()
    end = (datetime.utcnow() + timedelta(days=2, minutes=30)).isoformat()

    res = client.post(
        f"/api/v1/doctors/{doc_id}/slots",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={"start_time": start, "end_time": end}
    )
    assert res.status_code == 201
    assert res.json()["is_booked"] is False

    slots_res = client.get(f"/api/v1/doctors/{doc_id}/slots")
    assert slots_res.status_code == 200
    assert len(slots_res.json()) >= 1
