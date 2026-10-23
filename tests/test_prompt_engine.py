"""提示词引擎测试"""


def test_list_styles_not_empty(prompt_engine):
    styles = prompt_engine.list_styles()
    assert isinstance(styles, list)
    assert len(styles) > 0


def test_get_template_matches_style_name(prompt_engine):
    for style in prompt_engine.list_styles():
        template = prompt_engine.get_template(style)
        assert template is not None
        assert template["name"] == style


def test_unknown_style_returns_none(prompt_engine):
    assert prompt_engine.get_template("__not_exist_style__") is None


def test_enhance_prompt_without_style_keeps_text(prompt_engine):
    result = prompt_engine.enhance_prompt("一只猫")
    assert result["prompt"] == "一只猫"
    assert result["template_applied"] is False


def test_enhance_prompt_with_style_marks_template_applied(prompt_engine):
    style = prompt_engine.list_styles()[0]
    result = prompt_engine.enhance_prompt("一只猫", style)
    assert result["template_applied"] is True
    assert result["style"] == style


def test_build_prompt_merges_negative_prompt(prompt_engine):
    result = prompt_engine.build_prompt("一只猫", negative_prompt="blurry")
    assert result["negative_prompt"] == "blurry"


def test_build_prompt_without_negative_has_string(prompt_engine):
    result = prompt_engine.build_prompt("一只猫")
    assert isinstance(result["negative_prompt"], str)
