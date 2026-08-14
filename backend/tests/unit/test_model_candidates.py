"""Unit tests for app.ml.pipeline.model_candidates."""

import pytest
from lightgbm import LGBMClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from app.ml.pipeline.model_candidates import MODEL_NAMES, build_model, default_search_space


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_build_model_returns_correct_type(name):
    model = build_model(name)
    expected_types = {
        "logistic_regression": LogisticRegression,
        "random_forest": RandomForestClassifier,
        "gradient_boosting": GradientBoostingClassifier,
        "xgboost": XGBClassifier,
        "lightgbm": LGBMClassifier,
    }
    assert isinstance(model, expected_types[name])


def test_build_model_unknown_name_raises():
    with pytest.raises(ValueError, match="Unknown model name"):
        build_model("not_a_real_model")


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_build_model_applies_custom_params(name):
    search_space = default_search_space(name)
    first_param = next(iter(search_space))
    kind, low, high = search_space[first_param]
    value = low if kind == "int" else float(low)

    model = build_model(name, {first_param: value})
    assert getattr(model, first_param) == value


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_default_search_space_has_valid_spec_shape(name):
    space = default_search_space(name)
    assert len(space) > 0
    for param, spec in space.items():
        assert spec[0] in {"int", "float", "float_log"}
        assert spec[1] < spec[2]
