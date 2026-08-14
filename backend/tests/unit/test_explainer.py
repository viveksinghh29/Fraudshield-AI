"""
Unit tests for app.ml.engine.explainer.FraudExplainer.

The additivity tests are the ones that actually matter: they prove
SHAP's base_value + sum(shap_values) reconstructs the model's own
prediction, which is the mathematical guarantee that makes an
attribution trustworthy rather than decorative.
"""

import numpy as np
import pandas as pd
import pytest

from app.ml.engine.explainer import FraudExplainer
from app.ml.pipeline.model_candidates import MODEL_NAMES, build_model


def _separable_xy(n_per_class: int = 80, n_features: int = 10):
    rng = np.random.default_rng(7)
    X_legit = rng.normal(0, 1, size=(n_per_class * 5, n_features))
    X_fraud = rng.normal(3, 1, size=(n_per_class, n_features))
    X = pd.DataFrame(
        np.vstack([X_legit, X_fraud]), columns=[f"f{i}" for i in range(n_features)]
    )
    y = pd.Series([0] * (n_per_class * 5) + [1] * n_per_class)
    return X, y


@pytest.fixture(params=MODEL_NAMES)
def fitted_model_and_data(request):
    X, y = _separable_xy()
    model = build_model(request.param)
    model.fit(X, y)
    return request.param, model, X, y


def test_explain_instance_returns_expected_keys(fitted_model_and_data):
    name, model, X, y = fitted_model_and_data
    explainer = FraudExplainer(model, X)

    result = explainer.explain_instance(X.iloc[[0]])

    for key in ["shap_values", "base_value", "top_features", "fraud_probability", "prediction_confidence", "value_space"]:
        assert key in result

    assert result["value_space"] in {"probability", "log_odds"}
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert len(result["shap_values"]) == X.shape[1]


def test_explain_instance_additivity_holds(fitted_model_and_data):
    """
    The core correctness guarantee: base_value + sum(SHAP values)
    must reconstruct the model's actual output for that instance --
    in probability space for tree models, in log-odds space (then
    sigmoid-transformed) for logistic regression.
    """
    name, model, X, y = fitted_model_and_data
    explainer = FraudExplainer(model, X)

    row = X.iloc[[0]]
    result = explainer.explain_instance(row)

    reconstructed = result["base_value"] + sum(result["shap_values"].values())
    actual_proba = model.predict_proba(row)[0, 1]

    if result["value_space"] == "probability":
        assert reconstructed == pytest.approx(actual_proba, abs=1e-3)
    else:  # log_odds
        reconstructed_proba = 1 / (1 + np.exp(-reconstructed))
        assert reconstructed_proba == pytest.approx(actual_proba, abs=1e-3)


def test_explain_instance_rejects_multi_row_input(fitted_model_and_data):
    name, model, X, y = fitted_model_and_data
    explainer = FraudExplainer(model, X)

    with pytest.raises(ValueError, match="exactly one row"):
        explainer.explain_instance(X.iloc[:2])


def test_explain_global_returns_ranked_importance(fitted_model_and_data):
    name, model, X, y = fitted_model_and_data
    explainer = FraudExplainer(model, X)

    result = explainer.explain_global(X, sample_size=50)

    assert "global_feature_importance" in result
    assert len(result["top_10_features"]) <= 10
    importances = list(result["global_feature_importance"].values())
    assert importances == sorted(importances, reverse=True)  # ranked descending


def test_top_features_are_labeled_with_correct_direction(fitted_model_and_data):
    name, model, X, y = fitted_model_and_data
    explainer = FraudExplainer(model, X)

    result = explainer.explain_instance(X.iloc[[0]])
    for feature_info in result["top_features"]:
        if feature_info["shap_value"] > 0:
            assert feature_info["direction"] == "increases_fraud_probability"
        else:
            assert feature_info["direction"] == "decreases_fraud_probability"


def test_unsupported_model_type_raises():
    from sklearn.svm import SVC

    X, y = _separable_xy()
    model = SVC(probability=True).fit(X, y)

    with pytest.raises(ValueError, match="No native SHAP explainer path"):
        FraudExplainer(model, X)
