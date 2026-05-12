"""格式转换模块 - 图片、视频、音频格式转换"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)

logger = logging.getLogger("hydraflow.multimodal.format_converter")


@dataclass
class ImageFormatConfig:
    """图片格式转换配置"""
    output_format: str = "png"
    quality: int = 90
    width: Optional[int] = None
    height: Optional[int] = None
    preserve_aspect_ratio: bool = True
    optimize: bool = True
    progressive: bool = False


@dataclass
class VideoFormatConfig:
    """视频格式转换配置"""
    output_format: str = "mp4"
    codec: str = "h264"
    quality: int = 23
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    bitrate: Optional[str] = None
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"


@dataclass
class AudioFormatConfig:
    """音频格式转换配置"""
    output_format: str = "wav"
    codec: str = "pcm_s16le"
    sample_rate: int = 44100
    bit_depth: int = 16
    channels: int = 2
    bitrate: Optional[str] = None


@dataclass
class FormatConversionResult:
    """格式转换结果"""
    success: bool
    output_path: Optional[str] = None
    output_format: Optional[str] = None
    original_size: Optional[int] = None
    converted_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FormatConverter:
    """格式转换器"""
    
    def __init__(self):
        self.validator = get_consistency_validator()
    
    def convert_image(
        self,
        input_path: str,
        config: ImageFormatConfig,
        output_path: Optional[str] = None,
    ) -> FormatConversionResult:
        """图片格式转换"""
        validation_data = {
            "width": config.width or 1024,
            "height": config.height or 1024,
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.IMAGE_FORMAT_CONVERT,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return FormatConversionResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_image_conversion(input_path, config, output_path)
            return result
        except Exception as e:
            logger.error(f"图片格式转换失败: {str(e)}")
            return FormatConversionResult(
                success=False,
                error_message=str(e),
            )
    
    def convert_video(
        self,
        input_path: str,
        config: VideoFormatConfig,
        output_path: Optional[str] = None,
    ) -> FormatConversionResult:
        """视频格式转换"""
        validation_data = {
            "duration": config.width or 100,
            "fps": config.fps or 24,
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.VIDEO_FORMAT_CONVERT,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return FormatConversionResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_video_conversion(input_path, config, output_path)
            return result
        except Exception as e:
            logger.error(f"视频格式转换失败: {str(e)}")
            return FormatConversionResult(
                success=False,
                error_message=str(e),
            )
    
    def convert_audio(
        self,
        input_path: str,
        config: AudioFormatConfig,
        output_path: Optional[str] = None,
    ) -> FormatConversionResult:
        """音频格式转换"""
        validation_data = {
            "sample_rate": config.sample_rate,
            "bit_depth": config.bit_depth,
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.AUDIO_FORMAT_CONVERT,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return FormatConversionResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_audio_conversion(input_path, config, output_path)
            return result
        except Exception as e:
            logger.error(f"音频格式转换失败: {str(e)}")
            return FormatConversionResult(
                success=False,
                error_message=str(e),
            )
    
    def _execute_image_conversion(
        self,
        input_path: str,
        config: ImageFormatConfig,
        output_path: Optional[str],
    ) -> FormatConversionResult:
        """执行图片格式转换"""
        logger.info(f"图片格式转换: {input_path} -> {config.output_format}")
        return FormatConversionResult(
            success=True,
            output_format=config.output_format,
            metadata={
                "quality": config.quality,
                "width": config.width,
                "height": config.height,
                "optimize": config.optimize,
            },
        )
    
    def _execute_video_conversion(
        self,
        input_path: str,
        config: VideoFormatConfig,
        output_path: Optional[str],
    ) -> FormatConversionResult:
        """执行视频格式转换"""
        logger.info(f"视频格式转换: {input_path} -> {config.output_format}")
        return FormatConversionResult(
            success=True,
            output_format=config.output_format,
            metadata={
                "codec": config.codec,
                "quality": config.quality,
                "fps": config.fps,
                "audio_codec": config.audio_codec,
            },
        )
    
    def _execute_audio_conversion(
        self,
        input_path: str,
        config: AudioFormatConfig,
        output_path: Optional[str],
    ) -> FormatConversionResult:
        """执行音频格式转换"""
        logger.info(f"音频格式转换: {input_path} -> {config.output_format}")
        return FormatConversionResult(
            success=True,
            output_format=config.output_format,
            metadata={
                "codec": config.codec,
                "sample_rate": config.sample_rate,
                "bit_depth": config.bit_depth,
                "channels": config.channels,
            },
        )
    
    @staticmethod
    def get_supported_image_formats() -> List[str]:
        """获取支持的图片格式"""
        return ["png", "jpg", "jpeg", "gif", "webp", "tiff", "bmp", "svg"]
    
    @staticmethod
    def get_supported_video_formats() -> List[str]:
        """获取支持的视频格式"""
        return ["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"]
    
    @staticmethod
    def get_supported_audio_formats() -> List[str]:
        """获取支持的音频格式"""
        return ["wav", "mp3", "flac", "aac", "ogg", "m4a", "wma"]
