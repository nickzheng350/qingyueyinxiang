"""本地模型解析器 - Qwen 和 Llama（支持真实本地 LLM 调用）"""

import json
import re
import logging
from typing import Any

import httpx

from src.intent_parser.base import IntentParserBase, ParseResult, IntentType
from src.intent_parser.parsers.api_parser import INTENT_SYSTEM_PROMPT, _parse_llm_response
from src.core.config import get_config
from src.core.stability import get_stability_manager, ErrorSeverity

logger = logging.getLogger("hydraflow.intent_parser.local")


class QwenParser(IntentParserBase):
    def __init__(self, name: str = "qwen2.5", config: dict[str, Any] | None = None):
        super().__init__(name, config)
        self._model_info = {
            "type": "local",
            "model": "qwen2.5-1.8b",
            "api_base": self.config.get("api_base", "http://localhost:1234/v1"),
            "description": "Qwen2.5 本地模型解析器",
        }

    def parse(self, text: str, **kwargs) -> ParseResult:
        should_use_llm, reason = self._should_use_llm(text)

        if not should_use_llm:
            result = self._keyword_based_parse(text)
            parameters = self._extract_parameters(text)
            result.parameters = parameters
            result.metadata["skip_llm_reason"] = reason
            return result

        llm_result = self._try_llm_parse(text)
        if llm_result is not None:
            llm_result.negative_prompt = self._build_negative_prompt(llm_result.intent, llm_result.style)
            llm_result.model_suggestions = self._suggest_models(llm_result.intent)
            parameters = self._extract_parameters(text)
            llm_result.parameters = parameters
            llm_result.metadata["llm_reason"] = reason
            return llm_result

        intent = self._detect_intent(text)
        style = self._detect_style(text)
        negative_prompt = self._build_negative_prompt(intent, style)
        parameters = self._extract_parameters(text)
        model_suggestions = self._suggest_models(intent)
        clean_prompt = self._clean_prompt(text, style)
        return ParseResult(
            intent=intent,
            style=style,
            prompt=clean_prompt,
            negative_prompt=negative_prompt,
            parameters=parameters,
            model_suggestions=model_suggestions,
            confidence=0.85,
            raw_text=text,
            metadata={"parser": self.name, "type": "local", "llm_parsed": False, "fallback": True},
        )

    def _try_llm_parse(self, text: str) -> ParseResult | None:
        api_base = self.config.get("api_base", "http://localhost:1234/v1")
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{api_base}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
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
                return _parse_llm_response(content, text, self.name, "local")
        except Exception as e:
            logger.debug(f"Qwen 本地 LLM 不可用，使用关键词解析: {e}")
            return None

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _extract_parameters(self, text: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        size_match = re.search(r"(\d+)\s*[x×]\s*(\d+)", text)
        if size_match:
            params["width"] = int(size_match.group(1))
            params["height"] = int(size_match.group(2))
        count_match = re.search(r"(\d+)\s*[张幅个]", text)
        if count_match:
            params["num_images"] = min(int(count_match.group(1)), 4)
        steps_match = re.search(r"步数\s*(\d+)", text)
        if steps_match:
            params["num_inference_steps"] = int(steps_match.group(1))
        return params

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["sdxl_1.0", "sd_1.5", "openai_dall_e"],
            IntentType.VIDEO_GENERATION: ["svd"],
            IntentType.AUDIO_GENERATION: ["tts"],
            IntentType.IMAGE_UPSCALE: ["esrgan"],
            IntentType.IMAGE_EDIT: ["sdxl_1.0", "sd_1.5"],
            IntentType.CODE_GENERATION: ["qwen2.5-coder-1.8b"],
            IntentType.TEXT_GENERATION: ["qwen2.5-1.8b"],
            IntentType.GENERAL: ["sdxl_1.0"],
        }
        return model_map.get(intent, ["sdxl_1.0"])

    def _clean_prompt(self, text: str, style: str) -> str:
        style_keywords = {
            "cyberpunk": ["赛博朋克", "cyberpunk", "霓虹", "neon"],
            "anime": ["动漫", "anime", "二次元"],
            "fantasy": ["奇幻", "fantasy", "魔法"],
            "photorealistic": ["真实", "写实", "照片级", "photorealistic"],
            "cinematic": ["电影", "cinematic"],
            "scifi": ["科幻", "sci-fi"],
            "steampunk": ["蒸汽朋克", "steampunk"],
        }
        cleaned = text
        if style in style_keywords:
            for kw in style_keywords[style]:
                cleaned = cleaned.replace(kw, "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned if cleaned else text


class LlamaParser(IntentParserBase):
    def __init__(self, name: str = "llama", config: dict[str, Any] | None = None):
        super().__init__(name, config)
        self._model_info = {
            "type": "local",
            "model": "llama3",
            "api_base": self.config.get("api_base", "http://localhost:11434/v1"),
            "description": "Llama 本地模型解析器",
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
        clean_prompt = self._clean_prompt(text, style)
        return ParseResult(
            intent=intent,
            style=style,
            prompt=clean_prompt,
            negative_prompt=negative_prompt,
            parameters={},
            model_suggestions=self._suggest_models(intent),
            confidence=0.80,
            raw_text=text,
            metadata={"parser": self.name, "type": "local", "llm_parsed": False, "fallback": True},
        )

    def _try_llm_parse(self, text: str) -> ParseResult | None:
        api_base = self.config.get("api_base", "http://localhost:11434/v1")
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{api_base}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
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
                return _parse_llm_response(content, text, self.name, "local")
        except Exception as e:
            logger.debug(f"Llama 本地 LLM 不可用，使用关键词解析: {e}")
            return None

    def _get_model_info(self) -> dict[str, Any]:
        return self._model_info

    def _suggest_models(self, intent: IntentType) -> list[str]:
        model_map = {
            IntentType.IMAGE_GENERATION: ["sdxl_1.0", "sd_1.5"],
            IntentType.VIDEO_GENERATION: ["svd"],
            IntentType.AUDIO_GENERATION: ["tts"],
            IntentType.IMAGE_UPSCALE: ["esrgan"],
            IntentType.IMAGE_EDIT: ["sdxl_1.0"],
            IntentType.CODE_GENERATION: ["qwen2.5-coder-1.8b"],
            IntentType.GENERAL: ["sdxl_1.0"],
        }
        return model_map.get(intent, ["sdxl_1.0"])

    def _clean_prompt(self, text: str, style: str) -> str:
        cleaned = text
        style_keywords = {
            "cyberpunk": ["赛博朋克", "cyberpunk"],
            "anime": ["动漫", "anime"],
            "fantasy": ["奇幻", "fantasy"],
            "photorealistic": ["真实", "写实", "照片级", "photorealistic"],
            "cinematic": ["电影", "cinematic"],
            "scifi": ["科幻", "sci-fi"],
            "steampunk": ["蒸汽朋克", "steampunk"],
        }
        if style in style_keywords:
            for kw in style_keywords[style]:
                cleaned = cleaned.replace(kw, "")
        return re.sub(r"\s+", " ", cleaned).strip() or text
