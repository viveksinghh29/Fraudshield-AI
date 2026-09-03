"""Inference engine that loads a model bundle and predicts transactions with consistent preprocessing and lazy SHAP explanations."""

from typing import Any

import pandas as pd

from app.ml.engine.explainer import FraudExplainer
from app.ml.engine.model_registry import load_model_artifact
from app.ml.pipeline.feature_engineering import engineer_features

# Risk-level bucketing is a separate, coarser decision from the
# fraud/legitimate binary cutoff (optimal_threshold): even within
# "flagged as fraud", an analyst benefits from knowing whether a
# transaction is borderline or overwhelming. These bounds are fixed
# business thresholds, not fit from data.
RISK_LEVEL_BOUNDS = [
    (0.30, "low"),
    (0.60, "medium"),
    (0.85, "high"),
]
RISK_LEVEL_CRITICAL = "critical"


def _risk_level_for_probability(probability: float) -> str:
    for upper_bound, level in RISK_LEVEL_BOUNDS:
        if probability < upper_bound:
            return level
    return RISK_LEVEL_CRITICAL


class Predictor:
    def __init__(self, artifact_path: str):
        bundle = load_model_artifact(artifact_path)
        self.model = bundle["model"]
        self.feature_columns = bundle["feature_columns"]
        self.optimal_threshold = bundle["optimal_threshold"]
        self.scaler = bundle["scaler"]
        self.background_sample = bundle["background_sample"]
        self._explainer: FraudExplainer | None = None

    @property
    def explainer(self) -> FraudExplainer:
        if self._explainer is None:
            self._explainer = FraudExplainer(self.model, self.background_sample)
        return self._explainer

    def _raw_row_to_features(self, raw_row: dict[str, Any]) -> pd.DataFrame:
        """
        Takes a single raw transaction (Time, Amount, V1-V28) and
        applies the exact Phase 5 feature-engineering step -- reusing
        this bundle's fitted scaler, never refitting -- to produce the
        model's expected feature vector, in the model's expected
        column order.
        """
        df = pd.DataFrame([raw_row])
        engineered, _, _ = engineer_features(df, scaler=self.scaler)
        return engineered[self.feature_columns]

    def predict(self, raw_row: dict[str, Any]) -> dict[str, Any]:
        """
        Args:
            raw_row: dict with keys Time, Amount, V1..V28 (matching the
                Kaggle schema fields transactions are stored with).

        Returns: predicted_class, fraud_probability, risk_level --
            everything PredictionService needs to persist a Prediction row.
        """
        features = self._raw_row_to_features(raw_row)
        fraud_probability = float(self.model.predict_proba(features)[0, 1])
        predicted_class = "fraud" if fraud_probability >= self.optimal_threshold else "legitimate"
        risk_level = _risk_level_for_probability(fraud_probability)

        return {
            "fraud_probability": round(fraud_probability, 6),
            "predicted_class": predicted_class,
            "risk_level": risk_level,
            "threshold_used": self.optimal_threshold,
        }

    def explain(self, raw_row: dict[str, Any]) -> dict[str, Any]:
        """Full SHAP explanation for a single raw transaction (see FraudExplainer.explain_instance)."""
        features = self._raw_row_to_features(raw_row)
        return self.explainer.explain_instance(features)

    def predict_batch(self, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Vectorized batch prediction -- one feature-engineering pass and
        one predict_proba call for the whole batch, instead of looping
        row by row. Used by the Celery batch-prediction task (Phase 8)
        for CSV uploads that may contain thousands of rows.
        """
        df = pd.DataFrame(raw_rows)
        engineered, _, _ = engineer_features(df, scaler=self.scaler)
        X = engineered[self.feature_columns]

        fraud_probabilities = self.model.predict_proba(X)[:, 1]

        results = []
        for probability in fraud_probabilities:
            probability = float(probability)
            results.append(
                {
                    "fraud_probability": round(probability, 6),
                    "predicted_class": "fraud" if probability >= self.optimal_threshold else "legitimate",
                    "risk_level": _risk_level_for_probability(probability),
                    "threshold_used": self.optimal_threshold,
                }
            )
        return results
