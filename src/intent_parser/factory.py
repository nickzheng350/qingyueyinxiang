"""意图解析器工厂"""

import logging
from typing import Any

from src.intent_parser.base import IntentParserBase, ParseResult, IntentType
from src.intent_parser.parsers import QwenParser, OpenAIParser, LlamaParser, ClaudeParser

logger = logging.getLogger("hydraflow.intent_parser")


class IntentParserFactory:
    _parsers: dict[str, type[IntentParserBase]] = {}

    def __init__(self) -> None:
        self._register_defaults()

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

    def parse(self, text: str, parser_name: str = "qwen2.5", **kwargs) -> ParseResult:
        parser = self.get_parser(parser_name)
        return parser.parse(text, **kwargs)
