"""意图解析模块测试"""

from src.intent_parser.base import IntentType


def test_list_parsers_contains_defaults(parser_factory):
    names = {p["name"] for p in parser_factory.list_parsers()}
    assert {"qwen2.5", "openai", "llama", "claude"}.issubset(names)


def test_parse_image_generation(parser_factory):
    result = parser_factory.parse("生成一张猫的图片")
    assert result.intent == IntentType.IMAGE_GENERATION
    assert result.confidence > 0
    assert result.raw_text == "生成一张猫的图片"


def test_parse_detects_cyberpunk_style(parser_factory):
    result = parser_factory.parse("生成赛博朋克风格的图片")
    assert result.intent == IntentType.IMAGE_GENERATION
    assert result.style == "cyberpunk"


def test_parse_video_generation(parser_factory):
    result = parser_factory.parse("生成一段视频")
    assert result.intent == IntentType.VIDEO_GENERATION


def test_parse_result_has_negative_prompt_for_image(parser_factory):
    result = parser_factory.parse("画一张风景图")
    assert isinstance(result.negative_prompt, str)


def test_unknown_parser_falls_back_to_default(parser_factory):
    parser = parser_factory.get_parser("__not_registered__")
    assert parser.name == "qwen2.5"


def test_repeated_parse_is_stable(parser_factory):
    text = "生成一只狗的图片"
    first = parser_factory.parse(text)
    second = parser_factory.parse(text)
    assert first.intent == second.intent
    assert first.style == second.style


def test_cache_stats_exposed(parser_factory):
    parser_factory.parse("生成一张图片")
    stats = parser_factory.get_cache_stats()
    assert isinstance(stats, dict)
