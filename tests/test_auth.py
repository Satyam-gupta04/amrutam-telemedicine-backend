def test_register_patient_success(client):
    payload = {
        "email": "newpatient@amrutam.com",
        "password": "StrongPassword123!",
        "role": "patient",
        "full_name": "Aarav Patel",
        "phone": "9876501234"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "patient"
    assert data["profile"]["full_name"] == "Aarav Patel"

def test_register_duplicate_email_fails(client, test_patient):
    payload = {
        "email": test_patient.email,
        "password": "Password123!",
        "role": "patient",
        "full_name": "Duplicate User"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client, test_patient):
    payload = {
        "email": test_patient.email,
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "patient"

def test_login_wrong_password_fails(client, test_patient):
    payload = {
        "email": test_patient.email,
        "password": "IncorrectPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

def test_get_current_user_me(client, patient_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "patient@amrutam.com"

def test_mfa_setup_and_verify(client, patient_token):
    setup_res = client.post(
        "/api/v1/auth/mfa/setup",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert setup_res.status_code == 200
    instructions = setup_res.json()["instructions"]
    code = instructions.split(": ")[-1]

    verify_res = client.post(
        "/api/v1/auth/mfa/verify",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"code": code}
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "success"
