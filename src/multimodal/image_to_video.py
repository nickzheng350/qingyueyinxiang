"""图生视频模块 - 将图片转换为视频"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

from src.model_dispatcher.type_system import (
    ModelFunctionType,
    get_consistency_validator,
    TouchPoint,
)

logger = logging.getLogger("hydraflow.multimodal.img2vid")


class VideoMotionType(str, Enum):
    """视频运动类型"""
    CAMERA_PAN = "camera_pan"
    CAMERA_ZOOM = "camera_zoom"
    CAMERA_TILT = "camera_tilt"
    SUBJECT_MOTION = "subject_motion"
    PARTICLE_EFFECT = "particle_effect"
    CUSTOM = "custom"


@dataclass
class ImageToVideoConfig:
    """图生视频配置"""
    duration: float = 5.0
    fps: int = 24
    width: Optional[int] = None
    height: Optional[int] = None
    motion_type: VideoMotionType = VideoMotionType.CAMERA_PAN
    motion_strength: float = 0.5
    consistency_level: float = 0.8
    seed: Optional[int] = None
    output_format: str = "mp4"
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageToVideoResult:
    """图生视频结果"""
    success: bool
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    duration: Optional[float] = None
    fps: Optional[int] = None
    resolution: Optional[tuple] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ImageToVideoGenerator:
    """图生视频生成器"""
    
    def __init__(self):
        self.validator = get_consistency_validator()
        self._models: Dict[str, Any] = {}
    
    def generate(
        self,
        image_path: str,
        config: Optional[ImageToVideoConfig] = None,
        model_id: Optional[str] = None,
    ) -> ImageToVideoResult:
        """生成视频"""
        config = config or ImageToVideoConfig()
        
        validation_data = {
            "duration": config.duration,
            "fps": config.fps,
            "width": config.width,
            "height": config.height,
        }
        
        report = self.validator.validate(
            function_type=ModelFunctionType.IMAGE_TO_VIDEO,
            data=validation_data,
            touch_point=TouchPoint.PRE_PROCESSING,
        )
        
        if not report.overall_passed:
            return ImageToVideoResult(
                success=False,
                error_message=f"验证失败: {'; '.join(report.errors)}",
            )
        
        try:
            result = self._execute_generation(image_path, config, model_id)
            
            post_report = self.validator.validate(
                function_type=ModelFunctionType.IMAGE_TO_VIDEO,
                data=result.__dict__,
                touch_point=TouchPoint.RESULT_DELIVERY,
            )
            
            if not post_report.overall_passed:
                result.success = False
                result.error_message = f"输出验证失败: {'; '.join(post_report.errors)}"
            
            return result
        except Exception as e:
            logger.error(f"图生视频生成失败: {str(e)}")
            return ImageToVideoResult(
                success=False,
                error_message=str(e),
            )
    
    def _execute_generation(
        self,
        image_path: str,
        config: ImageToVideoConfig,
        model_id: Optional[str],
    ) -> ImageToVideoResult:
        """执行视频生成"""
        logger.info(f"开始生成视频: {image_path}, 时长={config.duration}s, FPS={config.fps}")
        
        result = ImageToVideoResult(
            success=True,
            duration=config.duration,
            fps=config.fps,
            resolution=(config.width or 1024, config.height or 768),
            metadata={
                "motion_type": config.motion_type.value,
                "motion_strength": config.motion_strength,
                "consistency_level": config.consistency_level,
                "seed": config.seed,
            },
        )
        
        return result
    
    def register_model(self, model_id: str, model: Any) -> None:
        """注册模型"""
        self._models[model_id] = model
        logger.info(f"注册图生视频模型: {model_id}")
    
    def list_available_models(self) -> List[str]:
        """列出可用模型"""
        return list(self._models.keys())
