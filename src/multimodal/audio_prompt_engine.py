"""音频提示词数字公式化引擎 - 风格特性参数化、优化组合"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import math

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)

logger = logging.getLogger("hydraflow.multimodal.audio_prompt")


class EmotionalTone(float, Enum):
    """情感基调（0-1）"""
    VERY_SAD = 0.1
    SAD = 0.25
    NEUTRAL = 0.5
    HAPPY = 0.75
    VERY_HAPPY = 0.9
    EXCITED = 0.95


class EnergyLevel(float, Enum):
    """能量级别（0-1）"""
    VERY_CALM = 0.1
    CALM = 0.25
    MODERATE = 0.5
    ENERGETIC = 0.75
    VERY_ENERGETIC = 0.9
    INTENSE = 0.95


class MusicalGenre(str, Enum):
    """音乐流派"""
    CLASSICAL = "classical"
    JAZZ = "jazz"
    POP = "pop"
    ROCK = "rock"
    HIP_HOP = "hip_hop"
    ELECTRONIC = "electronic"
    AMBIENT = "ambient"
    LO_FI = "lo_fi"
    CINEMATIC = "cinematic"
    FOLK = "folk"
    BLUES = "blues"
    R_AND_B = "r_and_b"


class VoiceType(str, Enum):
    """人声类型"""
    FEMALE_SOPRANO = "female_soprano"
    FEMALE_ALTO = "female_alto"
    MALE_TENOR = "male_tenor"
    MALE_BASS = "male_bass"
    CHILD = "child"
    NEUTRAL = "neutral"


@dataclass
class AudioStyleParams:
    """音频风格参数（数字公式化）"""
    # 时域参数
    tempo: float = 120.0  # BPM (40-240)
    rhythm_complexity: float = 0.5  # 节奏复杂度 (0-1)
    dynamics_range: float = 0.6  # 动态范围 (0-1)
    
    # 频域参数
    brightness: float = 0.5  # 明亮度 (0-1)
    warmth: float = 0.5  # 温暖度 (0-1)
    harmonic_richness: float = 0.6  # 和声丰富度 (0-1)
    
    # 情感参数
    emotional_tone: EmotionalTone = EmotionalTone.NEUTRAL
    energy_level: EnergyLevel = EnergyLevel.MODERATE
    valence: float = 0.5  # 情感效价 (0-1, 消极-积极)
    arousal: float = 0.5  # 唤醒度 (0-1, 平静-激动)
    
    # 空间参数
    reverb_level: float = 0.3  # 混响水平 (0-1)
    stereo_width: float = 0.6  # 立体声宽度 (0-1)
    
    # 人声参数
    voice_type: Optional[VoiceType] = None
    pitch_shift: float = 0.0  # 音高偏移 (-12 到 +12 半音)
    vibrato_depth: float = 0.3  # 颤音深度 (0-1)
    
    # 流派参数
    genre: MusicalGenre = MusicalGenre.CLASSICAL
    genre_influence: float = 0.7  # 流派影响度 (0-1)
    
    def to_numeric_vector(self) -> List[float]:
        """转换为数值向量"""
        return [
            self.tempo / 240.0,  # 归一化
            self.rhythm_complexity,
            self.dynamics_range,
            self.brightness,
            self.warmth,
            self.harmonic_richness,
            self.emotional_tone.value,
            self.energy_level.value,
            self.valence,
            self.arousal,
            self.reverb_level,
            self.stereo_width,
            (self.pitch_shift + 12) / 24.0,  # 归一化
            self.vibrato_depth,
            self.genre_influence,
        ]
    
    @classmethod
    def from_numeric_vector(cls, vector: List[float]) -> 'AudioStyleParams':
        """从数值向量创建"""
        return cls(
            tempo=vector[0] * 240.0,
            rhythm_complexity=vector[1],
            dynamics_range=vector[2],
            brightness=vector[3],
            warmth=vector[4],
            harmonic_richness=vector[5],
            emotional_tone=EmotionalTone(min(max(vector[6], 0.1), 0.95)),
            energy_level=EnergyLevel(min(max(vector[7], 0.1), 0.95)),
            valence=vector[8],
            arousal=vector[9],
            reverb_level=vector[10],
            stereo_width=vector[11],
            pitch_shift=(vector[12] * 24.0) - 12.0,
            vibrato_depth=vector[13],
            genre_influence=vector[14],
        )


@dataclass
class PromptOptimizationResult:
    """提示词优化结果"""
    original_prompt: str
    optimized_prompt: str
    style_params: AudioStyleParams
    confidence_score: float
    alternative_params: List[AudioStyleParams] = field(default_factory=list)
    optimization_metadata: Dict[str, Any] = field(default_factory=dict)


class AudioPromptEngine:
    """音频提示词数字公式化引擎"""
    
    def __init__(self):
        self.validator = get_consistency_validator()
        self._genre_profiles: Dict[MusicalGenre, AudioStyleParams] = {}
        self._initialize_genre_profiles()
    
    def _initialize_genre_profiles(self) -> None:
        """初始化流派配置"""
        self._genre_profiles[MusicalGenre.CLASSICAL] = AudioStyleParams(
            tempo=80,
            rhythm_complexity=0.4,
            dynamics_range=0.8,
            brightness=0.4,
            warmth=0.6,
            harmonic_richness=0.8,
            emotional_tone=EmotionalTone.NEUTRAL,
            energy_level=EnergyLevel.CALM,
            valence=0.5,
            arousal=0.3,
            reverb_level=0.5,
            stereo_width=0.7,
            genre=MusicalGenre.CLASSICAL,
            genre_influence=0.9,
        )
        
        self._genre_profiles[MusicalGenre.JAZZ] = AudioStyleParams(
            tempo=100,
            rhythm_complexity=0.7,
            dynamics_range=0.6,
            brightness=0.5,
            warmth=0.7,
            harmonic_richness=0.85,
            emotional_tone=EmotionalTone.NEUTRAL,
            energy_level=EnergyLevel.MODERATE,
            valence=0.55,
            arousal=0.45,
            reverb_level=0.3,
            stereo_width=0.6,
            genre=MusicalGenre.JAZZ,
            genre_influence=0.85,
        )
        
        self._genre_profiles[MusicalGenre.POP] = AudioStyleParams(
            tempo=120,
            rhythm_complexity=0.4,
            dynamics_range=0.5,
            brightness=0.7,
            warmth=0.4,
            harmonic_richness=0.5,
            emotional_tone=EmotionalTone.HAPPY,
            energy_level=EnergyLevel.ENERGETIC,
            valence=0.75,
            arousal=0.7,
            reverb_level=0.2,
            stereo_width=0.5,
            genre=MusicalGenre.POP,
            genre_influence=0.8,
        )
        
        self._genre_profiles[MusicalGenre.ELECTRONIC] = AudioStyleParams(
            tempo=128,
            rhythm_complexity=0.6,
            dynamics_range=0.5,
            brightness=0.8,
            warmth=0.3,
            harmonic_richness=0.4,
            emotional_tone=EmotionalTone.EXCITED,
            energy_level=EnergyLevel.VERY_ENERGETIC,
            valence=0.7,
            arousal=0.85,
            reverb_level=0.4,
            stereo_width=0.8,
            genre=MusicalGenre.ELECTRONIC,
            genre_influence=0.9,
        )
        
        self._genre_profiles[MusicalGenre.AMBIENT] = AudioStyleParams(
            tempo=60,
            rhythm_complexity=0.2,
            dynamics_range=0.3,
            brightness=0.3,
            warmth=0.5,
            harmonic_richness=0.6,
            emotional_tone=EmotionalTone.NEUTRAL,
            energy_level=EnergyLevel.VERY_CALM,
            valence=0.5,
            arousal=0.15,
            reverb_level=0.8,
            stereo_width=0.9,
            genre=MusicalGenre.AMBIENT,
            genre_influence=0.95,
        )
        
        self._genre_profiles[MusicalGenre.LO_FI] = AudioStyleParams(
            tempo=70,
            rhythm_complexity=0.3,
            dynamics_range=0.4,
            brightness=0.35,
            warmth=0.65,
            harmonic_richness=0.5,
            emotional_tone=EmotionalTone.CALM,
            energy_level=EnergyLevel.CALM,
            valence=0.55,
            arousal=0.25,
            reverb_level=0.45,
            stereo_width=0.6,
            genre=MusicalGenre.LO_FI,
            genre_influence=0.9,
        )
    
    def parse_prompt(
        self,
        prompt: str,
        genre_hint: Optional[MusicalGenre] = None,
    ) -> AudioStyleParams:
        """解析提示词为数字参数"""
        params = AudioStyleParams()
        
        if genre_hint and genre_hint in self._genre_profiles:
            base_params = self._genre_profiles[genre_hint]
            params = AudioStyleParams(
                tempo=base_params.tempo,
                rhythm_complexity=base_params.rhythm_complexity,
                dynamics_range=base_params.dynamics_range,
                brightness=base_params.brightness,
                warmth=base_params.warmth,
                harmonic_richness=base_params.harmonic_richness,
                emotional_tone=base_params.emotional_tone,
                energy_level=base_params.energy_level,
                valence=base_params.valence,
                arousal=base_params.arousal,
                reverb_level=base_params.reverb_level,
                stereo_width=base_params.stereo_width,
                genre=genre_hint,
                genre_influence=base_params.genre_influence,
            )
        
        prompt_lower = prompt.lower()
        
        if "fast" in prompt_lower or "upbeat" in prompt_lower:
            params.tempo = min(params.tempo + 30, 200)
            params.energy_level = EnergyLevel.ENERGETIC
        if "slow" in prompt_lower or "relaxing" in prompt_lower:
            params.tempo = max(params.tempo - 30, 50)
            params.energy_level = EnergyLevel.CALM
        
        if "happy" in prompt_lower or "cheerful" in prompt_lower:
            params.emotional_tone = EmotionalTone.HAPPY
            params.valence = 0.8
        if "sad" in prompt_lower or "melancholy" in prompt_lower:
            params.emotional_tone = EmotionalTone.SAD
            params.valence = 0.3
        
        if "bright" in prompt_lower or "clear" in prompt_lower:
            params.brightness = min(params.brightness + 0.3, 1.0)
        if "warm" in prompt_lower or "mellow" in prompt_lower:
            params.warmth = min(params.warmth + 0.3, 1.0)
        
        if "reverb" in prompt_lower or "echo" in prompt_lower:
            params.reverb_level = min(params.reverb_level + 0.3, 1.0)
        if "dry" in prompt_lower:
            params.reverb_level = max(params.reverb_level - 0.3, 0.0)
        
        return params
    
    def optimize_prompt(
        self,
        prompt: str,
        target_genre: Optional[MusicalGenre] = None,
        num_variations: int = 3,
    ) -> PromptOptimizationResult:
        """优化提示词并生成参数组合"""
        base_params = self.parse_prompt(prompt, target_genre)
        
        validation_data = {
            "sample_rate": 44100,
            "bit_depth": 16,
        }
        
        self.validator.validate(
            function_type=ModelFunctionType.TEXT_TO_AUDIO,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        optimized_prompt = self._construct_optimized_prompt(prompt, base_params)
        
        variations = self._generate_parameter_variations(base_params, num_variations)
        
        confidence = self._calculate_confidence(base_params)
        
        return PromptOptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized_prompt,
            style_params=base_params,
            confidence_score=confidence,
            alternative_params=variations,
            optimization_metadata={
                "vector_dimension": len(base_params.to_numeric_vector()),
                "genre_applied": base_params.genre.value,
                "num_variations": num_variations,
            },
        )
    
    def _construct_optimized_prompt(
        self,
        original_prompt: str,
        params: AudioStyleParams,
    ) -> str:
        """构建优化后的提示词"""
        parts = [original_prompt]
        
        if params.genre != MusicalGenre.CLASSICAL or params.genre_influence > 0.5:
            parts.append(f"in {params.genre.value} style")
        
        tempo_desc = "slow" if params.tempo < 80 else "fast" if params.tempo > 140 else "moderate"
        parts.append(f"at a {tempo_desc} tempo ({int(params.tempo)} BPM)")
        
        if params.emotional_tone != EmotionalTone.NEUTRAL:
            emotion_desc = params.emotional_tone.name.lower().replace("_", " ")
            parts.append(f"with a {emotion_desc} emotional tone")
        
        if params.energy_level != EnergyLevel.MODERATE:
            energy_desc = params.energy_level.name.lower().replace("_", " ")
            parts.append(f"with {energy_desc} energy")
        
        return ", ".join(parts)
    
    def _generate_parameter_variations(
        self,
        base_params: AudioStyleParams,
        num_variations: int,
    ) -> List[AudioStyleParams]:
        """生成参数变体"""
        variations = []
        
        for i in range(num_variations):
            vector = base_params.to_numeric_vector()
            variation = vector.copy()
            
            for j in range(len(variation)):
                delta = (math.sin(i * 0.5 + j) * 0.1)
                variation[j] = max(0.0, min(1.0, variation[j] + delta))
            
            variant_params = AudioStyleParams.from_numeric_vector(variation)
            variant_params.genre = base_params.genre
            variations.append(variant_params)
        
        return variations
    
    def _calculate_confidence(self, params: AudioStyleParams) -> float:
        """计算置信度"""
        base_confidence = 0.7
        
        if params.genre in self._genre_profiles:
            base_confidence += 0.15
        
        if 60 <= params.tempo <= 180:
            base_confidence += 0.05
        
        if 0.2 <= params.valence <= 0.8:
            base_confidence += 0.05
        
        return min(1.0, max(0.0, base_confidence))
    
    def blend_styles(
        self,
        style_a: AudioStyleParams,
        style_b: AudioStyleParams,
        blend_ratio: float = 0.5,
    ) -> AudioStyleParams:
        """混合两种风格"""
        blend_ratio = max(0.0, min(1.0, blend_ratio))
        
        vector_a = style_a.to_numeric_vector()
        vector_b = style_b.to_numeric_vector()
        
        blended_vector = [
            a * blend_ratio + b * (1 - blend_ratio)
            for a, b in zip(vector_a, vector_b)
        ]
        
        blended = AudioStyleParams.from_numeric_vector(blended_vector)
        blended.genre = style_a.genre if blend_ratio > 0.5 else style_b.genre
        
        return blended
    
    def get_style_preset(
        self,
        genre: MusicalGenre,
    ) -> AudioStyleParams:
        """获取风格预设"""
        return self._genre_profiles.get(genre, AudioStyleParams())
    
    def list_available_genres(self) -> List[str]:
        """列出可用流派"""
        return [g.value for g in MusicalGenre]
