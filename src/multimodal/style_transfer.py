"""风格转换模块 - 图片、视频、音频风格转换"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)

logger = logging.getLogger("hydraflow.multimodal.style_transfer")


class ArtStyle(str, Enum):
    """艺术风格"""
    VAN_GOGH = "van_gogh"
    PICASSO = "picasso"
    MONET = "monet"
    DA_VINCI = "da_vinci"
    ANIME = "anime"
    CYBERPUNK = "cyberpunk"
    WATERCOLOR = "watercolor"
    OIL_PAINTING = "oil_painting"
    SKETCH = "sketch"
    CARTOON = "cartoon"
    RETRO = "retro"
    NEON = "neon"
    CUSTOM = "custom"


class AudioStyle(str, Enum):
    """音频风格"""
    CLASSICAL = "classical"
    JAZZ = "jazz"
    ROCK = "rock"
    POP = "pop"
    HIP_HOP = "hip_hop"
    ELECTRONIC = "electronic"
    AMBIENT = "ambient"
    LO_FI = "lo_fi"
    CINEMATIC = "cinematic"
    CUSTOM = "custom"


@dataclass
class StyleTransferConfig:
    """风格转换配置"""
    style: ArtStyle = ArtStyle.VAN_GOGH
    style_strength: float = 0.7
    preserve_original: float = 0.3
    seed: Optional[int] = None
    output_format: str = "png"
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioStyleTransferConfig:
    """音频风格转换配置"""
    style: AudioStyle = AudioStyle.CLASSICAL
    style_strength: float = 0.6
    preserve_content: float = 0.4
    sample_rate: int = 44100
    bit_depth: int = 16
    seed: Optional[int] = None
    output_format: str = "wav"
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StyleTransferResult:
    """风格转换结果"""
    success: bool
    output_path: Optional[str] = None
    style_used: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StyleTransferEngine:
    """风格转换引擎"""
    
    def __init__(self):
        self.validator = get_consistency_validator()
        self._image_models: Dict[str, Any] = {}
        self._video_models: Dict[str, Any] = {}
        self._audio_models: Dict[str, Any] = {}
    
    def transfer_image_style(
        self,
        image_path: str,
        config: StyleTransferConfig,
        model_id: Optional[str] = None,
    ) -> StyleTransferResult:
        """图片风格转换"""
        validation_data = {
            "width": config.additional_params.get("width", 1024),
            "height": config.additional_params.get("height", 1024),
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.IMAGE_STYLE_TRANSFER,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return StyleTransferResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_image_transfer(image_path, config, model_id)
            return result
        except Exception as e:
            logger.error(f"图片风格转换失败: {str(e)}")
            return StyleTransferResult(
                success=False,
                error_message=str(e),
            )
    
    def transfer_video_style(
        self,
        video_path: str,
        config: StyleTransferConfig,
        model_id: Optional[str] = None,
    ) -> StyleTransferResult:
        """视频风格转换"""
        validation_data = {
            "fps": config.additional_params.get("fps", 24),
            "duration": config.additional_params.get("duration", 30),
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.VIDEO_STYLE_TRANSFER,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return StyleTransferResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_video_transfer(video_path, config, model_id)
            return result
        except Exception as e:
            logger.error(f"视频风格转换失败: {str(e)}")
            return StyleTransferResult(
                success=False,
                error_message=str(e),
            )
    
    def transfer_audio_style(
        self,
        audio_path: str,
        config: AudioStyleTransferConfig,
        model_id: Optional[str] = None,
    ) -> StyleTransferResult:
        """音频风格转换"""
        validation_data = {
            "sample_rate": config.sample_rate,
            "bit_depth": config.bit_depth,
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.AUDIO_STYLE_TRANSFER,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return StyleTransferResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_audio_transfer(audio_path, config, model_id)
            return result
        except Exception as e:
            logger.error(f"音频风格转换失败: {str(e)}")
            return StyleTransferResult(
                success=False,
                error_message=str(e),
            )
    
    def _execute_image_transfer(
        self,
        image_path: str,
        config: StyleTransferConfig,
        model_id: Optional[str],
    ) -> StyleTransferResult:
        """执行图片风格转换"""
        logger.info(f"图片风格转换: {image_path} -> {config.style.value}")
        return StyleTransferResult(
            success=True,
            style_used=config.style.value,
            metadata={
                "style_strength": config.style_strength,
                "preserve_original": config.preserve_original,
                "seed": config.seed,
            },
        )
    
    def _execute_video_transfer(
        self,
        video_path: str,
        config: StyleTransferConfig,
        model_id: Optional[str],
    ) -> StyleTransferResult:
        """执行视频风格转换"""
        logger.info(f"视频风格转换: {video_path} -> {config.style.value}")
        return StyleTransferResult(
            success=True,
            style_used=config.style.value,
            metadata={
                "style_strength": config.style_strength,
                "preserve_original": config.preserve_original,
                "seed": config.seed,
            },
        )
    
    def _execute_audio_transfer(
        self,
        audio_path: str,
        config: AudioStyleTransferConfig,
        model_id: Optional[str],
    ) -> StyleTransferResult:
        """执行音频风格转换"""
        logger.info(f"音频风格转换: {audio_path} -> {config.style.value}")
        return StyleTransferResult(
            success=True,
            style_used=config.style.value,
            metadata={
                "style_strength": config.style_strength,
                "preserve_content": config.preserve_content,
                "sample_rate": config.sample_rate,
                "seed": config.seed,
            },
        )
    
    def list_art_styles(self) -> List[str]:
        """列出艺术风格"""
        return [s.value for s in ArtStyle]
    
    def list_audio_styles(self) -> List[str]:
        """列出音频风格"""
        return [s.value for s in AudioStyle]
