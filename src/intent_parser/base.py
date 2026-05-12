"""意图解析器基类与数据模型"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import re

ENABLE_LLM_BY_DEFAULT = True

COMPLEXITY_THRESHOLD_HIGH = 0.7
COMPLEXITY_THRESHOLD_MEDIUM = 0.4

SIMPLE_QUERY_PATTERNS = [
    r"^生成[一二三四五六七八九十\d]?[张幅个]?(图片|图画|图像|照片|画)$",
    r"^画[一二三四五六七八九十\d]?[张幅个]?(图|画|像)$",
    r"^创?作?[一二三四五六七八九十\d]?[张幅个]?(图|画|像|作品)$",
    r"^(制作|创建|生成)\s*一张?\s*(图|画|照片)$",
    r"^做个?\s*(图|画|头像|壁纸)$",
    r"^(头像|壁纸|背景)$",
    r"^看\s*(看|一下)?\s*(这|那个)?\s*(图|画|东西)$",
    r"^给我\s*(看|画|生成)\s*(个|张)$",
    r"^(cat|dog|猫|狗|花|树|山|水|天空)$",
    r"^[a-z]+\s+(cat|dog)$",
]

STYLE_ONLY_QUERY_PATTERNS = [
    r"^(赛博朋克|动漫|奇幻|写实|电影|科幻|蒸汽朋克)风格?的?(.*)$",
    r"^(cyberpunk|anime|fantasy|realistic|cinematic|scifi|steampunk)\s+(.*)$",
    r"^(.*)\s+(风格|style)$",
]

def analyze_query_complexity(text: str) -> tuple[float, str, list[str]]:
    """分析查询复杂度，返回 (复杂度分数, 复杂度级别, 触发关键词列表)"""
    text_lower = text.lower()
    triggers: list[str] = []
    score = 0.0

    if len(text) < 10:
        score += 0.3
        triggers.append("short_text")

    for pattern in SIMPLE_QUERY_PATTERNS:
        if re.search(pattern, text_lower):
            score -= 0.3
            triggers.append("simple_pattern_match")

    for pattern in STYLE_ONLY_QUERY_PATTERNS:
        if re.search(pattern, text_lower):
            score -= 0.2
            triggers.append("style_only_pattern")

    multi_intent_markers = ["但是", "而且", "并且", "还有", "另外", "同时", "and", "but", "also"]
    if any(marker in text_lower for marker in multi_intent_markers):
        score += 0.3
        triggers.append("multi_intent")

    technical_terms = ["参数", "设置", "配置", "option", "setting", "config", "param"]
    if any(term in text_lower for term in technical_terms):
        score += 0.2
        triggers.append("technical_query")

    ambiguous_terms = ["这个", "那个", "它", "这个怎么样", "类似", "差不多的", "something like", "similar"]
    if any(term in text_lower for term in ambiguous_terms):
        score += 0.2
        triggers.append("ambiguous_reference")

    length_bonus = min(len(text) / 100, 0.3)
    score += length_bonus
    if length_bonus > 0.1:
        triggers.append(f"length_{len(text)}")

    conditional_markers = ["如果", "要是", "假如", "万一", "if", "unless", "when"]
    if any(marker in text_lower for marker in conditional_markers):
        score += 0.15
        triggers.append("conditional")

    comparative_markers = ["更", "最", "比较", "better", "best", "more", "less"]
    if any(marker in text_lower for marker in comparative_markers):
        score += 0.1
        triggers.append("comparative")

    score = max(0.0, min(1.0, score))

    if score >= COMPLEXITY_THRESHOLD_HIGH:
        level = "high"
    elif score >= COMPLEXITY_THRESHOLD_MEDIUM:
        level = "medium"
    else:
        level = "simple"

    return score, level, triggers


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


def _levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def _fuzzy_match(text: str, keyword: str, threshold: float = 0.7) -> bool:
    if keyword in text:
        return True
    text_lower = text.lower()
    kw_lower = keyword.lower()
    n_kw = len(kw_lower)
    if n_kw < 2:
        return False
    n_text = len(text_lower)
    for i in range(n_text - n_kw + 1):
        segment = text_lower[i:i + n_kw]
        dist = _levenshtein_distance(segment, kw_lower)
        max_len = max(len(segment), n_kw)
        similarity = 1.0 - dist / max_len if max_len > 0 else 0.0
        if similarity >= threshold:
            return True
    return False


class IntentParserBase(ABC):
    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self._use_llm = self.config.get("use_llm", ENABLE_LLM_BY_DEFAULT)
        self._llm_threshold = self.config.get("llm_threshold", "medium")

    @abstractmethod
    def parse(self, text: str, **kwargs) -> ParseResult:
        pass

    @abstractmethod
    def _get_model_info(self) -> dict[str, Any]:
        pass

    def _should_use_llm(self, text: str) -> tuple[bool, str]:
        """判断是否应该使用LLM进行解析"""
        if not self._use_llm:
            return False, "llm_disabled"

        complexity, level, triggers = analyze_query_complexity(text)

        threshold_map = {
            "high": COMPLEXITY_THRESHOLD_HIGH,
            "medium": COMPLEXITY_THRESHOLD_MEDIUM,
            "simple": -1.0,
        }
        threshold = threshold_map.get(self._llm_threshold, COMPLEXITY_THRESHOLD_MEDIUM)

        if level == "simple" or complexity < threshold:
            return False, f"low_complexity_{level}"

        return True, f"high_complexity_{level}"

    def _keyword_based_parse(self, text: str) -> ParseResult:
        """基于关键词的解析方法（无需LLM）"""
        intent = self._detect_intent(text)
        style = self._detect_style(text)
        negative_prompt = self._build_negative_prompt(intent, style)
        clean_prompt = self._clean_prompt(text, style)
        model_suggestions = self._suggest_models(intent)

        confidence = 0.95 if intent != IntentType.GENERAL else 0.6

        return ParseResult(
            intent=intent,
            style=style,
            prompt=clean_prompt,
            negative_prompt=negative_prompt,
            parameters={},
            model_suggestions=model_suggestions,
            confidence=confidence,
            raw_text=text,
            metadata={
                "parser": self.name,
                "type": "keyword",
                "llm_parsed": False,
                "parsing_method": "keyword_only"
            },
        )

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

        return self._fuzzy_detect_intent(text_lower)

    def _fuzzy_detect_intent(self, text: str) -> IntentType:
        fuzzy_map = {
            IntentType.IMAGE_GENERATION: [
                "图", "画", "绘", "照", "像", "pic", "img", "art",
            ],
            IntentType.VIDEO_GENERATION: [
                "视", "动", "影", "vid", "mov",
            ],
            IntentType.AUDIO_GENERATION: [
                "音", "乐", "声", "歌", "aud", "mus",
            ],
            IntentType.CODE_GENERATION: [
                "码", "程", "编", "函", "cod", "dev",
            ],
            IntentType.IMAGE_UPSCALE: [
                "清", "晰", "大", "hd", "4k", "8k",
            ],
        }
        best_intent = IntentType.GENERAL
        best_score = 0.0
        for intent, keywords in fuzzy_map.items():
            for kw in keywords:
                if _fuzzy_match(text, kw, threshold=0.75):
                    score = 1.0 - _levenshtein_distance(text[:len(kw)], kw) / max(len(kw), 1)
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        if best_score > 0.5:
            return best_intent

        return self._context_detect_intent(text)

    def _context_detect_intent(self, text: str) -> IntentType:
        image_context = [
            "风景", "人物", "动物", "建筑", "猫", "狗", "花", "树",
            "天空", "海洋", "山", "城市", "少女", "男孩", "龙",
            "landscape", "portrait", "animal", "cat", "dog", "city",
        ]
        for kw in image_context:
            if _fuzzy_match(text, kw, threshold=0.8):
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

        for style, keywords in style_map.items():
            for kw in keywords:
                if _fuzzy_match(text_lower, kw, threshold=0.75):
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
