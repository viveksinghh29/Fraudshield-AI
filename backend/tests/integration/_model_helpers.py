"""Shared API test helper for registering an active model required by prediction, explanation, and analytics tests."""

import uuid

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

from app.ml.engine.model_registry import register_model_version, save_model_artifact
from app.ml.pipeline.feature_engineering import get_model_feature_columns
from app.ml.pipeline.model_candidates import build_model
from app.services.model_service import ModelService


async def register_quick_active_model(db_session, tmp_path, version_tag: str | None = None) -> str:
    """Fits a tiny RandomForest and registers+activates it. Returns the version_tag used."""
    ModelService.clear_cache()

    version_tag = version_tag or f"pytest_api_{uuid.uuid4().hex[:8]}"

    rng = np.random.default_rng(11)
    columns = get_model_feature_columns()
    X = pd.DataFrame(rng.normal(0, 1, size=(120, len(columns))), columns=columns)
    y = pd.Series([0] * 100 + [1] * 20)

    model = build_model("random_forest")
    model.fit(X, y)

    scaler = RobustScaler().fit(
        pd.DataFrame({"amount_log": rng.normal(3, 1, 50), "hour_of_day": rng.integers(0, 24, 50)})
    )

    artifact_path = save_model_artifact(
        model=model,
        optimal_threshold=0.5,
        scaler=scaler,
        background_sample=X,
        artifact_dir=tmp_path,
        version_tag=version_tag,
    )

    await register_model_version(
        db_session,
        version_tag=version_tag,
        algorithm="random_forest",
        metrics={
            "precision": 0.9,
            "recall": 0.85,
            "f1_score": 0.87,
            "roc_auc": 0.95,
            "pr_auc": 0.9,
            "threshold": 0.5,
            "confusion_matrix": {
                "true_negative": 95,
                "false_positive": 5,
                "false_negative": 3,
                "true_positive": 17,
            },
        },
        artifact_path=artifact_path,
        activate=True,
    )
    await db_session.commit()

    return version_tag


def sample_transaction_payload(amount: float = 250.75) -> dict:
    data = {"Time": 45000.0, "Amount": amount}
    for i in range(1, 29):
        data[f"V{i}"] = 0.05 * i
    return data
