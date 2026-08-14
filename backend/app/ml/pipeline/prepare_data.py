"""
Data preparation orchestrator — runs load -> EDA -> split -> clean ->
engineer -> SMOTE as one callable pipeline.

Split happens BEFORE cleaning/feature-engineering are fit. This
ordering is the whole point: imputation medians, outlier IQR bounds,
and the RobustScaler are all statistics learned from data, and fitting
them on anything that includes the test (or validation) split leaks
that split's information into how the training data gets transformed.
Every fitted statistic here is fit once, on the train split only, and
then applied (not refit) to val and test -- the same discipline a
StandardScaler tutorial would call "fit_transform on train, transform
on test", just extended to the imputer and outlier-bound step too.

Callable as a script:
    python -m app.ml.pipeline.prepare_data --input path/to/creditcard.csv

Also callable programmatically (used by train.py in Phase 6, and by
the pipeline's own tests).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib

from app.ml.pipeline.data_loader import dataset_summary, load_transactions_csv
from app.ml.pipeline.eda import run_eda
from app.ml.pipeline.feature_engineering import engineer_features
from app.ml.pipeline.imbalance import apply_smote
from app.ml.pipeline.preprocessing import clean_data
from app.ml.pipeline.split import extract_features_and_target, three_way_split_raw


def prepare_data(
    input_path: str | Path,
    *,
    apply_imbalance_handling: bool = True,
    smote_sampling_strategy: float = 0.5,
    test_size: float = 0.2,
    val_size: float = 0.15,
) -> dict[str, Any]:
    """
    Runs the complete data preparation pipeline against a single CSV
    and returns everything downstream stages need:
      - X_train, y_train (post-SMOTE)
      - X_val, y_val (real distribution, no SMOTE -- for threshold selection)
      - X_test, y_test (real distribution, no SMOTE, touched only by
        the train-fitted scaler -- for final reported metrics)
      - the fitted RobustScaler (must be persisted alongside the model)
      - a combined report from every stage, for logging/auditing
    """
    report: dict[str, Any] = {"input_path": str(input_path)}

    # ---- 1. Load ----
    df = load_transactions_csv(input_path, require_label=True)
    report["raw_summary"] = dataset_summary(df)

    # ---- 2. EDA (purely descriptive on the raw data -- fits nothing,
    #            so running it before the split doesn't leak anything) ----
    report["eda"] = run_eda(df)

    # ---- 3. Split FIRST, before any statistic is fit ----
    train_raw, val_raw, test_raw = three_way_split_raw(df, test_size=test_size, val_size=val_size)
    report["split"] = {
        "train_rows": len(train_raw),
        "val_rows": len(val_raw),
        "test_rows": len(test_raw),
        "train_fraud_count": int(train_raw["Class"].sum()),
        "val_fraud_count": int(val_raw["Class"].sum()),
        "test_fraud_count": int(test_raw["Class"].sum()),
    }

    # ---- 4. Clean: fit imputation/outlier stats on train only, reuse on val/test ----
    train_clean, cleaning_report, fitted_clean_params = clean_data(train_raw)
    val_clean, _, _ = clean_data(
        val_raw,
        impute_medians=fitted_clean_params["impute_medians"],
        outlier_bounds=fitted_clean_params["outlier_bounds"],
    )
    test_clean, _, _ = clean_data(
        test_raw,
        impute_medians=fitted_clean_params["impute_medians"],
        outlier_bounds=fitted_clean_params["outlier_bounds"],
    )
    report["cleaning"] = cleaning_report

    # ---- 5. Feature engineering: fit scaler on train only, reuse on val/test ----
    train_engineered, scaler, fe_report = engineer_features(train_clean)
    val_engineered, _, _ = engineer_features(val_clean, scaler=scaler)
    test_engineered, _, _ = engineer_features(test_clean, scaler=scaler)
    report["feature_engineering"] = fe_report

    # ---- 6. Extract X/y for each split ----
    X_train, y_train = extract_features_and_target(train_engineered)
    X_val, y_val = extract_features_and_target(val_engineered)
    X_test, y_test = extract_features_and_target(test_engineered)

    # ---- 7. SMOTE -- train split only, applied AFTER the val/test splits
    #         already have their final, untouched feature values ----
    if apply_imbalance_handling:
        X_train, y_train, smote_report = apply_smote(
            X_train, y_train, sampling_strategy=smote_sampling_strategy
        )
        report["smote"] = smote_report

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_val": X_val,
        "y_val": y_val,
        "X_test": X_test,
        "y_test": y_test,
        "scaler": scaler,
        "report": report,
    }


def save_pipeline_report(report: dict[str, Any], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)


def _main() -> None:
    parser = argparse.ArgumentParser(description="FraudShield AI — data preparation pipeline")
    parser.add_argument("--input", required=True, help="Path to the raw transactions CSV")
    parser.add_argument(
        "--report-output",
        default="ml_research/reports/data_preparation_report.json",
        help="Where to write the JSON pipeline report",
    )
    parser.add_argument(
        "--scaler-output",
        default="app/ml/artifacts/amount_time_scaler.joblib",
        help="Where to persist the fitted RobustScaler",
    )
    parser.add_argument(
        "--smote-sampling-strategy",
        type=float,
        default=0.5,
        help="Minority:majority ratio after SMOTE resampling",
    )
    args = parser.parse_args()

    result = prepare_data(
        args.input, smote_sampling_strategy=args.smote_sampling_strategy
    )

    save_pipeline_report(result["report"], args.report_output)

    scaler_path = Path(args.scaler_output)
    scaler_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["scaler"], scaler_path)

    print(f"Data preparation complete.")
    print(f"  Train rows (post-SMOTE): {len(result['X_train'])}")
    print(f"  Val rows:                {len(result['X_val'])}")
    print(f"  Test rows:               {len(result['X_test'])}")
    print(f"  Report written to:       {args.report_output}")
    print(f"  Scaler persisted to:     {args.scaler_output}")


if __name__ == "__main__":
    sys.exit(_main() or 0)
