"""
SHAP explainability engine.

Dispatches to the fast, exact, model-native SHAP algorithm per model
type rather than always falling back to the slow model-agnostic
Permutation/Kernel explainer -- verified empirically:

    LogisticRegression via a black-box callable (PermutationExplainer): ~6.8s/instance
    RandomForest       via a black-box callable (PermutationExplainer): ~0.8s/instance
    Any tree model     via native TreeExplainer:                        <0.05s/instance
    LogisticRegression via native LinearExplainer:                      <0.01s/instance

At the scale of one explanation per API request (Phase 9's /explain
endpoint, and every turn the Analyst AI Assistant grounds itself in),
that difference is the gap between an instant response and a
multi-second stall, so native explainers are used unconditionally here.

The tradeoff this creates: SHAP values live in different units
depending on the underlying model family --
  - Tree-based models (Random Forest, Gradient Boosting, XGBoost,
    LightGBM): explained directly in PROBABILITY space
    (TreeExplainer(..., model_output="probability")), so a SHAP value
    of +0.05 means "added 5 percentage points to the fraud probability".
  - Logistic Regression: explained in LOG-ODDS (logit) space, the
    space linear models are natively additive in. A SHAP value here
    means "added this many log-odds", not probability points directly.

Every explanation is tagged with `"value_space"` so callers (the
Analyst AI Assistant's context builder, the API layer) know which
units they're looking at, and `fraud_probability` is always taken
directly from the model's own predict_proba() -- never reconstructed
from SHAP values -- so the headline number shown to an analyst is
never at risk of an approximation error, regardless of value_space.
"""

from typing import Any

import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

TREE_MODEL_TYPES = (RandomForestClassifier, GradientBoostingClassifier, XGBClassifier, LGBMClassifier)

# RandomForest's TreeExplainer(model_output="probability") returns SHAP
# values for both classes ((n, features, 2)); GradientBoosting/XGBoost/
# LightGBM return just the positive class ((n, features)). Both are
# handled explicitly rather than assumed, since a wrong shape assumption
# here would silently mis-attribute contributions to the wrong class.
MULTI_OUTPUT_TREE_TYPES = (RandomForestClassifier,)


class FraudExplainer:
    def __init__(self, model: Any, background_data: pd.DataFrame, *, background_sample_size: int = 100):
        self.model = model
        self.feature_names = list(background_data.columns)

        if len(background_data) > background_sample_size:
            self.background = background_data.sample(n=background_sample_size, random_state=42)
        else:
            self.background = background_data

        if isinstance(model, TREE_MODEL_TYPES):
            self.value_space = "probability"
            self.explainer = shap.TreeExplainer(model, self.background, model_output="probability")
            self._is_multi_output = isinstance(model, MULTI_OUTPUT_TREE_TYPES)
        elif isinstance(model, LogisticRegression):
            self.value_space = "log_odds"
            self.explainer = shap.LinearExplainer(model, self.background)
            self._is_multi_output = False
        else:
            raise ValueError(
                f"No native SHAP explainer path configured for model type {type(model).__name__}. "
                "Add it to TREE_MODEL_TYPES (if tree-based) or add a dedicated branch here."
            )

    def _shap_values_for_row(self, x_row: pd.DataFrame) -> tuple[np.ndarray, float]:
        """Returns (per_feature_shap_values, base_value) for one row, normalized to 1D + scalar."""
        raw_values = self.explainer.shap_values(x_row)
        raw_base = self.explainer.expected_value

        if self._is_multi_output:
            # shape (1, features, 2) -- take the fraud class (index 1)
            values = np.array(raw_values)[0, :, 1]
            base = float(np.ravel(raw_base)[1])
        else:
            # shape (1, features) -- already the fraud/positive-class contribution
            values = np.array(raw_values)[0]
            base = float(np.ravel(raw_base)[0])

        return values, base

    def explain_instance(self, x_row: pd.DataFrame) -> dict[str, Any]:
        """
        Local explanation for a single transaction. Returns the shape
        Phase 3's `fraud_explanations` table expects (shap_values,
        top_features, base_value), plus fraud_probability (always from
        predict_proba directly) and value_space.
        """
        if len(x_row) != 1:
            raise ValueError("explain_instance expects exactly one row.")

        values, base_value = self._shap_values_for_row(x_row)

        shap_dict = {
            feature: round(float(value), 6) for feature, value in zip(self.feature_names, values)
        }
        fraud_probability = float(self.model.predict_proba(x_row)[0, 1])
        top_features = _rank_top_features(shap_dict, top_n=10)

        return {
            "shap_values": shap_dict,
            "base_value": round(base_value, 6),
            "top_features": top_features,
            "fraud_probability": round(fraud_probability, 6),
            "prediction_confidence": round(abs(fraud_probability - 0.5) * 2, 4),
            "value_space": self.value_space,
        }

    def explain_global(self, X: pd.DataFrame, *, sample_size: int = 200) -> dict[str, Any]:
        """
        Global feature importance -- mean absolute SHAP value per
        feature across a sample of instances.
        """
        if len(X) > sample_size:
            X = X.sample(n=sample_size, random_state=42)

        raw_values = self.explainer.shap_values(X)

        if self._is_multi_output:
            values = np.array(raw_values)[:, :, 1]
        else:
            values = np.array(raw_values)

        mean_abs_shap = np.abs(values).mean(axis=0)
        importance = {
            feature: round(float(value), 6) for feature, value in zip(self.feature_names, mean_abs_shap)
        }
        ranked = dict(sorted(importance.items(), key=lambda kv: kv[1], reverse=True))

        return {
            "global_feature_importance": ranked,
            "top_10_features": list(ranked.keys())[:10],
            "sample_size_used": len(X),
            "value_space": self.value_space,
        }


def _rank_top_features(shap_dict: dict[str, float], *, top_n: int = 10) -> list[dict[str, Any]]:
    """
    Ranks features by |SHAP value| and labels each as increasing or
    decreasing the fraud probability/log-odds -- this is the structure
    the Analyst AI Assistant (Phase 10) reads directly to ground
    sentences like "Feature V14 had the strongest positive contribution".
    """
    ranked = sorted(shap_dict.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top_n]
    return [
        {
            "feature": feature,
            "shap_value": value,
            "direction": "increases_fraud_probability" if value > 0 else "decreases_fraud_probability",
        }
        for feature, value in ranked
    ]
