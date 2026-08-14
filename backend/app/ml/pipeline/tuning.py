"""
Hyperparameter tuning via Optuna.

Optimizes PR-AUC (not accuracy, not even ROC-AUC) under stratified
cross-validation on the training split, because PR-AUC is the metric
that stays meaningful under heavy class imbalance -- ROC-AUC can look
deceptively good on a ~0.17%-fraud dataset even for a fairly weak
model, since the true-negative rate dominates it.
"""

from typing import Any

import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score

from app.ml.pipeline.model_candidates import RANDOM_STATE, build_model, default_search_space

optuna.logging.set_verbosity(optuna.logging.WARNING)


def _suggest_params(trial: optuna.Trial, search_space: dict[str, tuple]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for name, spec in search_space.items():
        kind = spec[0]
        if kind == "int":
            params[name] = trial.suggest_int(name, spec[1], spec[2])
        elif kind == "float":
            params[name] = trial.suggest_float(name, spec[1], spec[2])
        elif kind == "float_log":
            params[name] = trial.suggest_float(name, spec[1], spec[2], log=True)
        else:
            raise ValueError(f"Unknown search space spec kind: {kind}")
    return params


def tune_model(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    *,
    n_trials: int = 20,
    cv_folds: int = 3,
) -> dict[str, Any]:
    """
    Runs an Optuna study for one candidate model and returns the best
    params found plus the CV PR-AUC score that earned them.
    """
    search_space = default_search_space(model_name)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)

    def objective(trial: optuna.Trial) -> float:
        params = _suggest_params(trial, search_space)
        model = build_model(model_name, params)
        scores = cross_val_score(
            model, X_train, y_train, cv=cv, scoring="average_precision", n_jobs=-1
        )
        return float(np.mean(scores))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return {
        "model_name": model_name,
        "best_params": study.best_params,
        "best_cv_pr_auc": round(study.best_value, 4),
        "n_trials": n_trials,
    }
