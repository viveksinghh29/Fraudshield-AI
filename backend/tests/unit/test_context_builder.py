"""Unit tests for app.llm.context_builder."""

from app.llm.context_builder import build_transaction_context, render_context_as_text


def _sample_context():
    return build_transaction_context(
        transaction_id="5821",
        transaction_time=45000.0,
        transaction_amount=1200.50,
        predicted_class="fraud",
        fraud_probability=0.984,
        risk_level="critical",
        model_version="xgboost_v3",
        top_features=[
            {"feature": "V14", "shap_value": 0.21, "direction": "increases_fraud_probability"},
            {"feature": "V12", "shap_value": 0.15, "direction": "increases_fraud_probability"},
            {"feature": "V4", "shap_value": -0.05, "direction": "decreases_fraud_probability"},
        ],
        base_value=0.12,
        value_space="probability",
    )


def test_build_transaction_context_has_expected_structure():
    context = _sample_context()

    assert context["transaction_id"] == "5821"
    assert context["prediction"]["predicted_class"] == "fraud"
    assert context["prediction"]["fraud_probability"] == 0.984
    assert context["explanation"]["value_space"] == "probability"
    assert len(context["explanation"]["top_contributing_features"]) == 3


def test_build_transaction_context_computes_confidence_from_probability():
    context = _sample_context()
    # confidence = |p - 0.5| * 2 -> |0.984 - 0.5| * 2 = 0.968
    assert context["prediction"]["confidence"] == 0.968


def test_render_context_as_text_includes_all_key_facts():
    context = _sample_context()
    text = render_context_as_text(context)

    assert "5821" in text
    assert "fraud" in text
    assert "0.9840" in text
    assert "critical" in text
    assert "xgboost_v3" in text
    assert "V14" in text
    assert "V12" in text
    assert "V4" in text
    assert "increases_fraud_probability" in text
    assert "decreases_fraud_probability" in text


def test_render_context_as_text_is_deterministic():
    context = _sample_context()
    assert render_context_as_text(context) == render_context_as_text(context)
