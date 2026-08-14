"""Unit tests for app.ml.pipeline.data_loader."""

import pandas as pd
import pytest

from app.ml.pipeline.data_loader import (
    SchemaValidationError,
    dataset_summary,
    load_transactions_csv,
)


def _valid_df(n: int = 10) -> pd.DataFrame:
    data = {"Time": list(range(n)), "Amount": [10.0 + i for i in range(n)]}
    for i in range(1, 29):
        data[f"V{i}"] = [0.1 * i] * n
    data["Class"] = [0] * (n - 1) + [1]
    return pd.DataFrame(data)


def test_load_valid_csv(tmp_path):
    csv_path = tmp_path / "valid.csv"
    _valid_df().to_csv(csv_path, index=False)

    df = load_transactions_csv(csv_path)
    assert len(df) == 10
    assert "V28" in df.columns


def test_load_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_transactions_csv(tmp_path / "does_not_exist.csv")


def test_load_missing_columns_raises_schema_error(tmp_path):
    df = _valid_df().drop(columns=["V28"])
    csv_path = tmp_path / "missing_col.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(SchemaValidationError, match="V28"):
        load_transactions_csv(csv_path)


def test_load_invalid_class_values_raises_schema_error(tmp_path):
    df = _valid_df()
    df["Class"] = 2  # invalid — must be 0 or 1
    csv_path = tmp_path / "bad_class.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(SchemaValidationError, match="Class"):
        load_transactions_csv(csv_path)


def test_load_without_requiring_label_allows_missing_class(tmp_path):
    df = _valid_df().drop(columns=["Class"])
    csv_path = tmp_path / "no_label.csv"
    df.to_csv(csv_path, index=False)

    df_loaded = load_transactions_csv(csv_path, require_label=False)
    assert "Class" not in df_loaded.columns


def test_dataset_summary_reports_fraud_counts():
    df = _valid_df()
    summary = dataset_summary(df)
    assert summary["rows"] == 10
    assert summary["fraud_count"] == 1
    assert summary["legitimate_count"] == 9
