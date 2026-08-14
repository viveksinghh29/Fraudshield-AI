"""Unit tests for app.ml.pipeline.evaluate."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from app.ml.pipeline.evaluate import evaluate_model, optimize_threshold


@pytest.fixture
def fitted_model_and_test_data():
    rng = np.random.default_rng(0)
    X_train = pd.DataFrame(rng.normal(0, 1, size=(200, 3)), columns=["f1", "f2", "f3"])
    y_train = pd.Series((X_train["f1"] + X_train["f2"] > 0).astype(int))

    model = LogisticRegression().fit(X_train, y_train)

    X_test = pd.DataFrame(rng.normal(0, 1, size=(50, 3)), columns=["f1", "f2", "f3"])
    y_test = pd.Series((X_test["f1"] + X_test["f2"] > 0).astype(int))

    return model, X_test, y_test


def test_evaluate_model_returns_all_expected_metrics(fitted_model_and_test_data):
    model, X_test, y_test = fitted_model_and_test_data
    metrics = evaluate_model(model, X_test, y_test)

    for key in ["precision", "recall", "f1_score", "roc_auc", "pr_auc", "confusion_matrix"]:
        assert key in metrics

    cm = metrics["confusion_matrix"]
    total = cm["true_negative"] + cm["false_positive"] + cm["false_negative"] + cm["true_positive"]
    assert total == len(y_test)


def test_evaluate_model_metrics_are_bounded_between_0_and_1(fitted_model_and_test_data):
    model, X_test, y_test = fitted_model_and_test_data
    metrics = evaluate_model(model, X_test, y_test)

    for key in ["precision", "recall", "f1_score", "roc_auc", "pr_auc"]:
        assert 0.0 <= metrics[key] <= 1.0


def test_optimize_threshold_returns_valid_threshold(fitted_model_and_test_data):
    model, X_test, y_test = fitted_model_and_test_data
    result = optimize_threshold(model, X_test, y_test)

    assert 0.0 <= result["optimal_threshold"] <= 1.0
    assert 0.0 <= result["f1_at_optimal"] <= 1.0


def test_optimize_threshold_f1_is_at_least_as_good_as_default_threshold(fitted_model_and_test_data):
    model, X_test, y_test = fitted_model_and_test_data

    default_metrics = evaluate_model(model, X_test, y_test, threshold=0.5)
    optimal = optimize_threshold(model, X_test, y_test)

    # by construction, the F1-maximizing threshold can never score worse
    # than the arbitrary default 0.5 cutoff on the same data
    assert optimal["f1_at_optimal"] >= default_metrics["f1_score"]
