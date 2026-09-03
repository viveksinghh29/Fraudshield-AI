"""Schema-driven CSV loader that validates Kaggle fraud data before downstream processing."""

from pathlib import Path

import pandas as pd

REQUIRED_FEATURE_COLUMNS = [f"V{i}" for i in range(1, 29)]
REQUIRED_COLUMNS = ["Time", "Amount", *REQUIRED_FEATURE_COLUMNS]
# "Class" is required for training data but absent for pure inference batches,
# so it's validated separately via `require_label`.


class SchemaValidationError(ValueError):
    """Raised when a CSV doesn't match the expected Kaggle-style schema."""


def load_transactions_csv(path: str | Path, *, require_label: bool = True) -> pd.DataFrame:
    """
    Load and validate a transactions CSV.

    Args:
        path: path to the CSV file.
        require_label: if True, the `Class` column must be present
            (training/evaluation use). Set False for inference-only
            batches that don't carry ground truth.

    Raises:
        FileNotFoundError: if `path` doesn't exist.
        SchemaValidationError: if required columns are missing or the
            feature columns aren't numeric.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at: {path}")

    df = pd.read_csv(path)

    expected = set(REQUIRED_COLUMNS) | ({"Class"} if require_label else set())
    missing = expected - set(df.columns)
    if missing:
        raise SchemaValidationError(
            f"CSV at {path} is missing required columns: {sorted(missing)}"
        )

    non_numeric = [
        col for col in REQUIRED_COLUMNS if not pd.api.types.is_numeric_dtype(df[col])
    ]
    if non_numeric:
        raise SchemaValidationError(
            f"CSV at {path} has non-numeric values in expected-numeric columns: {non_numeric}"
        )

    if require_label and not pd.api.types.is_numeric_dtype(df["Class"]):
        raise SchemaValidationError("`Class` column must be numeric (0 = legitimate, 1 = fraud).")

    if require_label and not set(df["Class"].unique()).issubset({0, 1}):
        raise SchemaValidationError("`Class` column must contain only 0 (legitimate) or 1 (fraud).")

    return df


def dataset_summary(df: pd.DataFrame) -> dict:
    """Quick shape/row-count summary — used by both EDA and CLI logging."""
    summary = {
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }
    if "Class" in df.columns:
        fraud_count = int(df["Class"].sum())
        summary["fraud_count"] = fraud_count
        summary["legitimate_count"] = len(df) - fraud_count
        summary["fraud_rate_pct"] = round(100 * fraud_count / len(df), 4) if len(df) else 0.0
    return summary
