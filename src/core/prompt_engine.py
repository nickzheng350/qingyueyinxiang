"""多元化提示词引擎 - 结构完整，跨类型互补"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import json

from src.model_dispatcher.type_system import ModelFunctionType

logger = logging.getLogger("hydraflow.core.prompt_engine")


class PromptType(str, Enum):
    """提示词类型"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    COMBINED = "combined"


class QualityLevel(str, Enum):
    """质量级别"""
    FAST = "fast"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


class AspectRatio(str, Enum):
    """宽高比"""
    SQUARE = "1:1"
    STANDARD = "4:3"
    WIDE = "16:9"
    ULTRA_WIDE = "21:9"
    PORTRAIT = "9:16"


class PromptRole(str, Enum):
    """提示词角色"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUPPORT = "support"
    CONSTRAINT = "constraint"
    STYLE = "style"
    NEGATIVE = "negative"


@dataclass
class PromptElement:
    """提示词元素"""
    content: Union[str, List[str]]
    role: PromptRole
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "role": self.role.value,
            "weight": self.weight,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptElement":
        return cls(
            content=data["content"],
            role=PromptRole(data["role"]),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VisualConfig:
    """视觉配置"""
    aspect_ratio: AspectRatio = AspectRatio.WIDE
    resolution: tuple = (1024, 1024)
    style_presets: List[str] = field(default_factory=list)
    negative_prompts: List[str] = field(default_factory=list)
    seed: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "aspect_ratio": self.aspect_ratio.value,
            "resolution": list(self.resolution),
            "style_presets": self.style_presets,
            "negative_prompts": self.negative_prompts,
            "seed": self.seed,
        }


@dataclass
class AudioConfig:
    """音频配置"""
    duration: float = 10.0
    sample_rate: int = 44100
    channels: int = 2
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "genre": self.genre,
            "mood": self.mood,
            "tempo": self.tempo,
        }


@dataclass
class VideoConfig:
    """视频配置"""
    duration: float = 10.0
    fps: float = 30.0
    resolution: tuple = (1920, 1080)
    aspect_ratio: AspectRatio = AspectRatio.WIDE
    motion_level: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": self.duration,
            "fps": self.fps,
            "resolution": list(self.resolution),
            "aspect_ratio": self.aspect_ratio.value,
            "motion_level": self.motion_level,
        }


@dataclass
class RichPrompt:
    """丰富的提示词结构"""
    prompt_id: str
    prompt_type: PromptType
    elements: List[PromptElement] = field(default_factory=list)
    visual_config: Optional[VisualConfig] = None
    audio_config: Optional[AudioConfig] = None
    video_config: Optional[VideoConfig] = None
    quality: QualityLevel = QualityLevel.STANDARD
    target_types: List[ModelFunctionType] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    cross_type_complements: List[ModelFunctionType] = field(default_factory=list)
    
    def add_element(self, element: PromptElement):
        """添加元素"""
        self.elements.append(element)
    
    def get_element_by_role(self, role: PromptRole) -> Optional[PromptElement]:
        """按角色获取元素"""
        for elem in self.elements:
            if elem.role == role:
                return elem
        return None
    
    def get_primary_content(self) -> Optional[str]:
        """获取主内容"""
        primary = self.get_element_by_role(PromptRole.PRIMARY)
        if primary and isinstance(primary.content, str):
            return primary.content
        elif primary and isinstance(primary.content, list):
            return " ".join(primary.content)
        return None
    
    def get_negative_prompts(self) -> List[str]:
        """获取负面提示词"""
        negatives = []
        for elem in self.elements:
            if elem.role == PromptRole.NEGATIVE:
                if isinstance(elem.content, list):
                    negatives.extend(elem.content)
                else:
                    negatives.append(elem.content)
        return negatives
    
    def calculate_complement_score(self, target_type: ModelFunctionType) -> float:
        """计算互补分数"""
        if target_type in self.cross_type_complements:
            return 1.0
        if target_type in self.target_types:
            return 0.8
        return 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "prompt_id": self.prompt_id,
            "prompt_type": self.prompt_type.value,
            "elements": [e.to_dict() for e in self.elements],
            "visual_config": self.visual_config.to_dict() if self.visual_config else None,
            "audio_config": self.audio_config.to_dict() if self.audio_config else None,
            "video_config": self.video_config.to_dict() if self.video_config else None,
            "quality": self.quality.value,
            "target_types": [t.value for t in self.target_types],
            "context": self.context,
            "cross_type_complements": [t.value for t in self.cross_type_complements],
        }
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RichPrompt":
        """从字典创建"""
        return cls(
            prompt_id=data["prompt_id"],
            prompt_type=PromptType(data["prompt_type"]),
            elements=[PromptElement.from_dict(e) for e in data.get("elements", [])],
            visual_config=VisualConfig(**data["visual_config"]) if data.get("visual_config") else None,
            audio_config=AudioConfig(**data["audio_config"]) if data.get("audio_config") else None,
            video_config=VideoConfig(**data["video_config"]) if data.get("video_config") else None,
            quality=QualityLevel(data.get("quality", "standard")),
            target_types=[ModelFunctionType(t) for t in data.get("target_types", [])],
            context=data.get("context", {}),
            cross_type_complements=[ModelFunctionType(t) for t in data.get("cross_type_complements", [])],
        )


class CrossTypeComplementEngine:
    """跨类型互补引擎"""
    
    def __init__(self):
        self.compliment_map: Dict[ModelFunctionType, List[ModelFunctionType]] = {
            ModelFunctionType.TEXT_TO_AUDIO: [
                ModelFunctionType.AUDIO_TO_TEXT,
                ModelFunctionType.AUDIO_STYLE_TRANSFER,
            ],
            ModelFunctionType.TEXT_TO_VIDEO: [
                ModelFunctionType.IMAGE_TO_VIDEO,
                ModelFunctionType.TEXT_TO_IMAGE,
                ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ],
            ModelFunctionType.SCRIPT_TO_AUDIO: [
                ModelFunctionType.AV_FUSION,
                ModelFunctionType.BACKGROUND_MUSIC,
                ModelFunctionType.FOLEY,
            ],
            ModelFunctionType.CHARACTER_VOICEOVER: [
                ModelFunctionType.BACKGROUND_MUSIC,
                ModelFunctionType.FOLEY,
                ModelFunctionType.AV_FUSION,
            ],
        }
    
    def get_compliments(self, task_type: ModelFunctionType) -> List[ModelFunctionType]:
        """获取互补类型"""
        return self.compliment_map.get(task_type, [])
    
    def suggest_complementary_tasks(self, prompt: RichPrompt) -> List[Dict[str, Any]]:
        """建议互补任务"""
        suggestions = []
        for target in prompt.target_types:
            compliments = self.get_compliments(target)
            for comp in compliments:
                if comp not in prompt.target_types:
                    suggestions.append({
                        "type": comp,
                        "relevance": prompt.calculate_complement_score(comp),
                        "description": f"Complement for {target.value}",
                    })
        suggestions.sort(key=lambda x: -x["relevance"])
        return suggestions


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self):
        self.complement_engine = CrossTypeComplementEngine()
    
    def build_text_prompt(
        self,
        primary: str,
        style: Optional[str] = None,
        negatives: Optional[List[str]] = None,
        **kwargs
    ) -> RichPrompt:
        """构建文本提示词"""
        import uuid
        prompt = RichPrompt(
            prompt_id=str(uuid.uuid4()),
            prompt_type=PromptType.TEXT,
            target_types=[ModelFunctionType.TEXT_GENERATION],
        )
        
        prompt.add_element(PromptElement(content=primary, role=PromptRole.PRIMARY))
        
        if style:
            prompt.add_element(PromptElement(content=style, role=PromptRole.STYLE))
        
        if negatives:
            for neg in negatives:
                prompt.add_element(PromptElement(content=neg, role=PromptRole.NEGATIVE))
        
        return prompt
    
    def build_image_prompt(
        self,
        description: str,
        style: Optional[str] = None,
        aspect_ratio: AspectRatio = AspectRatio.WIDE,
        quality: QualityLevel = QualityLevel.STANDARD,
        negatives: Optional[List[str]] = None,
        **kwargs
    ) -> RichPrompt:
        """构建图像提示词"""
        import uuid
        prompt = RichPrompt(
            prompt_id=str(uuid.uuid4()),
            prompt_type=PromptType.IMAGE,
            target_types=[ModelFunctionType.TEXT_TO_IMAGE],
            quality=quality,
        )
        
        prompt.add_element(PromptElement(content=description, role=PromptRole.PRIMARY))
        
        if style:
            prompt.add_element(PromptElement(content=style, role=PromptRole.STYLE))
        
        if negatives:
            for neg in negatives:
                prompt.add_element(PromptElement(content=neg, role=PromptRole.NEGATIVE))
        
        prompt.visual_config = VisualConfig(
            aspect_ratio=aspect_ratio,
            resolution={
                QualityLevel.FAST: (512, 512),
                QualityLevel.STANDARD: (1024, 1024),
                QualityLevel.HIGH: (1536, 1536),
                QualityLevel.ULTRA: (2048, 2048),
            }[quality],
        )
        
        prompt.cross_type_complements = [
            ModelFunctionType.IMAGE_EDIT,
            ModelFunctionType.IMAGE_UPSCALE,
            ModelFunctionType.IMAGE_TO_VIDEO,
        ]
        
        return prompt
    
    def build_audio_prompt(
        self,
        description: str,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        duration: float = 10.0,
        quality: QualityLevel = QualityLevel.STANDARD,
        **kwargs
    ) -> RichPrompt:
        """构建音频提示词"""
        import uuid
        prompt = RichPrompt(
            prompt_id=str(uuid.uuid4()),
            prompt_type=PromptType.AUDIO,
            target_types=[ModelFunctionType.TEXT_TO_AUDIO],
            quality=quality,
        )
        
        prompt.add_element(PromptElement(content=description, role=PromptRole.PRIMARY))
        
        if genre:
            prompt.add_element(PromptElement(content=genre, role=PromptRole.STYLE, weight=0.8))
        if mood:
            prompt.add_element(PromptElement(content=mood, role=PromptRole.STYLE, weight=0.7))
        
        prompt.audio_config = AudioConfig(
            duration=duration,
            genre=genre,
            mood=mood,
        )
        
        prompt.cross_type_complements = [
            ModelFunctionType.AUDIO_STYLE_TRANSFER,
            ModelFunctionType.AUDIO_TO_TEXT,
            ModelFunctionType.AUDIO_TO_VIDEO,
        ]
        
        return prompt
    
    def build_video_prompt(
        self,
        description: str,
        duration: float = 10.0,
        fps: float = 30.0,
        quality: QualityLevel = QualityLevel.STANDARD,
        **kwargs
    ) -> RichPrompt:
        """构建视频提示词"""
        import uuid
        prompt = RichPrompt(
            prompt_id=str(uuid.uuid4()),
            prompt_type=PromptType.VIDEO,
            target_types=[ModelFunctionType.TEXT_TO_VIDEO],
            quality=quality,
        )
        
        prompt.add_element(PromptElement(content=description, role=PromptRole.PRIMARY))
        
        prompt.video_config = VideoConfig(
            duration=duration,
            fps=fps,
            resolution={
                QualityLevel.FAST: (640, 360),
                QualityLevel.STANDARD: (1280, 720),
                QualityLevel.HIGH: (1920, 1080),
                QualityLevel.ULTRA: (3840, 2160),
            }[quality],
        )
        
        prompt.cross_type_complements = [
            ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ModelFunctionType.VIDEO_TO_TEXT,
            ModelFunctionType.AV_FUSION,
        ]
        
        return prompt
    
    def build_combined_prompt(
        self,
        prompts: List[RichPrompt],
        **kwargs
    ) -> RichPrompt:
        """构建组合提示词"""
        import uuid
        combined = RichPrompt(
            prompt_id=str(uuid.uuid4()),
            prompt_type=PromptType.COMBINED,
        )
        
        all_elements = []
        all_targets = []
        
        for prompt in prompts:
            all_elements.extend(prompt.elements)
            all_targets.extend(prompt.target_types)
            
            if prompt.visual_config and not combined.visual_config:
                combined.visual_config = prompt.visual_config
            if prompt.audio_config and not combined.audio_config:
                combined.audio_config = prompt.audio_config
            if prompt.video_config and not combined.video_config:
                combined.video_config = prompt.video_config
        
        combined.elements = all_elements
        combined.target_types = list(set(all_targets))
        
        return combined


class PromptOptimizer:
    """提示词优化器"""
    
    def __init__(self):
        self.pattern_weights = {
            "descriptive": 1.2,
            "concise": 0.8,
            "technical": 1.1,
            "artistic": 1.0,
        }
    
    def optimize_for_type(self, prompt: RichPrompt, task_type: ModelFunctionType) -> RichPrompt:
        """为特定类型优化"""
        optimized = prompt
        optimized.context["optimized_for"] = task_type.value
        
        type_tweaks = {
            ModelFunctionType.TEXT_TO_IMAGE: self._optimize_visual_prompt,
            ModelFunctionType.TEXT_TO_AUDIO: self._optimize_audio_prompt,
            ModelFunctionType.TEXT_TO_VIDEO: self._optimize_video_prompt,
        }
        
        if task_type in type_tweaks:
            optimized = type_tweaks[task_type](prompt)
        
        return optimized
    
    def _optimize_visual_prompt(self, prompt: RichPrompt) -> RichPrompt:
        """优化视觉提示词"""
        if not prompt.visual_config:
            prompt.visual_config = VisualConfig()
        return prompt
    
    def _optimize_audio_prompt(self, prompt: RichPrompt) -> RichPrompt:
        """优化音频提示词"""
        if not prompt.audio_config:
            prompt.audio_config = AudioConfig()
        return prompt
    
    def _optimize_video_prompt(self, prompt: RichPrompt) -> RichPrompt:
        """优化视频提示词"""
        if not prompt.video_config:
            prompt.video_config = VideoConfig()
        return prompt


class DiversifiedPromptEngine:
    """多元化提示词引擎"""
    
    def __init__(self):
        self.builder = PromptBuilder()
        self.optimizer = PromptOptimizer()
        self.complement_engine = CrossTypeComplementEngine()
    
    def create_prompt(
        self,
        prompt_type: PromptType,
        content: str,
        **kwargs
    ) -> RichPrompt:
        """创建提示词"""
        factory_map = {
            PromptType.TEXT: self.builder.build_text_prompt,
            PromptType.IMAGE: self.builder.build_image_prompt,
            PromptType.AUDIO: self.builder.build_audio_prompt,
            PromptType.VIDEO: self.builder.build_video_prompt,
        }
        
        factory = factory_map.get(prompt_type)
        if not factory:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
        
        return factory(content, **kwargs)
    
    def get_complementary_suggestions(self, prompt: RichPrompt) -> List[Dict[str, Any]]:
        """获取互补建议"""
        return self.complement_engine.suggest_complementary_tasks(prompt)
