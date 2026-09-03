"""
Class imbalance handling via SMOTE.

"""

from typing import Any

import pandas as pd
from imblearn.over_sampling import SMOTE

from app.ml.pipeline.split import RANDOM_STATE


def apply_smote(
    X_train: pd.DataFrame, y_train: pd.Series, *, sampling_strategy: float = 0.5
) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    """
    Args:
        sampling_strategy: ratio of minority to majority class after
            resampling (0.5 = minority class becomes 50% the size of
            the majority class). Full 1.0 balance is deliberately not
            the default -- over-balancing a dataset this imbalanced
            (~0.17% fraud) tends to push models toward too many false
            positives; 0.5 is a starting point tuned further via
            Optuna in Phase 6.

    Returns:
        (X_resampled, y_resampled, report)
    """
    before_counts = y_train.value_counts().to_dict()

    smote = SMOTE(sampling_strategy=sampling_strategy, random_state=RANDOM_STATE)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    after_counts = y_resampled.value_counts().to_dict()

    report = {
        "before": {str(k): int(v) for k, v in before_counts.items()},
        "after": {str(k): int(v) for k, v in after_counts.items()},
        "synthetic_samples_created": int(len(y_resampled) - len(y_train)),
        "sampling_strategy": sampling_strategy,
    }

    return X_resampled, y_resampled, report
