"""
API-level tests for the batch prediction flow: CSV upload ->
POST /predict/batch -> GET /predict/batch/{id}/status.
"""

import io
import uuid

import pytest

from app.tasks.celery_app import celery_app
from tests.integration._model_helpers import register_quick_active_model


async def _register_and_login(api_client, role: str = "analyst") -> str:
    email = f"batch_{uuid.uuid4().hex[:8]}@fraudshield.ai"
    await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Batch Tester", "role": role},
    )
    login_resp = await api_client.post("/api/v1/auth/login", json={"email": email, "password": "Password1"})
    return login_resp.json()["access_token"]


def _sample_csv(rows: int = 3) -> bytes:
    header = "Time,Amount," + ",".join(f"V{i}" for i in range(1, 29))
    lines = [header]
    for n in range(rows):
        values = [str(1000.0 * n), str(40.0 + n * 10)] + [str(0.03 * i) for i in range(1, 29)]
        lines.append(",".join(values))
    return ("\n".join(lines)).encode()


@pytest.fixture
def celery_eager():
    original = celery_app.conf.task_always_eager
    original_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = original
    celery_app.conf.task_eager_propagates = original_propagates


@pytest.mark.asyncio
async def test_upload_csv_creates_transactions_under_one_batch(api_client, clean_api_tables):
    token = await _register_and_login(api_client)

    response = await api_client.post(
        "/api/v1/transactions/upload",
        files={"file": ("transactions.csv", io.BytesIO(_sample_csv(4)), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["transaction_count"] == 4
    assert body["status"] == "uploaded"
    assert "batch_id" in body


@pytest.mark.asyncio
async def test_upload_rejects_non_csv_file(api_client, clean_api_tables):
    token = await _register_and_login(api_client)

    response = await api_client.post(
        "/api/v1/transactions/upload",
        files={"file": ("not_a_csv.txt", io.BytesIO(b"hello"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_rejects_missing_columns(api_client, clean_api_tables):
    token = await _register_and_login(api_client)

    bad_csv = b"Time,Amount\n100.0,50.0\n"
    response = await api_client.post(
        "/api/v1/transactions/upload",
        files={"file": ("bad.csv", io.BytesIO(bad_csv), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_full_batch_prediction_flow(
    api_client, clean_api_tables, db_session, tmp_path, celery_eager
):
    await register_quick_active_model(db_session, tmp_path)
    token = await _register_and_login(api_client)

    upload_resp = await api_client.post(
        "/api/v1/transactions/upload",
        files={"file": ("transactions.csv", io.BytesIO(_sample_csv(3)), "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    batch_id = upload_resp.json()["batch_id"]

    trigger_resp = await api_client.post(
        "/api/v1/predict/batch",
        params={"batch_id": batch_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert trigger_resp.status_code == 200
    assert trigger_resp.json()["transaction_count"] == 3

    status_resp = await api_client.get(
        f"/api/v1/predict/batch/{batch_id}/status", headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.status_code == 200
    body = status_resp.json()
    # eager mode means the task already ran synchronously by the time
    # trigger_resp returned, so status should already reflect completion
    assert body["status"] == "completed"
    assert body["processed_transactions"] == 3
    assert body["total_transactions"] == 3
    assert body["fraud_count"] is not None


@pytest.mark.asyncio
async def test_batch_prediction_trigger_for_unknown_batch_returns_404(api_client, clean_api_tables):
    token = await _register_and_login(api_client)
    fake_batch_id = str(uuid.uuid4())

    response = await api_client.post(
        "/api/v1/predict/batch",
        params={"batch_id": fake_batch_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_status_for_unknown_batch_returns_404(api_client, clean_api_tables):
    token = await _register_and_login(api_client)
    fake_batch_id = str(uuid.uuid4())

    response = await api_client.get(
        f"/api/v1/predict/batch/{fake_batch_id}/status", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
