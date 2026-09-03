"""Unit tests for data splitting that verify no rows overlap across train, validation, and test sets."""

import pandas as pd

from app.ml.pipeline.split import extract_features_and_target, three_way_split_raw


def _synthetic_df(n: int = 500, fraud_rate: float = 0.1) -> pd.DataFrame:
    import numpy as np

    rng = np.random.default_rng(0)
    n_fraud = int(n * fraud_rate)
    n_legit = n - n_fraud

    data = {"Time": rng.uniform(0, 100_000, n), "Amount": rng.uniform(1, 500, n)}
    for i in range(1, 29):
        data[f"V{i}"] = rng.normal(0, 1, n)
    data["Class"] = [0] * n_legit + [1] * n_fraud

    return pd.DataFrame(data).sample(frac=1, random_state=0).reset_index(drop=True)


def test_three_way_split_produces_no_row_overlap():
    df = _synthetic_df(n=1000)
    train_df, val_df, test_df = three_way_split_raw(df, test_size=0.2, val_size=0.15)

    # Use a content-based identity (every column, not just an index) so
    # this genuinely checks for duplicated ROWS across splits, not just
    # duplicated positional indices which get reset by each split call.
    train_keys = set(map(tuple, train_df.values.tolist()))
    val_keys = set(map(tuple, val_df.values.tolist()))
    test_keys = set(map(tuple, test_df.values.tolist()))

    assert train_keys.isdisjoint(val_keys)
    assert train_keys.isdisjoint(test_keys)
    assert val_keys.isdisjoint(test_keys)


def test_three_way_split_preserves_all_rows_exactly_once():
    df = _synthetic_df(n=1000)
    train_df, val_df, test_df = three_way_split_raw(df, test_size=0.2, val_size=0.15)

    assert len(train_df) + len(val_df) + len(test_df) == len(df)


def test_three_way_split_is_stratified_on_class():
    df = _synthetic_df(n=2000, fraud_rate=0.1)
    train_df, val_df, test_df = three_way_split_raw(df, test_size=0.2, val_size=0.15)

    overall_rate = df["Class"].mean()
    for split_df, name in [(train_df, "train"), (val_df, "val"), (test_df, "test")]:
        split_rate = split_df["Class"].mean()
        assert abs(split_rate - overall_rate) < 0.03, f"{name} fraud rate {split_rate} drifted too far"


def test_three_way_split_is_reproducible():
    df = _synthetic_df(n=500)
    train_a, val_a, test_a = three_way_split_raw(df)
    train_b, val_b, test_b = three_way_split_raw(df)

    pd.testing.assert_frame_equal(train_a, train_b)
    pd.testing.assert_frame_equal(val_a, val_b)
    pd.testing.assert_frame_equal(test_a, test_b)


def test_extract_features_and_target_excludes_non_feature_columns():
    df = _synthetic_df(n=10)
    df["amount_scaled"] = 0.0
    df["hour_of_day_scaled"] = 0.0

    X, y = extract_features_and_target(df)

    assert "Class" not in X.columns
    assert "Time" not in X.columns
    assert "Amount" not in X.columns
    assert len(y) == len(df)
