"""
Integration tests for the repository layer — run against a real
Postgres database (see tests/integration/conftest.py), not mocks.
Each test is wrapped in a rollback so it never leaves data behind.
"""

from datetime import datetime, timezone

import pytest

from app.models.model_version import ModelVersion
from app.models.prediction import PredictedClass, Prediction, RiskLevel
from app.models.transaction import Transaction
from app.models.user import User, UserRole
from app.repositories.model_version_repository import ModelVersionRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_create_and_get_by_email(db_session):
    repo = UserRepository(db_session)
    user = await repo.create(
        email="analyst@fraudshield.ai",
        hashed_password="hashed",
        full_name="Test Analyst",
        role=UserRole.ANALYST,
    )
    assert user.id is not None

    found = await repo.get_by_email("analyst@fraudshield.ai")
    assert found is not None
    assert found.id == user.id
    assert await repo.email_exists("analyst@fraudshield.ai") is True
    assert await repo.email_exists("nobody@fraudshield.ai") is False


@pytest.mark.asyncio
async def test_transaction_bulk_create_and_feature_vector(db_session):
    repo = TransactionRepository(db_session)
    row = {"time": 0.0, "amount": 149.62}
    for i in range(1, 29):
        row[f"v{i}"] = float(i) * 0.1

    [txn] = await repo.bulk_create([row])
    assert txn.id is not None
    vector = txn.feature_vector()
    assert len(vector) == 28
    assert vector[0] == pytest.approx(0.1)
    assert vector[27] == pytest.approx(2.8)


@pytest.mark.asyncio
async def test_model_version_activation_enforces_single_active(db_session):
    repo = ModelVersionRepository(db_session)

    v1 = await repo.create(
        version_tag="xgboost_v1",
        algorithm="xgboost",
        metrics={"f1": 0.91},
        artifact_path="app/ml/artifacts/xgboost_v1.joblib",
        is_active=True,
        trained_at=datetime.now(timezone.utc),
    )
    v2 = await repo.create(
        version_tag="xgboost_v2",
        algorithm="xgboost",
        metrics={"f1": 0.94},
        artifact_path="app/ml/artifacts/xgboost_v2.joblib",
        is_active=False,
        trained_at=datetime.now(timezone.utc),
    )

    active = await repo.get_active()
    assert active.id == v1.id

    await repo.activate(v2.id)
    await db_session.flush()

    active_after = await repo.get_active()
    assert active_after.id == v2.id

    refreshed_v1 = await repo.get(v1.id)
    assert refreshed_v1.is_active is False


@pytest.mark.asyncio
async def test_prediction_repository_risk_distribution(db_session):
    txn_repo = TransactionRepository(db_session)
    model_repo = ModelVersionRepository(db_session)
    pred_repo = PredictionRepository(db_session)

    row = {"time": 0.0, "amount": 500.0}
    for i in range(1, 29):
        row[f"v{i}"] = 0.0
    [txn] = await txn_repo.bulk_create([row])

    model_version = await model_repo.create(
        version_tag="test_model_v1",
        algorithm="logistic_regression",
        metrics={"f1": 0.85},
        artifact_path="app/ml/artifacts/test_model_v1.joblib",
        is_active=True,
        trained_at=datetime.now(timezone.utc),
    )

    await pred_repo.create(
        transaction_id=txn.id,
        model_version_id=model_version.id,
        predicted_class=PredictedClass.FRAUD,
        fraud_probability=0.98,
        risk_level=RiskLevel.HIGH,
    )
    await db_session.flush()

    distribution = await pred_repo.risk_distribution()
    assert distribution["high"] >= 1
    assert set(distribution.keys()) == {"low", "medium", "high", "critical"}

    class_counts = await pred_repo.count_by_class()
    assert class_counts["fraud"] >= 1
