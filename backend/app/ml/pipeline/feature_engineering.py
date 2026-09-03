"""Transforms Amount and Time into robust-scaled features while preserving PCA components and the fitted scaler."""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler


def engineer_features(
    df: pd.DataFrame, *, scaler: RobustScaler | None = None
) -> tuple[pd.DataFrame, RobustScaler, dict[str, Any]]:
    """
    Args:
        df: cleaned dataframe with at least Time and Amount columns.
        scaler: a previously-fit RobustScaler to reuse (inference path).
            If None, a new one is fit on this data (training path).

    Returns:
        (engineered_df, fitted_scaler, report)
    """
    df = df.copy()
    report: dict[str, Any] = {}

    # ---- Amount: log1p transform (handles Amount == 0 safely, unlike log) ----
    df["amount_log"] = np.log1p(df["Amount"])

    # ---- Time: convert elapsed seconds to hour-of-day (0-23) ----
    seconds_in_day = 24 * 3600
    df["hour_of_day"] = ((df["Time"] % seconds_in_day) // 3600).astype(int)

    # ---- Scale the two engineered columns ----
    engineered_cols = ["amount_log", "hour_of_day"]

    if scaler is None:
        scaler = RobustScaler()
        scaled_values = scaler.fit_transform(df[engineered_cols])
        report["scaler_mode"] = "fit_new"
    else:
        scaled_values = scaler.transform(df[engineered_cols])
        report["scaler_mode"] = "reused_existing"

    df["amount_scaled"] = scaled_values[:, 0]
    df["hour_of_day_scaled"] = scaled_values[:, 1]

    report["engineered_columns_added"] = [
        "amount_log",
        "hour_of_day",
        "amount_scaled",
        "hour_of_day_scaled",
    ]
    report["scaler_center"] = scaler.center_.tolist()
    report["scaler_scale"] = scaler.scale_.tolist()

    return df, scaler, report


def get_model_feature_columns() -> list[str]:
    """
    The exact, ordered feature set the model is trained on and expects
    at inference time. V1-V28 (already scaled by the dataset's own PCA)
    plus the two engineered, scaled columns -- raw Time/Amount are
    deliberately excluded once their scaled counterparts exist, to
    avoid feeding the model both the raw and transformed version of
    the same signal.
    """
    from app.ml.pipeline.data_loader import REQUIRED_FEATURE_COLUMNS

    return [*REQUIRED_FEATURE_COLUMNS, "amount_scaled", "hour_of_day_scaled"]
