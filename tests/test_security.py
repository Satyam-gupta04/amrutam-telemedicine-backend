def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_invalid_token_rejected(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert response.status_code == 401

def test_patient_cannot_access_admin_endpoints(client, patient_token):
    res_analytics = client.get(
        "/api/v1/admin/analytics",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res_analytics.status_code == 403

    res_audit = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res_audit.status_code == 403
