"""API 模型解析器 - OpenAI 和 Claude"""

import logging
from typing import Any

from src.intent_parser.base import IntentParserBase, ParseResult, IntentType
from src.core.config import get_config
from src.core.exceptions import APIKeyError

logger = logging.getLogger("hydraflow.intent_parser.api")


class OpenAIParser(IntentParserBase):
    def __init__(self, name: str = "openai", config: dict[str, Any] | None = None):
        super().__init__(name, config)
        self._model_info = {
            "type": "api",
            "model": "gpt-4",
            "api_url": "https://api.openai.com/v1",
            "description": "OpenAI GPT 解析器",
        }

    def parse(self, text: str, **kwargs) -> ParseResult:
        intent = self._detect_intent(text)
        style = self._detect_style(text)
        negative_prompt = self._build_negative_prompt(intent, style)
        return ParseResult(
            intent=intent,
            style=style,
            prompt=text,
            negative_prompt=negative_prompt,
            parameters={},
            model_suggestions=self._suggest_models(intent),
            confidence=0.95,
            raw_text=text,
            metadata={"parser": self.name, "type": "api"},
        )

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["openai_dall_e"],
            IntentType.CODE_GENERATION: ["openai_gpt4"],
            IntentType.TEXT_GENERATION: ["openai_gpt4"],
            IntentType.GENERAL: ["openai_dall_e"],
        }
        return model_map.get(intent, ["openai_dall_e"])


class ClaudeParser(IntentParserBase):
    def __init__(self, name: str = "claude", config: dict[str, Any] | None = None):
        super().__init__(name, config)
        self._model_info = {
            "type": "api",
            "model": "claude-3-sonnet",
            "api_url": "https://api.anthropic.com/v1",
            "description": "Anthropic Claude 解析器",
        }

    def parse(self, text: str, **kwargs) -> ParseResult:
        intent = self._detect_intent(text)
        style = self._detect_style(text)
        negative_prompt = self._build_negative_prompt(intent, style)
        return ParseResult(
            intent=intent,
            style=style,
            prompt=text,
            negative_prompt=negative_prompt,
            parameters={},
            model_suggestions=self._suggest_models(intent),
            confidence=0.93,
            raw_text=text,
            metadata={"parser": self.name, "type": "api"},
        )

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["sdxl_1.0", "openai_dall_e"],
            IntentType.CODE_GENERATION: ["claude_3"],
            IntentType.TEXT_GENERATION: ["claude_3"],
            IntentType.GENERAL: ["sdxl_1.0"],
        }
        return model_map.get(intent, ["sdxl_1.0"])
