"""
Integration tests for PredictionService -- exercises the real
Transaction/Prediction persistence path against the live DB, with a
real (if quickly-trained) model registered as active. This is exactly
the path that caught the Time/Amount casing bug: a mock-based test
would never have exercised the real Transaction(**kwargs) call.
"""

import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import RobustScaler

from app.ml.engine.model_registry import register_model_version, save_model_artifact
from app.ml.pipeline.model_candidates import build_model
from app.repositories.model_version_repository import ModelVersionRepository
from app.schemas.prediction_schema import TransactionInput
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionService


def _build_and_register_quick_model(tmp_path, version_tag: str):
    """Fits a tiny RandomForest and returns (model, scaler, X_train) for artifact saving."""
    rng = np.random.default_rng(1)
    n_features_engineered = ["amount_scaled", "hour_of_day_scaled"]
    from app.ml.pipeline.feature_engineering import get_model_feature_columns

    columns = get_model_feature_columns()
    X = pd.DataFrame(rng.normal(0, 1, size=(120, len(columns))), columns=columns)
    y = pd.Series([0] * 100 + [1] * 20)

    model = build_model("random_forest")
    model.fit(X, y)

    scaler = RobustScaler().fit(pd.DataFrame({"amount_log": rng.normal(3, 1, 50), "hour_of_day": rng.integers(0, 24, 50)}))

    artifact_path = save_model_artifact(
        model=model,
        optimal_threshold=0.5,
        scaler=scaler,
        background_sample=X,
        artifact_dir=tmp_path,
        version_tag=version_tag,
    )
    return artifact_path


async def _register_active(db_session, artifact_path: str, version_tag: str) -> uuid.UUID:
    return await register_model_version(
        db_session,
        version_tag=version_tag,
        algorithm="random_forest",
        metrics={"pr_auc": 0.9},
        artifact_path=artifact_path,
        activate=True,
    )


def _sample_transaction_input() -> TransactionInput:
    data = {"Time": 50000.0, "Amount": 250.75}
    for i in range(1, 29):
        data[f"V{i}"] = 0.05 * i
    return TransactionInput(**data)


@pytest.mark.asyncio
async def test_predict_single_persists_transaction_with_correct_field_casing(db_session, tmp_path):
    """
    Regression test for the bug where TransactionInput.to_raw_dict()'s
    Kaggle-schema-cased keys (Time, Amount, V1..V28) were passed
    straight into Transaction(**raw_row), whose ORM columns are
    lowercase -- this raised TypeError at request time. Verifies the
    persisted row actually has the right values under the right
    (lowercase) attribute names.
    """
    ModelService.clear_cache()
    artifact_path = _build_and_register_quick_model(tmp_path, "pytest_predict_service_v1")
    await _register_active(db_session, artifact_path, "pytest_predict_service_v1")
    await db_session.flush()

    service = PredictionService(db_session)
    payload = _sample_transaction_input()

    result = await service.predict_single(payload)

    assert result["transaction_id"] is not None
    assert result["predicted_class"] in {"fraud", "legitimate"}
    assert 0.0 <= result["fraud_probability"] <= 1.0

    transaction = await service.transaction_repo.get_or_404(result["transaction_id"])
    assert transaction.time == 50000.0
    assert float(transaction.amount) == 250.75
    assert transaction.v1 == pytest.approx(0.05)
    assert transaction.v28 == pytest.approx(0.05 * 28)

    ModelService.clear_cache()


@pytest.mark.asyncio
async def test_predict_single_creates_linked_prediction_row(db_session, tmp_path):
    ModelService.clear_cache()
    artifact_path = _build_and_register_quick_model(tmp_path, "pytest_predict_service_v2")
    await _register_active(db_session, artifact_path, "pytest_predict_service_v2")
    await db_session.flush()

    service = PredictionService(db_session)
    result = await service.predict_single(_sample_transaction_input())

    prediction = await service.prediction_repo.get_by_transaction(result["transaction_id"])
    assert prediction is not None
    assert prediction.predicted_class.value == result["predicted_class"]
    assert prediction.fraud_probability == pytest.approx(result["fraud_probability"])

    ModelService.clear_cache()


@pytest.mark.asyncio
async def test_predict_single_raises_when_no_active_model(db_session):
    from app.core.exceptions import ModelNotLoadedError

    ModelService.clear_cache()
    service = PredictionService(db_session)

    # No model registered/activated in this fresh transaction -- should
    # raise a clear, typed error rather than an obscure NoneType crash.
    with pytest.raises(ModelNotLoadedError):
        await service.predict_single(_sample_transaction_input())
