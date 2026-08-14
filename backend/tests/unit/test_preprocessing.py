"""Unit tests for app.ml.pipeline.preprocessing."""

import numpy as np
import pandas as pd

from app.ml.pipeline.preprocessing import clean_data


def _base_df(n: int = 20) -> pd.DataFrame:
    data = {"Time": list(range(n)), "Amount": [10.0] * n}
    for i in range(1, 29):
        data[f"V{i}"] = [0.0] * n
    return pd.DataFrame(data)


def test_clean_data_imputes_missing_values_with_median():
    df = _base_df()
    df.loc[0, "Amount"] = np.nan
    df.loc[1, "V1"] = np.nan

    cleaned, report, fitted_params = clean_data(df)

    assert cleaned["Amount"].isnull().sum() == 0
    assert cleaned["V1"].isnull().sum() == 0
    assert report["missing_values_imputed"] == 2
    assert "Amount" in fitted_params["impute_medians"]
    assert "V1" in fitted_params["impute_medians"]


def test_clean_data_removes_exact_duplicates():
    df = _base_df(n=5)
    df_with_dupe = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    cleaned, report, _ = clean_data(df_with_dupe)

    assert report["duplicate_rows_removed"] == 1
    assert len(cleaned) == 5


def test_clean_data_flags_amount_outliers_without_dropping_rows():
    df = _base_df(n=10)
    df.loc[0, "Amount"] = 100_000.0  # extreme outlier

    cleaned, report, _ = clean_data(df)

    assert len(cleaned) == 10  # outliers flagged, never dropped
    assert "is_amount_outlier" in cleaned.columns
    assert cleaned.loc[0, "is_amount_outlier"] == 1
    assert report["amount_outliers_flagged"] >= 1


def test_clean_data_no_op_on_already_clean_data():
    df = _base_df()
    cleaned, report, _ = clean_data(df)

    assert report["missing_values_imputed"] == 0
    assert report["duplicate_rows_removed"] == 0
    assert report["final_row_count"] == len(df)


def test_clean_data_reuses_fitted_params_instead_of_refitting():
    """
    This is the leakage-prevention contract: calling clean_data on a
    second dataframe (standing in for val/test) with a train-fitted
    impute_medians/outlier_bounds must use exactly those values, not
    recompute new ones from the second dataframe's own distribution.
    """
    train_df = _base_df(n=20)
    train_df.loc[0, "Amount"] = np.nan
    train_df.loc[1:18, "Amount"] = 10.0  # median will be 10.0

    _, _, fitted_params = clean_data(train_df)
    assert fitted_params["impute_medians"]["Amount"] == 10.0

    # A val/test dataframe with a totally different distribution and a
    # missing value -- if clean_data refit instead of reusing, the
    # imputed value would NOT be 10.0.
    val_df = _base_df(n=5)
    val_df["Amount"] = [500.0, 500.0, 500.0, 500.0, np.nan]

    val_cleaned, _, _ = clean_data(
        val_df,
        impute_medians=fitted_params["impute_medians"],
        outlier_bounds=fitted_params["outlier_bounds"],
    )
    assert val_cleaned["Amount"].iloc[-1] == 10.0  # reused train median, not val's own median (500.0)
