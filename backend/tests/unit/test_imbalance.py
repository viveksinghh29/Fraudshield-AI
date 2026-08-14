"""Unit tests for app.ml.pipeline.imbalance and the split/SMOTE leakage boundary."""

import pandas as pd

from app.ml.pipeline.imbalance import apply_smote


def _imbalanced_xy(n_majority: int = 200, n_minority: int = 10):
    import numpy as np

    rng = np.random.default_rng(0)
    X_majority = pd.DataFrame(rng.normal(0, 1, size=(n_majority, 5)), columns=[f"f{i}" for i in range(5)])
    X_minority = pd.DataFrame(rng.normal(3, 1, size=(n_minority, 5)), columns=[f"f{i}" for i in range(5)])
    X = pd.concat([X_majority, X_minority], ignore_index=True)
    y = pd.Series([0] * n_majority + [1] * n_minority)
    return X, y


def test_apply_smote_increases_minority_class_to_target_ratio():
    X, y = _imbalanced_xy(n_majority=200, n_minority=10)

    X_resampled, y_resampled, report = apply_smote(X, y, sampling_strategy=0.5)

    counts = y_resampled.value_counts()
    assert counts[0] == 200  # majority class untouched
    assert counts[1] == 100  # 0.5 * 200
    assert report["synthetic_samples_created"] == 90
    assert report["before"]["1"] == 10
    assert report["after"]["1"] == 100


def test_apply_smote_does_not_modify_majority_rows():
    X, y = _imbalanced_xy(n_majority=200, n_minority=10)
    original_majority_rows = X[y == 0].reset_index(drop=True)

    X_resampled, y_resampled, _ = apply_smote(X, y, sampling_strategy=0.5)
    resampled_majority_rows = X_resampled[y_resampled == 0].reset_index(drop=True)

    pd.testing.assert_frame_equal(original_majority_rows, resampled_majority_rows)


def test_apply_smote_only_touches_the_data_passed_in():
    """
    Guards the no-leakage principle documented in imbalance.py: calling
    apply_smote with only the training split means test data is never
    seen by SMOTE, by construction (the function has no test-data
    parameter at all).
    """
    import inspect

    from app.ml.pipeline.imbalance import apply_smote as fn

    params = list(inspect.signature(fn).parameters.keys())
    assert "X_test" not in params
    assert "y_test" not in params
