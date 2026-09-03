"""
Model comparison and automatic best-model selection.
"""

from typing import Any

import pandas as pd

from app.ml.pipeline.evaluate import evaluate_model, optimize_threshold
from app.ml.pipeline.model_candidates import MODEL_NAMES, build_model

PR_AUC_TIE_MARGIN = 0.01


def train_and_compare_all(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    tuned_params: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Trains every candidate in MODEL_NAMES on (X_train, y_train), each
    with its tuned params if provided (falls back to the factory's
    class-imbalance-aware defaults otherwise). The decision threshold
    is optimized on (X_val, y_val). Final metrics -- at both the
    default 0.5 cutoff and the val-chosen optimal cutoff -- are then
    computed on the untouched (X_test, y_test), exactly once.
    """
    tuned_params = tuned_params or {}
    results: dict[str, Any] = {}
    fitted_models: dict[str, Any] = {}

    for name in MODEL_NAMES:
        params = tuned_params.get(name, {})
        model = build_model(name, params)
        model.fit(X_train, y_train)

        # Threshold chosen on validation data only.
        threshold_info = optimize_threshold(model, X_val, y_val)
        optimal_threshold = threshold_info["optimal_threshold"]

        # Final, one-time evaluation on the untouched test set, at both
        # the naive default cutoff and the val-selected optimal cutoff.
        default_metrics = evaluate_model(model, X_test, y_test, threshold=0.5)
        optimal_metrics = evaluate_model(model, X_test, y_test, threshold=optimal_threshold)

        results[name] = {
            **default_metrics,
            "threshold_optimization": {
                **threshold_info,
                "test_set_metrics_at_optimal_threshold": optimal_metrics,
            },
        }
        fitted_models[name] = model

    best_name = _select_best(results)

    return {
        "comparison": results,
        "best_model_name": best_name,
        "best_model": fitted_models[best_name],
        "best_model_metrics": results[best_name],
    }


def _select_best(results: dict[str, dict[str, Any]]) -> str:
    ranked = sorted(results.items(), key=lambda item: item[1]["pr_auc"], reverse=True)
    top_pr_auc = ranked[0][1]["pr_auc"]

    # Every candidate within PR_AUC_TIE_MARGIN of the top score is
    # considered "tied" -- among those, prefer the highest recall.
    contenders = [
        (name, metrics) for name, metrics in ranked if top_pr_auc - metrics["pr_auc"] <= PR_AUC_TIE_MARGIN
    ]
    contenders.sort(key=lambda item: item[1]["recall"], reverse=True)

    return contenders[0][0]
