"""
Exploratory Data Analysis — produces a structured, JSON-serializable
report rather than notebook cell output, so it can be surfaced through
an API endpoint or archived alongside a trained model version.
"""

from typing import Any

import pandas as pd

from app.ml.pipeline.data_loader import REQUIRED_FEATURE_COLUMNS


def run_eda(df: pd.DataFrame) -> dict[str, Any]:
    """
    Returns a structured EDA report:
      - class_balance: counts + rate of fraud vs legitimate
      - missing_values: per-column null counts (should be zero on the
        clean Kaggle dataset, but checked explicitly rather than assumed)
      - duplicate_rows: exact-duplicate row count
      - amount_stats: distribution stats for the Amount column, split
        by class (fraud transactions tend to differ meaningfully here)
      - time_stats: min/max/span, useful for spotting single-day vs
        multi-day capture windows
      - feature_correlation_with_class: which V-features correlate
        most strongly with fraud — a first-pass signal before SHAP
        gives per-prediction attribution in Phase 7
    """
    report: dict[str, Any] = {}

    report["row_count"] = len(df)
    report["column_count"] = len(df.columns)

    if "Class" in df.columns:
        fraud_count = int(df["Class"].sum())
        legit_count = len(df) - fraud_count
        report["class_balance"] = {
            "fraud": fraud_count,
            "legitimate": legit_count,
            "fraud_rate_pct": round(100 * fraud_count / len(df), 4) if len(df) else 0.0,
            "imbalance_ratio": round(legit_count / fraud_count, 1) if fraud_count else None,
        }

    missing = df.isnull().sum()
    report["missing_values"] = {col: int(count) for col, count in missing.items() if count > 0}
    report["total_missing_cells"] = int(missing.sum())

    report["duplicate_rows"] = int(df.duplicated().sum())

    if "Amount" in df.columns:
        amount_stats = {
            "overall": _describe_series(df["Amount"]),
        }
        if "Class" in df.columns:
            amount_stats["legitimate"] = _describe_series(df.loc[df["Class"] == 0, "Amount"])
            amount_stats["fraud"] = _describe_series(df.loc[df["Class"] == 1, "Amount"])
        report["amount_stats"] = amount_stats

    if "Time" in df.columns:
        report["time_stats"] = {
            "min": float(df["Time"].min()),
            "max": float(df["Time"].max()),
            "span_hours": round((df["Time"].max() - df["Time"].min()) / 3600, 2),
        }

    if "Class" in df.columns:
        available_features = [c for c in REQUIRED_FEATURE_COLUMNS if c in df.columns]
        if available_features:
            correlations = df[available_features].corrwith(df["Class"]).sort_values(key=abs, ascending=False)
            report["feature_correlation_with_class"] = {
                feature: round(float(value), 4) for feature, value in correlations.head(10).items()
            }

    return report


def _describe_series(series: pd.Series) -> dict[str, float]:
    if len(series) == 0:
        return {"count": 0}
    return {
        "count": int(series.count()),
        "mean": round(float(series.mean()), 2),
        "std": round(float(series.std()), 2) if len(series) > 1 else 0.0,
        "min": round(float(series.min()), 2),
        "p25": round(float(series.quantile(0.25)), 2),
        "median": round(float(series.median()), 2),
        "p75": round(float(series.quantile(0.75)), 2),
        "max": round(float(series.max()), 2),
    }
