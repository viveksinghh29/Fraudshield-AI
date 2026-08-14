"""Unit tests for app.ml.pipeline.feature_engineering."""

import pandas as pd
from sklearn.preprocessing import RobustScaler

from app.ml.pipeline.feature_engineering import engineer_features, get_model_feature_columns


def _base_df(n: int = 10) -> pd.DataFrame:
    data = {"Time": [i * 3600.0 for i in range(n)], "Amount": [10.0 * (i + 1) for i in range(n)]}
    for i in range(1, 29):
        data[f"V{i}"] = [0.1 * i] * n
    return pd.DataFrame(data)


def test_engineer_features_adds_expected_columns():
    df = _base_df()
    engineered, scaler, report = engineer_features(df)

    for col in ["amount_log", "hour_of_day", "amount_scaled", "hour_of_day_scaled"]:
        assert col in engineered.columns

    assert isinstance(scaler, RobustScaler)
    assert report["scaler_mode"] == "fit_new"


def test_engineer_features_hour_of_day_wraps_correctly():
    df = _base_df(n=1)
    df.loc[0, "Time"] = 25 * 3600  # 25 hours in -> should wrap to hour 1

    engineered, _, _ = engineer_features(df)
    assert engineered.loc[0, "hour_of_day"] == 1


def test_engineer_features_reuses_existing_scaler_without_refitting():
    train_df = _base_df(n=20)
    _, fitted_scaler, _ = engineer_features(train_df)

    new_row = _base_df(n=1)
    engineered, returned_scaler, report = engineer_features(new_row, scaler=fitted_scaler)

    assert report["scaler_mode"] == "reused_existing"
    assert returned_scaler is fitted_scaler  # same object, not refit


def test_get_model_feature_columns_has_30_features():
    columns = get_model_feature_columns()
    assert len(columns) == 30  # V1-V28 + amount_scaled + hour_of_day_scaled
    assert "amount_scaled" in columns
    assert "hour_of_day_scaled" in columns
    assert "Amount" not in columns  # raw column must not leak into model features
    assert "Time" not in columns
