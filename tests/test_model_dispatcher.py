"""模型调度器测试"""

import pytest

from src.core.exceptions import ModelNotFoundError


def test_statistics_report_total_models(dispatcher):
    stats = dispatcher.get_statistics()
    assert stats["total_models"] > 0


def test_list_models_non_empty(dispatcher):
    models = dispatcher.list_models()
    assert len(models) > 0
    assert "id" in models[0]


def test_get_unknown_model_raises(dispatcher):
    with pytest.raises(ModelNotFoundError):
        dispatcher.get_model("__not_exist_model__")


def test_select_model_for_image_intent(dispatcher):
    model = dispatcher.select_model("image_generation")
    assert model["id"]


def test_list_models_filter_by_intent(dispatcher):
    models = dispatcher.list_models(by_intent="image_generation")
    assert isinstance(models, list)


def test_validate_models_returns_report(dispatcher):
    report = dispatcher.validate_models()
    assert isinstance(report, dict)
