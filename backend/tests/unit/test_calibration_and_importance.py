"""Unit tests for the calibration and native-importance additions to evaluate.py."""

import numpy as np
import pandas as pd
import pytest

from app.ml.pipeline.evaluate import compute_calibration_curve, compute_native_feature_importance
from app.ml.pipeline.model_candidates import build_model


def _fitted_model_and_test_data(name: str, n_per_class: int = 100):
    rng = np.random.default_rng(3)
    n_features = 8
    X_legit = rng.normal(0, 1, size=(n_per_class * 8, n_features))
    X_fraud = rng.normal(2.5, 1, size=(n_per_class, n_features))
    X = pd.DataFrame(np.vstack([X_legit, X_fraud]), columns=[f"f{i}" for i in range(n_features)])
    y = pd.Series([0] * (n_per_class * 8) + [1] * n_per_class)

    model = build_model(name)
    model.fit(X, y)
    return model, X, y


def test_compute_calibration_curve_returns_matching_length_arrays():
    model, X, y = _fitted_model_and_test_data("random_forest")
    result = compute_calibration_curve(model, X, y, n_bins=5)

    assert len(result["mean_predicted_probability"]) == len(result["observed_fraud_fraction"])
    assert result["mean_calibration_error"] >= 0.0


def test_compute_calibration_curve_values_are_valid_probabilities():
    model, X, y = _fitted_model_and_test_data("logistic_regression")
    result = compute_calibration_curve(model, X, y, n_bins=5)

    for value in result["mean_predicted_probability"] + result["observed_fraud_fraction"]:
        assert 0.0 <= value <= 1.0


def test_compute_native_feature_importance_tree_model_uses_feature_importances():
    model, X, y = _fitted_model_and_test_data("random_forest")
    importance = compute_native_feature_importance(model, list(X.columns))

    assert set(importance.keys()) == set(X.columns)
    values = list(importance.values())
    assert values == sorted(values, reverse=True)
    assert all(v >= 0 for v in values)  # feature_importances_ is always non-negative


def test_compute_native_feature_importance_linear_model_uses_coef():
    model, X, y = _fitted_model_and_test_data("logistic_regression")
    importance = compute_native_feature_importance(model, list(X.columns))

    assert set(importance.keys()) == set(X.columns)
    # coef-based importance is abs(coef), so also always non-negative
    assert all(v >= 0 for v in importance.values())


def test_compute_native_feature_importance_unsupported_model_raises():
    from sklearn.svm import SVC

    X = pd.DataFrame(np.random.default_rng(0).normal(0, 1, size=(20, 3)), columns=["a", "b", "c"])
    y = pd.Series([0] * 10 + [1] * 10)
    model = SVC().fit(X, y)

    with pytest.raises(ValueError, match="neither"):
        compute_native_feature_importance(model, list(X.columns))
