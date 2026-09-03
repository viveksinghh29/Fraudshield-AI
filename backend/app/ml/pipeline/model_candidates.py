"""Centralized factory for five class-imbalance-aware model candidates with consistent defaults."""

from typing import Any

from lightgbm import LGBMClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

RANDOM_STATE = 42

MODEL_NAMES = [
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
    "xgboost",
    "lightgbm",
]


def build_model(name: str, params: dict[str, Any] | None = None):
    """Returns an unfitted estimator for the given candidate name."""
    params = params or {}

    if name == "logistic_regression":
        return LogisticRegression(
            random_state=RANDOM_STATE,
            max_iter=1000,
            class_weight="balanced",
            **params,
        )

    if name == "random_forest":
        return RandomForestClassifier(
            random_state=RANDOM_STATE,
            class_weight="balanced",
            n_jobs=-1,
            **params,
        )

    if name == "gradient_boosting":
        return GradientBoostingClassifier(random_state=RANDOM_STATE, **params)

    if name == "xgboost":
        return XGBClassifier(
            random_state=RANDOM_STATE,
            eval_metric="aucpr",
            n_jobs=-1,
            **params,
        )

    if name == "lightgbm":
        return LGBMClassifier(
            random_state=RANDOM_STATE,
            class_weight="balanced",
            n_jobs=-1,
            verbosity=-1,
            **params,
        )

    raise ValueError(f"Unknown model name: {name}. Expected one of {MODEL_NAMES}.")


def default_search_space(name: str) -> dict[str, tuple]:
    """
    Optuna search space per model, expressed as
    (param_type, low, high) tuples that tuning.py turns into trial
    suggestions. Kept here (not in tuning.py) so the valid hyperparameter
    ranges live next to the model they belong to.
    """
    if name == "logistic_regression":
        return {"C": ("float_log", 1e-3, 10.0)}

    if name == "random_forest":
        return {
            "n_estimators": ("int", 100, 400),
            "max_depth": ("int", 4, 20),
            "min_samples_split": ("int", 2, 10),
            "min_samples_leaf": ("int", 1, 8),
        }

    if name == "gradient_boosting":
        return {
            "n_estimators": ("int", 100, 300),
            "learning_rate": ("float_log", 0.01, 0.3),
            "max_depth": ("int", 2, 8),
        }

    if name == "xgboost":
        return {
            "n_estimators": ("int", 100, 400),
            "max_depth": ("int", 3, 10),
            "learning_rate": ("float_log", 0.01, 0.3),
            "subsample": ("float", 0.6, 1.0),
            "colsample_bytree": ("float", 0.6, 1.0),
        }

    if name == "lightgbm":
        return {
            "n_estimators": ("int", 100, 400),
            "max_depth": ("int", 3, 12),
            "learning_rate": ("float_log", 0.01, 0.3),
            "num_leaves": ("int", 15, 127),
        }

    raise ValueError(f"Unknown model name: {name}. Expected one of {MODEL_NAMES}.")
