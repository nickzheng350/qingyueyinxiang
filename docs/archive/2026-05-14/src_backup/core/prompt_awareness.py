"""提示词敏锐性引擎 - 提示词感知、分析、增强"""
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from collections import defaultdict

from src.model_dispatcher.type_system import ModelFunctionType
from src.core.prompt_engine import RichPrompt, PromptRole

logger = logging.getLogger("hydraflow.core.prompt_awareness")


class PromptIntent(str, Enum):
    """提示词意图类型"""
    CREATIVE = "creative"  # 创意生成
    TECHNICAL = "technical"  # 技术需求
    FINE_TUNING = "fine_tuning"  # 微调需求
    STYLE_ADAPTATION = "style_adaptation"  # 风格适配
    QUALITY_ENHANCEMENT = "quality_enhancement"  # 质量提升
    BATCH_PROCESSING = "batch_processing"  # 批量处理
    EXPERIMENTATION = "experimentation"  # 实验探索
    MASTERPIECE = "masterpiece"  # 杰作需求


class ContentCategory(str, Enum):
    """内容类别"""
    ART = "art"
    PHOTOGRAPHY = "photography"
    ARCHITECTURE = "architecture"
    NATURE = "nature"
    PORTRAIT = "portrait"
    ABSTRACT = "abstract"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"


class KeywordPriority(str, Enum):
    """关键词优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KeywordAnalysis:
    """关键词分析结果"""
    keyword: str
    category: Optional[str]
    priority: KeywordPriority
    frequency: int
    position_score: float
    context: str
    synonyms: List[str] = field(default_factory=list)


@dataclass
class IntentDetection:
    """意图检测结果"""
    primary_intent: PromptIntent
    secondary_intents: List[PromptIntent] = field(default_factory=list)
    confidence_scores: Dict[PromptIntent, float] = field(default_factory=dict)
    intent_triggers: Dict[PromptIntent, List[str]] = field(default_factory=dict)


@dataclass
class QualityAssessment:
    """质量评估"""
    clarity_score: float
    specificity_score: float
    structure_score: float
    overall_quality: float
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class EnhancementSuggestion:
    """增强建议"""
    suggestion_id: str
    type: str
    original: str
    enhanced: str
    expected_improvement: float
    description: str
    applied: bool = False


@dataclass
class PromptProfile:
    """提示词画像"""
    profile_id: str
    content_category: ContentCategory
    complexity_level: str
    creativity_level: str
    detail_level: str
    emotional_tone: Optional[str]
    target_audience: Optional[str]
    technical_requirements: List[str] = field(default_factory=list)
    style_references: List[str] = field(default_factory=list)


@dataclass
class AwarenessResult:
    """敏锐性分析完整结果"""
    analysis_id: str
    original_prompt: RichPrompt
    keyword_analysis: List[KeywordAnalysis]
    intent_detection: IntentDetection
    quality_assessment: QualityAssessment
    prompt_profile: PromptProfile
    enhancement_suggestions: List[EnhancementSuggestion]
    recommended_engines: List[ModelFunctionType]
    runtime_parameters: Dict[str, Any] = field(default_factory=dict)
    context_metadata: Dict[str, Any] = field(default_factory=dict)


class PromptAnalyzer:
    """提示词分析器"""
    
    def __init__(self):
        self.quality_thresholds = {
            "excellent": 0.8,
            "good": 0.6,
            "average": 0.4,
            "poor": 0.2,
        }
        
        self.intent_keywords = {
            PromptIntent.CREATIVE: [
                "imagine", "create", "invent", "fantasy", "surreal", "dream",
                "artistic", "creative", "imagination", "inspiration"
            ],
            PromptIntent.TECHNICAL: [
                "technical", "precise", "accurate", "detailed", "specification",
                "professional", "standard", "quality", "high res", "8k", "4k"
            ],
            PromptIntent.STYLE_ADAPTATION: [
                "style", "like", "in the style of", "art style", "artwork",
                "painting", "drawing", "illustration", "rendering"
            ],
            PromptIntent.QUALITY_ENHANCEMENT: [
                "quality", "best", "masterpiece", "excellent", "superb",
                "perfect", "amazing", "stunning", "high quality", "detailed"
            ],
            PromptIntent.MASTERPIECE: [
                "masterpiece", "best quality", "ultra detailed", "award winning",
                "professional", "exquisite", "perfect"
            ],
            PromptIntent.EXPERIMENTATION: [
                "experiment", "try", "explore", "different", "various", "variations",
                "test", "attempt"
            ],
        }
        
        self.creative_keywords = {
            "art", "painting", "illustration", "drawing", "sculpture",
            "creative", "artistic", "imagination", "fantasy", "surreal"
        }
        
        self.quality_keywords = {
            "quality", "best", "masterpiece", "excellent", "superb",
            "perfect", "amazing", "stunning", "detailed", "high quality"
        }
        
        self.technical_keywords = {
            "8k", "4k", "high res", "resolution", "render", "cgi", "3d",
            "photorealistic", "realistic", "detailed", "professional"
        }
        
        self.style_indicators = {
            "in the style of", "like", "similar to", "inspired by",
            "art by", "painting by", "style of"
        }
    
    def analyze_keywords(
        self, 
        prompt: RichPrompt
    ) -> List[KeywordAnalysis]:
        """分析关键词"""
        primary_content = prompt.get_primary_content() or ""
        all_text = primary_content
        
        for elem in prompt.elements:
            if elem.content and isinstance(elem.content, str):
                all_text += " " + elem.content
        
        keywords = self._extract_keywords(all_text)
        keyword_analyses = []
        
        for keyword in keywords:
            analysis = self._analyze_single_keyword(
                keyword, all_text, keywords
            )
            keyword_analyses.append(analysis)
        
        keyword_analyses.sort(key=lambda k: (
            self._priority_order(k.priority), 
            -k.frequency
        ))
        
        return keyword_analyses
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do",
            "does", "did", "will", "would", "could", "should", "may",
            "might", "must", "shall", "can"
        }
        
        keywords = [
            word for word in words 
            if word not in stopwords and len(word) > 2
        ]
        
        return keywords
    
    def _analyze_single_keyword(
        self, 
        keyword: str, 
        text: str, 
        all_keywords: List[str]
    ) -> KeywordAnalysis:
        """分析单个关键词"""
        frequency = all_keywords.count(keyword)
        
        position = text.lower().find(keyword)
        position_score = max(0.0, 1.0 - position / len(text)) if len(text) > 0 else 0.5
        
        priority = KeywordPriority.MEDIUM
        if keyword in self.quality_keywords:
            priority = KeywordPriority.CRITICAL
        elif keyword in self.technical_keywords:
            priority = KeywordPriority.HIGH
        elif keyword in self.creative_keywords:
            priority = KeywordPriority.HIGH
        
        start_idx = max(0, text.lower().find(keyword) - 50)
        end_idx = min(len(text), text.lower().find(keyword) + len(keyword) + 50)
        context = text[start_idx:end_idx]
        
        return KeywordAnalysis(
            keyword=keyword,
            category=None,
            priority=priority,
            frequency=frequency,
            position_score=position_score,
            context=context,
            synonyms=[]
        )
    
    def _priority_order(self, priority: KeywordPriority) -> int:
        """优先级排序"""
        return {
            KeywordPriority.CRITICAL: 0,
            KeywordPriority.HIGH: 1,
            KeywordPriority.MEDIUM: 2,
            KeywordPriority.LOW: 3,
        }.get(priority, 99)
    
    def detect_intent(self, prompt: RichPrompt) -> IntentDetection:
        """检测意图"""
        primary_content = prompt.get_primary_content() or ""
        text = primary_content.lower()
        
        confidence_scores: Dict[PromptIntent, float] = {}
        intent_triggers: Dict[PromptIntent, List[str]] = defaultdict(list)
        
        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            triggers = []
            
            for keyword in keywords:
                if keyword in text:
                    score += 1.0
                    triggers.append(keyword)
            
            if score > 0:
                confidence_scores[intent] = min(score / len(keywords) * 2, 1.0)
                intent_triggers[intent] = triggers
        
        if confidence_scores:
            sorted_intents = sorted(
                confidence_scores.items(),
                key=lambda x: -x[1]
            )
            primary_intent = sorted_intents[0][0]
            secondary_intents = [
                intent for intent, score in sorted_intents[1:3]
                if score > 0.3
            ]
        else:
            primary_intent = PromptIntent.CREATIVE
            secondary_intents = []
        
        return IntentDetection(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence_scores=confidence_scores,
            intent_triggers=intent_triggers,
        )
    
    def assess_quality(self, prompt: RichPrompt) -> QualityAssessment:
        """质量评估"""
        primary_content = prompt.get_primary_content() or ""
        text = primary_content
        
        clarity_score = self._assess_clarity(text)
        specificity_score = self._assess_specificity(text)
        structure_score = self._assess_structure(prompt)
        
        overall_quality = (
            clarity_score * 0.35 +
            specificity_score * 0.35 +
            structure_score * 0.3
        )
        
        suggestions = self._generate_suggestions(
            clarity_score, specificity_score, structure_score
        )
        
        strengths = self._identify_strengths(
            clarity_score, specificity_score, structure_score
        )
        
        weaknesses = self._identify_weaknesses(
            clarity_score, specificity_score, structure_score
        )
        
        return QualityAssessment(
            clarity_score=clarity_score,
            specificity_score=specificity_score,
            structure_score=structure_score,
            overall_quality=overall_quality,
            suggestions=suggestions,
            strengths=strengths,
            weaknesses=weaknesses,
        )
    
    def _assess_clarity(self, text: str) -> float:
        """评估清晰度"""
        word_count = len(text.split())
        
        if word_count < 10:
            return 0.4
        elif word_count < 30:
            return 0.6
        elif word_count < 100:
            return 0.8
        else:
            return 0.7
    
    def _assess_specificity(self, text: str) -> float:
        """评估具体性"""
        specific_indicators = [
            "8k", "4k", "high res", "detailed", "photorealistic",
            "professional", "perfect", "masterpiece", "style of",
            "in the style of", "rendering", "illustration"
        ]
        
        text_lower = text.lower()
        specific_count = sum(
            1 for indicator in specific_indicators
            if indicator in text_lower
        )
        
        if specific_count >= 3:
            return 0.9
        elif specific_count >= 1:
            return 0.7
        else:
            return 0.4
    
    def _assess_structure(self, prompt: RichPrompt) -> float:
        """评估结构"""
        score = 0.5
        
        has_primary = any(
            elem.role == PromptRole.PRIMARY for elem in prompt.elements
        )
        if has_primary:
            score += 0.2
        
        has_style = any(
            elem.role == PromptRole.STYLE for elem in prompt.elements
        )
        if has_style:
            score += 0.15
        
        has_negative = any(
            elem.role == PromptRole.NEGATIVE for elem in prompt.elements
        )
        if has_negative:
            score += 0.15
        
        return min(score, 1.0)
    
    def _generate_suggestions(
        self,
        clarity_score: float,
        specificity_score: float,
        structure_score: float
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if clarity_score < 0.5:
            suggestions.append("增加提示词的描述性内容")
        
        if specificity_score < 0.6:
            suggestions.append("添加更多具体的风格和质量关键词")
        
        if structure_score < 0.7:
            suggestions.append("考虑添加负面提示词来排除不需要的元素")
        
        return suggestions
    
    def _identify_strengths(
        self,
        clarity_score: float,
        specificity_score: float,
        structure_score: float
    ) -> List[str]:
        """识别优点"""
        strengths = []
        
        if clarity_score >= 0.7:
            strengths.append("提示词描述清晰")
        
        if specificity_score >= 0.7:
            strengths.append("包含丰富的具体细节")
        
        if structure_score >= 0.8:
            strengths.append("结构完善，包含风格和负面提示")
        
        return strengths
    
    def _identify_weaknesses(
        self,
        clarity_score: float,
        specificity_score: float,
        structure_score: float
    ) -> List[str]:
        """识别缺点"""
        weaknesses = []
        
        if clarity_score < 0.5:
            weaknesses.append("提示词过于简短")
        
        if specificity_score < 0.6:
            weaknesses.append("缺乏具体的风格和质量要求")
        
        if structure_score < 0.6:
            weaknesses.append("结构需要完善")
        
        return weaknesses
    
    def build_profile(self, prompt: RichPrompt) -> PromptProfile:
        """构建提示词画像"""
        import uuid
        
        primary_content = prompt.get_primary_content() or ""
        text = primary_content.lower()
        
        content_category = ContentCategory.ART
        if "photo" in text or "photograph" in text:
            content_category = ContentCategory.PHOTOGRAPHY
        elif "building" in text or "architecture" in text:
            content_category = ContentCategory.ARCHITECTURE
        elif "nature" in text or "landscape" in text:
            content_category = ContentCategory.NATURE
        elif "portrait" in text or "person" in text:
            content_category = ContentCategory.PORTRAIT
        
        word_count = len(primary_content.split())
        complexity_level = "simple"
        if word_count > 100:
            complexity_level = "complex"
        elif word_count > 50:
            complexity_level = "moderate"
        
        creativity_level = "moderate"
        if any(
            word in text for word in [
                "fantasy", "surreal", "imagine", "dream", "creative"
            ]
        ):
            creativity_level = "high"
        
        detail_level = "moderate"
        if any(
            word in text for word in [
                "detailed", "highly detailed", "masterpiece", "8k", "4k"
            ]
        ):
            detail_level = "high"
        
        style_references = []
        for indicator in self.style_indicators:
            if indicator in text:
                style_references.append(indicator)
        
        return PromptProfile(
            profile_id=str(uuid.uuid4()),
            content_category=content_category,
            complexity_level=complexity_level,
            creativity_level=creativity_level,
            detail_level=detail_level,
            emotional_tone=None,
            target_audience=None,
            style_references=style_references,
        )


class PromptEnhancer:
    """提示词增强器"""
    
    def __init__(self):
        self.enhancement_patterns = {
            "quality_boost": [
                ("masterpiece", ", best quality, masterpiece"),
                ("detailed", ", ultra detailed, highly detailed"),
                ("quality", ", best quality, professional"),
            ],
            "style_improvement": [
                ("style", ", professional style, artistic style"),
                ("art", ", professional artwork, masterpiece"),
            ],
            "technical_enhance": [
                ("render", ", 8k, 4k, high resolution, photorealistic"),
                ("realistic", ", photorealistic, highly realistic"),
            ],
        }
        
        self.negative_suggestions = [
            "blurry, low quality",
            "ugly, deformed",
            "watermark, signature",
            "extra fingers, extra limbs",
            "bad anatomy, bad proportions",
        ]
    
    def generate_suggestions(
        self,
        awareness_result: AwarenessResult
    ) -> List[EnhancementSuggestion]:
        """生成增强建议"""
        import uuid
        
        suggestions = []
        
        primary_content = awareness_result.original_prompt.get_primary_content() or ""
        
        for pattern_type, replacements in self.enhancement_patterns.items():
            for original, enhanced in replacements:
                if original in primary_content.lower() and enhanced not in primary_content:
                    suggestion = EnhancementSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        type=pattern_type,
                        original=original,
                        enhanced=enhanced,
                        expected_improvement=0.15,
                        description=f"添加 {enhanced} 来提升质量"
                    )
                    suggestions.append(suggestion)
        
        has_negative = any(
            elem.role == PromptRole.NEGATIVE
            for elem in awareness_result.original_prompt.elements
        )
        
        if not has_negative:
            suggestion = EnhancementSuggestion(
                suggestion_id=str(uuid.uuid4()),
                type="negative_addition",
                original="",
                enhanced=", ".join(self.negative_suggestions[:3]),
                expected_improvement=0.2,
                description="添加负面提示词以排除不需要的元素"
            )
            suggestions.append(suggestion)
        
        return suggestions


class MultimodalRouter:
    """多模态路由 - 推荐引擎"""
    
    def __init__(self):
        self.intent_to_engines = {
            PromptIntent.CREATIVE: [
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.TEXT_TO_VIDEO,
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
            ],
            PromptIntent.TECHNICAL: [
                ModelFunctionType.IMAGE_UPSCALE,
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
                ModelFunctionType.TEXT_TO_IMAGE,
            ],
            PromptIntent.STYLE_ADAPTATION: [
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ],
            PromptIntent.QUALITY_ENHANCEMENT: [
                ModelFunctionType.IMAGE_UPSCALE,
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ],
            PromptIntent.MASTERPIECE: [
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.IMAGE_UPSCALE,
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
            ],
            PromptIntent.EXPERIMENTATION: [
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
                ModelFunctionType.IMAGE_EDIT,
            ],
        }
        
        self.category_to_engines = {
            ContentCategory.ART: [
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.IMAGE_STYLE_TRANSFER,
            ],
            ContentCategory.PHOTOGRAPHY: [
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.IMAGE_UPSCALE,
                ModelFunctionType.IMAGE_EDIT,
            ],
            ContentCategory.VIDEO: [
                ModelFunctionType.TEXT_TO_VIDEO,
                ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ],
        }
    
    def recommend_engines(
        self,
        awareness_result: AwarenessResult
    ) -> List[ModelFunctionType]:
        """推荐引擎"""
        recommendations = set()
        
        profile = awareness_result.prompt_profile
        intent = awareness_result.intent_detection.primary_intent
        
        if intent in self.intent_to_engines:
            recommendations.update(self.intent_to_engines[intent])
        
        if profile.content_category in self.category_to_engines:
            recommendations.update(self.category_to_engines[profile.content_category])
        
        if not recommendations:
            recommendations.add(ModelFunctionType.TEXT_TO_IMAGE)
        
        return list(recommendations)
    
    def suggest_runtime_parameters(
        self,
        awareness_result: AwarenessResult
    ) -> Dict[str, Any]:
        """建议运行参数"""
        quality = awareness_result.quality_assessment.overall_quality
        intent = awareness_result.intent_detection.primary_intent
        
        params = {
            "quality_preset": "high" if quality >= 0.7 else "standard",
            "enable_creativity": intent in [
                PromptIntent.CREATIVE, PromptIntent.EXPERIMENTATION
            ],
            "auto_enhance": quality < 0.6,
        }
        
        return params


class PromptAwarenessEngine:
    """提示词敏锐性引擎 - 统一接口"""
    
    def __init__(self):
        self.analyzer = PromptAnalyzer()
        self.enhancer = PromptEnhancer()
        self.router = MultimodalRouter()
    
    def analyze(
        self,
        prompt: RichPrompt
    ) -> AwarenessResult:
        """完整分析流程"""
        import uuid
        
        keyword_analysis = self.analyzer.analyze_keywords(prompt)
        intent_detection = self.analyzer.detect_intent(prompt)
        quality_assessment = self.analyzer.assess_quality(prompt)
        prompt_profile = self.analyzer.build_profile(prompt)
        
        temp_result = AwarenessResult(
            analysis_id=str(uuid.uuid4()),
            original_prompt=prompt,
            keyword_analysis=keyword_analysis,
            intent_detection=intent_detection,
            quality_assessment=quality_assessment,
            prompt_profile=prompt_profile,
            enhancement_suggestions=[],
            recommended_engines=[],
        )
        
        enhancement_suggestions = self.enhancer.generate_suggestions(temp_result)
        recommended_engines = self.router.recommend_engines(temp_result)
        runtime_parameters = self.router.suggest_runtime_parameters(temp_result)
        
        return AwarenessResult(
            analysis_id=temp_result.analysis_id,
            original_prompt=prompt,
            keyword_analysis=keyword_analysis,
            intent_detection=intent_detection,
            quality_assessment=quality_assessment,
            prompt_profile=prompt_profile,
            enhancement_suggestions=enhancement_suggestions,
            recommended_engines=recommended_engines,
            runtime_parameters=runtime_parameters,
        )
