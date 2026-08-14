"""
API-level tests for /predict, /transactions, /explain, /model -- real
HTTP requests against the actual app, with a real active model
registered via the shared _model_helpers.register_quick_active_model.
"""

import uuid

import pytest

from tests.integration._model_helpers import register_quick_active_model, sample_transaction_payload


async def _register_and_login(api_client, role: str = "analyst") -> str:
    email = f"pred_{uuid.uuid4().hex[:8]}@fraudshield.ai"
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Predict Tester", "role": role},
    )
    login_resp = await api_client.post("/api/v1/auth/login", json={"email": email, "password": "Password1"})
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_predict_without_active_model_returns_503(api_client, clean_api_tables):
    token = await _register_and_login(api_client)
    response = await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert response.json()["error"] == "model_not_loaded"


@pytest.mark.asyncio
async def test_predict_returns_valid_prediction(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    response = await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_class"] in {"fraud", "legitimate"}
    assert 0.0 <= body["fraud_probability"] <= 1.0
    assert body["risk_level"] in {"low", "medium", "high", "critical"}
    assert "transaction_id" in body


@pytest.mark.asyncio
async def test_predict_requires_authentication(api_client, clean_api_tables):
    response = await api_client.post("/api/v1/predict", json=sample_transaction_payload())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_predict_rejects_malformed_payload(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    incomplete_payload = {"Time": 1000.0, "Amount": 50.0}  # missing V1-V28
    response = await api_client.post(
        "/api/v1/predict", json=incomplete_payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_explain_returns_shap_breakdown(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    predict_resp = await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    transaction_id = predict_resp.json()["transaction_id"]

    explain_resp = await api_client.post(
        "/api/v1/explain",
        json={"transaction_id": transaction_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert explain_resp.status_code == 200
    body = explain_resp.json()
    assert len(body["top_features"]) > 0
    assert body["value_space"] in {"probability", "log_odds"}


@pytest.mark.asyncio
async def test_explain_for_transaction_with_no_prediction_returns_404(api_client, clean_api_tables):
    token = await _register_and_login(api_client)
    fake_transaction_id = str(uuid.uuid4())

    response = await api_client.post(
        "/api/v1/explain",
        json={"transaction_id": fake_transaction_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_transactions_list_and_detail(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    predict_resp = await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    transaction_id = predict_resp.json()["transaction_id"]

    list_resp = await api_client.get("/api/v1/transactions", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["total"] >= 1
    assert any(item["id"] == transaction_id for item in list_body["items"])

    detail_resp = await api_client.get(
        f"/api/v1/transactions/{transaction_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert detail_resp.status_code == 200
    detail_body = detail_resp.json()
    assert detail_body["id"] == transaction_id
    assert "v1" in detail_body and "v28" in detail_body


@pytest.mark.asyncio
async def test_transactions_filter_by_risk_level(api_client, clean_api_tables, db_session, tmp_path):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    predict_resp = await api_client.post(
        "/api/v1/predict",
        json=sample_transaction_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    actual_risk_level = predict_resp.json()["risk_level"]

    # Filtering by whatever risk level this prediction actually landed on
    # must include it; every item returned must match the filter, whatever
    # that risk level turned out to be (a random_forest fit on random data
    # can't be assumed to always land on any one specific level).
    matching_resp = await api_client.get(
        "/api/v1/transactions",
        params={"risk_level": actual_risk_level},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert matching_resp.status_code == 200
    matching_body = matching_resp.json()
    assert matching_body["total"] >= 1
    for item in matching_body["items"]:
        assert item["prediction"]["risk_level"] == actual_risk_level

    # Every OTHER risk level's filter must never include this transaction
    other_levels = {"low", "medium", "high", "critical"} - {actual_risk_level}
    for level in other_levels:
        other_resp = await api_client.get(
            "/api/v1/transactions",
            params={"risk_level": level},
            headers={"Authorization": f"Bearer {token}"},
        )
        for item in other_resp.json()["items"]:
            assert item["prediction"]["risk_level"] == level


@pytest.mark.asyncio
async def test_model_info_returns_active_model(api_client, clean_api_tables, db_session, tmp_path):
    version_tag = await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    response = await api_client.get("/api/v1/model/info", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["version_tag"] == version_tag
    assert body["is_active"] is True
    assert body["algorithm"] == "random_forest"
