"""API 模型解析器 - OpenAI 和 Claude（支持真实 LLM 调用）"""

import json
import logging
from typing import Any, Optional

import httpx

from src.intent_parser.base import IntentParserBase, ParseResult, IntentType
from src.core.config import get_config
from src.core.stability import get_stability_manager, ErrorSeverity

logger = logging.getLogger("hydraflow.intent_parser.api")

INTENT_SYSTEM_PROMPT = """你是一个意图解析器。分析用户输入，返回 JSON 格式的意图分析结果。

支持的意图类型:
- image_generation: 图片/图像生成
- video_generation: 视频生成
- audio_generation: 音频/音乐/语音生成
- text_generation: 文本生成
- image_edit: 图片编辑/修改
- image_upscale: 图片超分/放大/增强分辨率
- code_generation: 代码/编程/算法
- general: 无法判断的通用意图

支持的风格:
- cyberpunk: 赛博朋克
- anime: 动漫
- fantasy: 奇幻
- photorealistic: 照片级真实感
- cinematic: 电影感
- scifi: 科幻
- steampunk: 蒸汽朋克
- (空字符串): 无特定风格

请严格返回如下 JSON:
{
  "intent": "意图类型",
  "style": "风格或空字符串",
  "prompt": "清理后的核心提示词(去除风格词和意图词)",
  "confidence": 0.0到1.0的置信度
}

只返回 JSON，不要其他文字。"""


def _parse_llm_response(text: str, raw_text: str, parser_name: str, parser_type: str) -> Optional[ParseResult]:
    """解析LLM响应"""
    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"LLM 返回非 JSON ({parser_name}/{parser_type})，回退关键词解析: {text[:100]}")
        logger.debug(f"JSON解析错误详情: {e}")
        return None

    intent_str = data.get("intent", "general")
    intent_map = {e.value: e for e in IntentType}
    intent = intent_map.get(intent_str, IntentType.GENERAL)

    return ParseResult(
        intent=intent,
        style=data.get("style", ""),
        prompt=data.get("prompt", raw_text),
        negative_prompt="",
        parameters={},
        model_suggestions=[],
        confidence=float(data.get("confidence", 0.5)),
        raw_text=raw_text,
        metadata={"parser": parser_name, "type": parser_type, "llm_parsed": True},
    )


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
        should_use_llm, reason = self._should_use_llm(text)

        if not should_use_llm:
            result = self._keyword_based_parse(text)
            result.metadata["skip_llm_reason"] = reason
            return result

        llm_result = self._try_llm_parse(text)
        if llm_result is not None:
            llm_result.negative_prompt = self._build_negative_prompt(llm_result.intent, llm_result.style)
            llm_result.model_suggestions = self._suggest_models(llm_result.intent)
            llm_result.metadata["llm_reason"] = reason
            return llm_result

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
            confidence=0.85,
            raw_text=text,
            metadata={"parser": self.name, "type": "api", "llm_parsed": False, "fallback": True},
        )

    def _try_llm_parse(self, text: str) -> ParseResult | None:
        config = get_config()
        api_key = config.get_api_key("openai")
        if not api_key:
            return None

        api_url = self.config.get("api_url", "https://api.openai.com/v1")
        model = self.config.get("model", "gpt-4")

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{api_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                            {"role": "user", "content": text},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 200,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                return _parse_llm_response(content, text, self.name, "api")
        except Exception as e:
            logger.warning(f"OpenAI LLM 调用失败，回退关键词解析: {e}")
            get_stability_manager().record_error(e, ErrorSeverity.MEDIUM, "openai_parser")
            return None

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["openai_dall_e", "sdxl_1.0"],
            IntentType.CODE_GENERATION: ["openai_gpt4"],
            IntentType.TEXT_GENERATION: ["openai_gpt4"],
            IntentType.VIDEO_GENERATION: ["svd"],
            IntentType.AUDIO_GENERATION: ["tts"],
            IntentType.IMAGE_UPSCALE: ["esrgan"],
            IntentType.IMAGE_EDIT: ["openai_dall_e", "sdxl_1.0"],
            IntentType.GENERAL: ["openai_dall_e", "sdxl_1.0"],
        }
        return model_map.get(intent, ["sdxl_1.0"])


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
        should_use_llm, reason = self._should_use_llm(text)

        if not should_use_llm:
            result = self._keyword_based_parse(text)
            result.metadata["skip_llm_reason"] = reason
            return result

        llm_result = self._try_llm_parse(text)
        if llm_result is not None:
            llm_result.negative_prompt = self._build_negative_prompt(llm_result.intent, llm_result.style)
            llm_result.model_suggestions = self._suggest_models(llm_result.intent)
            llm_result.metadata["llm_reason"] = reason
            return llm_result

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
            confidence=0.85,
            raw_text=text,
            metadata={"parser": self.name, "type": "api", "llm_parsed": False, "fallback": True},
        )

    def _try_llm_parse(self, text: str) -> ParseResult | None:
        config = get_config()
        api_key = config.get_api_key("anthropic")
        if not api_key:
            return None

        api_url = self.config.get("api_url", "https://api.anthropic.com/v1")
        model = self.config.get("model", "claude-3-sonnet-20240229")

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{api_url}/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": 200,
                        "messages": [{"role": "user", "content": f"{INTENT_SYSTEM_PROMPT}\n\n用户输入: {text}"}],
                    },
                )
                resp.raise_for_status()
                content = resp.json()["content"][0]["text"]
                return _parse_llm_response(content, text, self.name, "api")
        except Exception as e:
            logger.warning(f"Claude LLM 调用失败，回退关键词解析: {e}")
            get_stability_manager().record_error(e, ErrorSeverity.MEDIUM, "claude_parser")
            return None

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["sdxl_1.0", "openai_dall_e"],
            IntentType.CODE_GENERATION: ["claude_3"],
            IntentType.TEXT_GENERATION: ["claude_3"],
            IntentType.VIDEO_GENERATION: ["svd"],
            IntentType.AUDIO_GENERATION: ["tts"],
            IntentType.IMAGE_UPSCALE: ["esrgan"],
            IntentType.IMAGE_EDIT: ["sdxl_1.0"],
            IntentType.GENERAL: ["sdxl_1.0"],
        }
        return model_map.get(intent, ["sdxl_1.0"])
