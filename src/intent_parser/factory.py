"""意图解析器工厂"""

import logging
from typing import Any

from src.intent_parser.base import IntentParserBase, ParseResult, IntentType
from src.intent_parser.parsers import QwenParser, OpenAIParser, LlamaParser, ClaudeParser
from src.intent_parser.cache import (
    get_intent_cache,
    set_intent_cache,
    should_cache_text,
    get_intent_cache_stats,
)

logger = logging.getLogger("hydraflow.intent_parser")


class IntentParserFactory:
    _parsers: dict[str, type[IntentParserBase]] = {}

    def __init__(self) -> None:
        self._register_defaults()
        self._enable_cache = True

    def _register_defaults(self) -> None:
        self._parsers["qwen2.5"] = QwenParser
        self._parsers["openai"] = OpenAIParser
        self._parsers["llama"] = LlamaParser
        self._parsers["claude"] = ClaudeParser

    def register(self, name: str, parser_class: type[IntentParserBase]) -> None:
        self._parsers[name] = parser_class

    def get_parser(self, name: str, config: dict[str, Any] | None = None) -> IntentParserBase:
        if name not in self._parsers:
            logger.warning(f"解析器 '{name}' 未注册，使用默认 qwen2.5")
            name = "qwen2.5"
        parser_class = self._parsers[name]
        return parser_class(name=name, config=config)

    def list_parsers(self) -> list[dict[str, Any]]:
        result = []
        for name, parser_class in self._parsers.items():
            parser = parser_class(name=name)
            result.append(parser.get_info())
        return result

    def parse(self, text: str, parser_name: str = "qwen2.5", use_cache: bool = True, **kwargs) -> ParseResult:
        if self._enable_cache and use_cache and should_cache_text(text):
            cached = get_intent_cache(text, parser_name)
            if cached:
                logger.debug(f"命中解析缓存: {text[:30]}...")
                cached["intent"] = IntentType(cached["intent"])
                return ParseResult(**cached)

        parser = self.get_parser(parser_name)
        result = parser.parse(text, **kwargs)

        if self._enable_cache and use_cache and should_cache_text(text):
            set_intent_cache(text, parser_name, {
                "intent": result.intent.value,
                "style": result.style,
                "prompt": result.prompt,
                "negative_prompt": result.negative_prompt,
                "parameters": result.parameters,
                "model_suggestions": result.model_suggestions,
                "confidence": result.confidence,
                "raw_text": result.raw_text,
                "metadata": result.metadata,
            })

        return result

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return get_intent_cache_stats()

    def enable_cache(self, enabled: bool = True) -> None:
        """启用/禁用缓存"""
        self._enable_cache = enabled
