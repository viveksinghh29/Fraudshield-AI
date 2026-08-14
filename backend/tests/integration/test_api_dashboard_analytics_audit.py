"""
API-level tests for /dashboard, /analytics, /audit-logs -- real HTTP
requests against the actual app.
"""

import uuid

import pytest

from tests.integration._model_helpers import register_quick_active_model, sample_transaction_payload


async def _register_and_login(api_client, role: str = "analyst") -> str:
    email = f"dash_{uuid.uuid4().hex[:8]}@fraudshield.ai"
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Dash Tester", "role": role},
    )
    login_resp = await api_client.post("/api/v1/auth/login", json={"email": email, "password": "Password1"})
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_dashboard_reflects_real_predictions(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    for amount in [50, 500, 5000]:
        await api_client.post(
            "/api/v1/predict",
            json=sample_transaction_payload(amount=amount),
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await api_client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 3
    assert body["fraud_count"] + body["legitimate_count"] == 3
    assert len(body["recent_predictions"]) == 3
    assert body["active_model_version"] is not None


@pytest.mark.asyncio
async def test_dashboard_with_no_predictions_returns_zeros(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    response = await api_client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 0
    assert body["fraud_rate_pct"] == 0.0


@pytest.mark.asyncio
async def test_analytics_reflects_real_predictions(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    for amount in [50, 500]:
        await api_client.post(
            "/api/v1/predict",
            json=sample_transaction_payload(amount=amount),
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await api_client.get(
        "/api/v1/analytics", params={"days": 30}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_predictions"] == 2
    assert 0.0 <= body["avg_fraud_probability"] <= 1.0
    assert len(body["fraud_trend"]) >= 1


@pytest.mark.asyncio
async def test_analytics_requires_authentication(api_client, clean_api_tables):
    response = await api_client.get("/api/v1/analytics")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_audit_logs_admin_only(api_client, clean_api_tables):
    analyst_token = await _register_and_login(api_client, role="analyst")
    response = await api_client.get(
        "/api/v1/audit-logs", headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_captures_real_events(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    admin_token = await _register_and_login(api_client, role="admin")

    await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await api_client.get(
        "/api/v1/audit-logs", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    body = response.json()
    actions = [entry["action"] for entry in body["items"]]
    assert "USER_REGISTERED" in actions
    assert "LOGIN" in actions
    assert "PREDICTION_CREATED" in actions


@pytest.mark.asyncio
async def test_audit_logs_filter_by_action(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    admin_token = await _register_and_login(api_client, role="admin")

    await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await api_client.get(
        "/api/v1/audit-logs",
        params={"action": "PREDICTION_CREATED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    for entry in response.json()["items"]:
        assert entry["action"] == "PREDICTION_CREATED"
