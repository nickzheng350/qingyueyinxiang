"""意图解析器基类与数据模型"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(Enum):
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    TEXT_GENERATION = "text_generation"
    IMAGE_EDIT = "image_edit"
    IMAGE_UPSCALE = "image_upscale"
    CODE_GENERATION = "code_generation"
    GENERAL = "general"


@dataclass
class ParseResult:
    intent: IntentType = IntentType.GENERAL
    style: str = ""
    prompt: str = ""
    negative_prompt: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    model_suggestions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class IntentParserBase(ABC):
    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    def parse(self, text: str, **kwargs) -> ParseResult:
        pass

    @abstractmethod
    def _get_model_info(self) -> dict[str, Any]:
        pass

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "model_info": self._get_model_info(),
            "config": self.config,
        }

    def _detect_intent(self, text: str) -> IntentType:
        text_lower = text.lower()
        video_keywords = [
            "视频", "动画", "影片", "录影",
            "video", "animation", "movie", "clip", "motion",
        ]
        audio_keywords = [
            "音频", "音乐", "语音", "声音", "配音",
            "audio", "music", "sound", "voice", "speech", "tts",
        ]
        code_keywords = [
            "代码", "编程", "函数", "程序", "算法", "写一个", "实现",
            "code", "program", "function", "script", "implement", "algorithm",
        ]
        upscale_keywords = [
            "超分", "放大", "高清", "增强",
            "upscale", "enhance", "hd", "high resolution",
        ]
        edit_keywords = [
            "编辑", "修改", "调整", "裁剪",
            "edit", "modify", "adjust", "crop", "filter",
        ]
        image_specific_keywords = [
            "图片", "图像", "画", "绘制", "生成图", "插画", "照片",
            "image", "picture", "photo", "draw", "paint", "illustration",
            "portrait", "landscape", "artwork",
        ]
        image_general_keywords = [
            "创建", "生成", "制作", "设计", "渲染",
            "create", "generate", "render",
        ]
        if any(kw in text_lower for kw in video_keywords):
            return IntentType.VIDEO_GENERATION
        if any(kw in text_lower for kw in audio_keywords):
            return IntentType.AUDIO_GENERATION
        if any(kw in text_lower for kw in code_keywords):
            return IntentType.CODE_GENERATION
        if any(kw in text_lower for kw in upscale_keywords):
            return IntentType.IMAGE_UPSCALE
        if any(kw in text_lower for kw in edit_keywords):
            return IntentType.IMAGE_EDIT
        if any(kw in text_lower for kw in image_specific_keywords):
            return IntentType.IMAGE_GENERATION
        if any(kw in text_lower for kw in image_general_keywords):
            return IntentType.IMAGE_GENERATION
        return IntentType.GENERAL

    def _detect_style(self, text: str) -> str:
        text_lower = text.lower()
        style_map = {
            "cyberpunk": ["赛博朋克", "cyberpunk", "霓虹", "neon", "未来"],
            "anime": ["动漫", "anime", "manga", "二次元", "日系"],
            "fantasy": ["奇幻", "fantasy", "魔法", "magic", "精灵"],
            "photorealistic": ["真实", "写实", "照片级", "photorealistic", "realistic", "photo"],
            "cinematic": ["电影", "cinematic", "镜头", "dramatic"],
            "scifi": ["科幻", "sci-fi", "scifi", "太空", "space", "宇宙"],
            "steampunk": ["蒸汽朋克", "steampunk", "蒸汽", "维多利亚"],
        }
        for style, keywords in style_map.items():
            if any(kw in text_lower for kw in keywords):
                return style
        return ""

    def _build_negative_prompt(self, intent: IntentType, style: str) -> str:
        base = "blurry, low quality, distorted, deformed, extra limbs, bad anatomy, text, watermark"
        style_negatives = {
            "anime": "realistic, photorealistic, poor line art",
            "cyberpunk": "flat colors, poor contrast, low resolution",
            "photorealistic": "cartoon, anime, drawing, painting, illustration",
            "cinematic": "amateur, low budget, poor lighting",
        }
        if style in style_negatives:
            base += f", {style_negatives[style]}"
        return base
