"""Builds factual LLM context from predictions, SHAP values, and transaction data to prevent hallucinations and enable auditing."""

from typing import Any


def build_transaction_context(
    *,
    transaction_id: str,
    transaction_time: float,
    transaction_amount: float,
    predicted_class: str,
    fraud_probability: float,
    risk_level: str,
    model_version: str,
    top_features: list[dict[str, Any]],
    base_value: float,
    value_space: str,
) -> dict[str, Any]:
    """Returns the structured context dict -- both rendered into the system prompt and persisted as-is."""
    return {
        "transaction_id": transaction_id,
        "transaction_time": transaction_time,
        "transaction_amount": transaction_amount,
        "prediction": {
            "predicted_class": predicted_class,
            "fraud_probability": fraud_probability,
            "risk_level": risk_level,
            "model_version": model_version,
            "confidence": round(abs(fraud_probability - 0.5) * 2, 4),
        },
        "explanation": {
            "base_value": base_value,
            "value_space": value_space,
            "top_contributing_features": top_features,
        },
    }


def render_context_as_text(context: dict[str, Any]) -> str:
    """
    Renders the structured context into the plain-text block inserted
    into the system prompt. Kept deliberately simple and literal
    (labeled key: value lines) rather than prose, so the LLM has no
    ambiguity about what's a fact from the data vs. anything else.
    """
    prediction = context["prediction"]
    explanation = context["explanation"]

    lines = [
        f"Transaction ID: {context['transaction_id']}",
        f"Transaction Time (seconds elapsed): {context['transaction_time']}",
        f"Transaction Amount: {context['transaction_amount']}",
        "",
        f"Model Prediction: {prediction['predicted_class']}",
        f"Fraud Probability: {prediction['fraud_probability']:.4f}",
        f"Risk Level: {prediction['risk_level']}",
        f"Model Version: {prediction['model_version']}",
        f"Prediction Confidence: {prediction['confidence']:.4f}",
        "",
        f"SHAP Base Value ({explanation['value_space']} space): {explanation['base_value']:.6f}",
        "Top Contributing Features (ranked by |SHAP value|):",
    ]

    for feature in explanation["top_contributing_features"]:
        lines.append(
            f"  - {feature['feature']}: SHAP value {feature['shap_value']:+.6f} "
            f"({feature['direction']})"
        )

    return "\n".join(lines)
