"""
Data cleaning — missing value handling, duplicate removal, and outlier
flagging.
"""

from typing import Any

import pandas as pd

from app.ml.pipeline.data_loader import REQUIRED_FEATURE_COLUMNS


def clean_data(
    df: pd.DataFrame,
    *,
    impute_medians: dict[str, float] | None = None,
    outlier_bounds: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """
    Args:
        df: raw dataframe to clean.
        impute_medians: previously-fit {column: median} to reuse. If
            None, medians are computed from `df` itself (fit mode --
            use only on the training split).
        outlier_bounds: previously-fit {"lower": x, "upper": y} to
            reuse. If None, computed from `df` itself (fit mode --
            training split only).

    Returns:
        (cleaned_df, report, fitted_params) -- `fitted_params` contains
        whatever was fit (or the reused values, echoed back) so the
        caller can pass them into the next clean_data() call for
        val/test splits without recomputing anything.
    """
    report: dict[str, Any] = {}
    df = df.copy()

    # ---- Missing values ----
    numeric_cols = [c for c in ["Time", "Amount", *REQUIRED_FEATURE_COLUMNS] if c in df.columns]
    missing_before = int(df[numeric_cols].isnull().sum().sum())

    if impute_medians is None:
        # Fit mode: compute medians from this dataframe (must be the train split).
        impute_medians = {col: float(df[col].median()) for col in numeric_cols if df[col].isnull().any()}

    for col, median in impute_medians.items():
        if col in df.columns:
            df[col] = df[col].fillna(median)

    report["missing_values_imputed"] = missing_before

    # ---- Duplicate rows ----
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
    report["duplicate_rows_removed"] = duplicate_count

    # ---- Outlier flagging (IQR method on Amount) ----
    if "Amount" in df.columns:
        if outlier_bounds is None:
            # Fit mode: compute IQR bounds from this dataframe (train split only).
            q1 = df["Amount"].quantile(0.25)
            q3 = df["Amount"].quantile(0.75)
            iqr = q3 - q1
            outlier_bounds = {
                "lower": float(q1 - 1.5 * iqr),
                "upper": float(q3 + 1.5 * iqr),
            }

        df["is_amount_outlier"] = (
            (df["Amount"] < outlier_bounds["lower"]) | (df["Amount"] > outlier_bounds["upper"])
        ).astype(int)

        report["amount_outliers_flagged"] = int(df["is_amount_outlier"].sum())
        report["amount_outlier_bounds"] = {
            "lower": round(outlier_bounds["lower"], 2),
            "upper": round(outlier_bounds["upper"], 2),
        }

    report["final_row_count"] = len(df)

    fitted_params = {
        "impute_medians": impute_medians,
        "outlier_bounds": outlier_bounds,
    }
    return df, report, fitted_params
