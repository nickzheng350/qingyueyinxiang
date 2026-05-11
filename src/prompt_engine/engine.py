"""提示词引擎 - 加载模板、优化提示词"""

import re
import logging
from pathlib import Path
from typing import Any

from src.core.config import get_config

logger = logging.getLogger("hydraflow.prompt_engine")


class PromptEngine:
    _instance: "PromptEngine | None" = None

    def __new__(cls) -> "PromptEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._templates: dict[str, dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        config = get_config()
        prompts_dir = config.project_root / "prompts" / "templates"
        if not prompts_dir.exists():
            logger.warning(f"提示词模板目录不存在: {prompts_dir}")
            return
        for template_file in prompts_dir.glob("*.md"):
            style_name = template_file.stem
            try:
                content = template_file.read_text(encoding="utf-8")
                template_data = self._parse_template(content, style_name)
                self._templates[style_name] = template_data
                logger.debug(f"加载模板: {style_name}")
            except Exception as e:
                logger.error(f"加载模板失败 {template_file}: {e}")

    def _parse_template(self, content: str, style_name: str) -> dict[str, Any]:
        template: dict[str, Any] = {
            "name": style_name,
            "keywords": [],
            "color_palette": [],
            "lighting_style": "",
            "base_prompt": "",
            "enhanced_prompt": "",
            "negative_prompt": "",
        }
        json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if json_match:
            import json
            try:
                json_data = json.loads(json_match.group(1))
                template["keywords"] = json_data.get("keywords", [])
                template["color_palette"] = json_data.get("color_palette", [])
                template["lighting_style"] = json_data.get("lighting_style", "")
            except json.JSONDecodeError:
                pass
        sections = re.split(r"---", content)
        for section in sections:
            if "**基础版**" in section or "基础版" in section:
                code_blocks = re.findall(r"```\s*(.*?)\s*```", section, re.DOTALL)
                if code_blocks:
                    template["base_prompt"] = code_blocks[0].strip()
            if "**增强版**" in section or "增强版" in section:
                code_blocks = re.findall(r"```\s*(.*?)\s*```", section, re.DOTALL)
                if code_blocks:
                    template["enhanced_prompt"] = code_blocks[0].strip()
        neg_section_match = re.search(r"负面提示词.*?\n(.*?)(?:\n---|\n#|\Z)", content, re.DOTALL)
        if neg_section_match:
            neg_blocks = re.findall(r"```\s*(.*?)\s*```", neg_section_match.group(1), re.DOTALL)
            if neg_blocks:
                template["negative_prompt"] = neg_blocks[0].strip()
        return template

    def get_template(self, style: str) -> dict[str, Any] | None:
        return self._templates.get(style)

    def list_styles(self) -> list[str]:
        return list(self._templates.keys())

    def enhance_prompt(self, text: str, style: str = "", enhanced: bool = True) -> dict[str, Any]:
        template = self._templates.get(style, {}) if style else {}
        base = template.get("enhanced_prompt" if enhanced else "base_prompt", "")
        negative = template.get("negative_prompt", "")
        keywords = template.get("keywords", [])
        if base:
            final_prompt = f"{text}, {base}"
        else:
            final_prompt = text
        if keywords:
            keyword_str = ", ".join(keywords[:3])
            final_prompt = f"{text}, {keyword_str}"
        return {
            "prompt": final_prompt,
            "negative_prompt": negative,
            "style": style,
            "template_applied": bool(template),
            "keywords": keywords,
        }

    def build_prompt(
        self,
        text: str,
        style: str = "",
        negative_prompt: str = "",
        enhanced: bool = True,
    ) -> dict[str, Any]:
        result = self.enhance_prompt(text, style, enhanced)
        if negative_prompt:
            result["negative_prompt"] = (
                f"{negative_prompt}, {result['negative_prompt']}"
                if result["negative_prompt"]
                else negative_prompt
            )
        return result
