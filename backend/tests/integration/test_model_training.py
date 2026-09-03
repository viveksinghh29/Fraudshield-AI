"""Integration tests for model training, comparison, and registry using a fast synthetic dataset."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

from app.ml.engine.model_registry import (
    load_model_artifact,
    register_model_version,
    save_model_artifact,
)
from app.ml.pipeline.select_best_model import train_and_compare_all
from app.repositories.model_version_repository import ModelVersionRepository


def _separable_dataset(n_per_class: int = 60):
    """Returns (X_train, X_val, X_test, y_train, y_val, y_test)."""
    rng = np.random.default_rng(42)
    n_features = 30

    X_legit = rng.normal(0, 1, size=(n_per_class * 10, n_features))
    X_fraud = rng.normal(4, 1, size=(n_per_class, n_features))
    X = pd.DataFrame(np.vstack([X_legit, X_fraud]), columns=[f"f{i}" for i in range(n_features)])
    y = pd.Series([0] * (n_per_class * 10) + [1] * n_per_class)

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42, stratify=y_train_full
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


@pytest.mark.asyncio
async def test_train_and_compare_all_selects_a_reasonable_model():
    X_train, X_val, X_test, y_train, y_val, y_test = _separable_dataset()

    result = train_and_compare_all(X_train, y_train, X_val, y_val, X_test, y_test)

    assert result["best_model_name"] in {
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
        "xgboost",
        "lightgbm",
    }
    # this dataset is trivially separable -- any reasonable model should
    # score well above chance
    assert result["best_model_metrics"]["pr_auc"] > 0.8
    assert set(result["comparison"].keys()) == {
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
        "xgboost",
        "lightgbm",
    }


@pytest.mark.asyncio
async def test_threshold_is_selected_on_validation_not_test():
    """
    Leakage-prevention contract: passing a val set that looks nothing
    like the test set should change the selected threshold, proving
    optimize_threshold() is actually reading from X_val/y_val and not
    silently falling back to test data.
    """
    X_train, X_val, X_test, y_train, y_val, y_test = _separable_dataset()

    result_a = train_and_compare_all(X_train, y_train, X_val, y_val, X_test, y_test)

    # Swap in a degenerate all-legitimate validation set -- with no
    # positive examples, F1-optimal threshold selection has no signal
    # to work with and should behave differently from result_a, which
    # is only possible if validation (not test) drives the selection.
    X_val_degenerate = X_val.copy()
    y_val_degenerate = pd.Series([0] * len(y_val))

    result_b = train_and_compare_all(
        X_train, y_train, X_val_degenerate, y_val_degenerate, X_test, y_test
    )

    threshold_a = result_a["best_model_metrics"]["threshold_optimization"]["optimal_threshold"]
    threshold_b = result_b["best_model_metrics"]["threshold_optimization"]["optimal_threshold"]

    # test set metrics at the default 0.5 threshold must be identical
    # regardless of what validation set was used -- test data itself
    # was never touched by either run.
    assert result_a["best_model_metrics"]["pr_auc"] == result_b["best_model_metrics"]["pr_auc"]
    # but the chosen threshold differs, proving it came from validation
    assert threshold_a != threshold_b


@pytest.mark.asyncio
async def test_model_registry_round_trip(db_session, tmp_path):
    X_train, X_val, X_test, y_train, y_val, y_test = _separable_dataset()
    result = train_and_compare_all(X_train, y_train, X_val, y_val, X_test, y_test)

    artifact_path = save_model_artifact(
        model=result["best_model"],
        optimal_threshold=result["best_model_metrics"]["threshold_optimization"]["optimal_threshold"],
        scaler=RobustScaler().fit(X_train),
        background_sample=X_train,
        artifact_dir=tmp_path,
        version_tag="pytest_registry_test",
    )

    model_version_id = await register_model_version(
        db_session,
        version_tag="pytest_registry_test",
        algorithm=result["best_model_name"],
        metrics=result["best_model_metrics"],
        artifact_path=artifact_path,
        activate=True,
    )
    await db_session.flush()

    repo = ModelVersionRepository(db_session)
    active = await repo.get_active()
    assert active is not None
    assert active.id == model_version_id
    assert active.version_tag == "pytest_registry_test"

    bundle = load_model_artifact(artifact_path)
    assert "model" in bundle
    assert "feature_columns" in bundle
    assert "optimal_threshold" in bundle
    assert "scaler" in bundle
    assert "background_sample" in bundle


@pytest.mark.asyncio
async def test_register_model_version_rejects_duplicate_tag(db_session, tmp_path):
    X_train, X_val, X_test, y_train, y_val, y_test = _separable_dataset(n_per_class=20)
    result = train_and_compare_all(X_train, y_train, X_val, y_val, X_test, y_test)

    artifact_path = save_model_artifact(
        model=result["best_model"],
        optimal_threshold=0.5,
        scaler=RobustScaler().fit(X_train),
        background_sample=X_train,
        artifact_dir=tmp_path,
        version_tag="pytest_dup_tag",
    )

    await register_model_version(
        db_session,
        version_tag="pytest_dup_tag",
        algorithm=result["best_model_name"],
        metrics=result["best_model_metrics"],
        artifact_path=artifact_path,
    )
    await db_session.flush()

    with pytest.raises(ValueError, match="already exists"):
        await register_model_version(
            db_session,
            version_tag="pytest_dup_tag",
            algorithm=result["best_model_name"],
            metrics=result["best_model_metrics"],
            artifact_path=artifact_path,
        )
