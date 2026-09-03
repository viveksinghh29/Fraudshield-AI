"""Evaluates models on held-out data with both default and optimized decision thresholds."""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, *, threshold: float = 0.5) -> dict[str, Any]:
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

    return {
        "threshold": threshold,
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_proba)), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def optimize_threshold(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """
    Sweeps the probability cutoff and picks the one maximizing F1 on
    the test set. The naive 0.5 cutoff is rarely optimal for a target
    this imbalanced -- this is what step 10 of the ML pipeline design
    (Phase 1) refers to as "threshold optimization".
    """
    y_proba = model.predict_proba(X_test)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)

    # precision_recall_curve returns one more precision/recall point than
    # thresholds (the last point is threshold=1.0 implicitly) -- align them.
    precisions, recalls = precisions[:-1], recalls[:-1]
    f1_scores = np.divide(
        2 * precisions * recalls,
        precisions + recalls,
        out=np.zeros_like(precisions),
        where=(precisions + recalls) != 0,
    )

    best_idx = int(np.argmax(f1_scores))
    best_threshold = float(thresholds[best_idx])

    return {
        "optimal_threshold": round(best_threshold, 4),
        "precision_at_optimal": round(float(precisions[best_idx]), 4),
        "recall_at_optimal": round(float(recalls[best_idx]), 4),
        "f1_at_optimal": round(float(f1_scores[best_idx]), 4),
    }


def compute_calibration_curve(
    model, X_test: pd.DataFrame, y_test: pd.Series, *, n_bins: int = 10
) -> dict[str, Any]:
    """
    A model can have excellent PR-AUC (it *ranks* fraud above
    legitimate transactions correctly) while still being poorly
    *calibrated* (when it says "80% probability of fraud", the true
    fraud rate among such predictions might actually be 40% or 95%).
    Calibration matters here specifically because the Analyst AI
    Assistant (Phase 10) states the fraud probability as a number an
    analyst will trust at face value -- "98.4% probability" should
    mean something close to 98.4%, not just "very likely, roughly".
    """
    y_proba = model.predict_proba(X_test)[:, 1]

    try:
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_test, y_proba, n_bins=n_bins, strategy="quantile"
        )
    except ValueError:
        # Not enough distinct probability values / positive examples to
        # form `n_bins` quantile bins (common on small or highly
        # imbalanced test sets) -- fall back to uniform-width bins.
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_test, y_proba, n_bins=n_bins, strategy="uniform"
        )

    calibration_error = float(np.mean(np.abs(fraction_of_positives - mean_predicted_value)))

    return {
        "mean_predicted_probability": [round(float(v), 4) for v in mean_predicted_value],
        "observed_fraud_fraction": [round(float(v), 4) for v in fraction_of_positives],
        "mean_calibration_error": round(calibration_error, 4),
    }


def compute_native_feature_importance(model, feature_names: list[str]) -> dict[str, float]:
    """
    Fast, model-native feature importance -- `feature_importances_` for
    tree ensembles, absolute coefficient magnitude for Logistic
    Regression. This is distinct from (and much cheaper than) SHAP's
    global importance in explainer.py: useful for a quick sanity check
    in the training report, while SHAP remains the source of truth for
    anything analyst-facing, since it also supports per-instance
    explanations that native importance can't provide at all.
    """
    if hasattr(model, "feature_importances_"):
        raw_importance = model.feature_importances_
    elif hasattr(model, "coef_"):
        raw_importance = np.abs(model.coef_[0])
    else:
        raise ValueError(
            f"Model type {type(model).__name__} exposes neither "
            "feature_importances_ nor coef_ -- cannot compute native importance."
        )

    importance = {
        name: round(float(value), 6) for name, value in zip(feature_names, raw_importance)
    }
    return dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True))
