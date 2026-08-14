"""
Training orchestrator — the Phase 6 entry point.

Runs: prepare_data (Phase 5) -> hyperparameter tuning (Optuna, one
study per candidate) -> train + compare all 5 candidates on their
tuned params -> select the best -> persist the artifact -> register
it in the model_versions table (Phase 3) as the new active model.

Usage:
    python -m app.ml.pipeline.train --input path/to/creditcard.csv
    python -m app.ml.pipeline.train --input ... --n-trials 5 --skip-tuning
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from app.db.session import AsyncSessionLocal
from app.ml.engine.explainer import FraudExplainer
from app.ml.engine.model_registry import register_model_version, save_model_artifact
from app.ml.pipeline.evaluate import compute_calibration_curve, compute_native_feature_importance
from app.ml.pipeline.prepare_data import prepare_data, save_pipeline_report
from app.ml.pipeline.select_best_model import train_and_compare_all
from app.ml.pipeline.tuning import tune_model
from app.ml.pipeline.model_candidates import MODEL_NAMES


async def run_training(
    *,
    input_path: str,
    n_trials: int,
    skip_tuning: bool,
    artifact_dir: str,
    report_output: str,
    version_tag: str,
) -> dict[str, Any]:
    report: dict[str, Any] = {}

    # ---- Phase 5 data preparation ----
    prep = prepare_data(input_path)
    report["data_preparation"] = prep["report"]
    X_train, X_val, X_test = prep["X_train"], prep["X_val"], prep["X_test"]
    y_train, y_val, y_test = prep["y_train"], prep["y_val"], prep["y_test"]

    # ---- Hyperparameter tuning (Optuna, one study per candidate) ----
    tuned_params: dict[str, dict[str, Any]] = {}
    tuning_report: dict[str, Any] = {}

    if not skip_tuning:
        for name in MODEL_NAMES:
            result = tune_model(name, X_train, y_train, n_trials=n_trials)
            tuned_params[name] = result["best_params"]
            tuning_report[name] = result
    report["tuning"] = tuning_report

    # ---- Train + compare all candidates on tuned params ----
    comparison = train_and_compare_all(
        X_train, y_train, X_val, y_val, X_test, y_test, tuned_params=tuned_params
    )
    report["comparison"] = {
        name: {k: v for k, v in metrics.items()} for name, metrics in comparison["comparison"].items()
    }
    report["best_model_name"] = comparison["best_model_name"]
    report["best_model_metrics"] = comparison["best_model_metrics"]

    # ---- Phase 7: calibration, native importance, and SHAP for the winner ----
    best_model = comparison["best_model"]
    report["best_model_metrics"]["calibration"] = compute_calibration_curve(best_model, X_test, y_test)
    report["best_model_metrics"]["native_feature_importance"] = compute_native_feature_importance(
        best_model, list(X_train.columns)
    )

    explainer = FraudExplainer(best_model, X_train)
    report["best_model_metrics"]["shap_global_importance"] = explainer.explain_global(X_test)

    # ---- Persist artifact ----
    optimal_threshold = comparison["best_model_metrics"]["threshold_optimization"]["optimal_threshold"]
    artifact_path = save_model_artifact(
        model=comparison["best_model"],
        optimal_threshold=optimal_threshold,
        scaler=prep["scaler"],
        background_sample=X_train,
        artifact_dir=artifact_dir,
        version_tag=version_tag,
    )
    report["artifact_path"] = artifact_path

    # ---- Register in model_versions table, activate it ----
    async with AsyncSessionLocal() as session:
        model_version_id = await register_model_version(
            session,
            version_tag=version_tag,
            algorithm=comparison["best_model_name"],
            metrics=comparison["best_model_metrics"],
            artifact_path=artifact_path,
            activate=True,
        )
        await session.commit()
    report["model_version_id"] = str(model_version_id)

    save_pipeline_report(report, report_output)
    return report


def _main() -> None:
    parser = argparse.ArgumentParser(description="FraudShield AI — model training pipeline")
    parser.add_argument("--input", required=True, help="Path to the training CSV")
    parser.add_argument("--n-trials", type=int, default=15, help="Optuna trials per candidate model")
    parser.add_argument("--skip-tuning", action="store_true", help="Skip Optuna, use factory defaults")
    parser.add_argument("--artifact-dir", default="app/ml/artifacts")
    parser.add_argument("--report-output", default="ml_research/reports/training_report.json")
    parser.add_argument(
        "--version-tag",
        default=None,
        help="Unique tag for this model version (default: <algorithm>_<timestamp>, filled in after training)",
    )
    args = parser.parse_args()

    version_tag = args.version_tag
    if version_tag is None:
        import time

        version_tag = f"model_{int(time.time())}"

    report = asyncio.run(
        run_training(
            input_path=args.input,
            n_trials=args.n_trials,
            skip_tuning=args.skip_tuning,
            artifact_dir=args.artifact_dir,
            report_output=args.report_output,
            version_tag=version_tag,
        )
    )

    print("Training complete.")
    print(f"  Best model:            {report['best_model_name']}")
    print(f"  PR-AUC:                {report['best_model_metrics']['pr_auc']}")
    print(f"  Recall:                {report['best_model_metrics']['recall']}")
    print(f"  Precision:             {report['best_model_metrics']['precision']}")
    print(f"  Optimal threshold:     {report['best_model_metrics']['threshold_optimization']['optimal_threshold']}")
    print(f"  Calibration error:     {report['best_model_metrics']['calibration']['mean_calibration_error']}")
    print(f"  Top 3 SHAP features:   {report['best_model_metrics']['shap_global_importance']['top_10_features'][:3]}")
    print(f"  Artifact:              {report['artifact_path']}")
    print(f"  Model version ID:      {report['model_version_id']}")


if __name__ == "__main__":
    sys.exit(_main() or 0)
