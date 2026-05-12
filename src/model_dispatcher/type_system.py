"""模型类型系统 - 提供统一的类型定义和兼容性处理"""

from enum import Enum
from typing import Any, TypeVar, Generic, Optional, Union, Dict, List
from pydantic import BaseModel, field_validator, ValidationError
import logging

logger = logging.getLogger("hydraflow.type_system")

# 统一的模型功能类型
class ModelFunctionType(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    TEXT_TO_VIDEO = "text_to_video"
    TEXT_TO_AUDIO = "text_to_audio"
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_UPSCALE = "image_upscale"
    IMAGE_EDIT = "image_edit"
    IMAGE_TO_VIDEO = "image_to_video"
    IMAGE_STYLE_TRANSFER = "image_style_transfer"
    IMAGE_FORMAT_CONVERT = "image_format_convert"
    VIDEO_STYLE_TRANSFER = "video_style_transfer"
    VIDEO_FORMAT_CONVERT = "video_format_convert"
    AUDIO_STYLE_TRANSFER = "audio_style_transfer"
    AUDIO_FORMAT_CONVERT = "audio_format_convert"
    IMAGE_TO_AUDIO = "image_to_audio"
    AUDIO_TO_TEXT = "audio_to_text"
    VIDEO_TO_AUDIO = "video_to_audio"
    VIDEO_TO_TEXT = "video_to_text"
    IMAGE_TO_TEXT = "image_to_text"
    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"
    SCRIPT_TO_AUDIO = "script_to_audio"
    AUDIO_TO_VIDEO = "audio_to_video"
    AV_FUSION = "av_fusion"
    SCENE_GENERATION = "scene_generation"
    CHARACTER_VOICEOVER = "character_voiceover"
    DUBBING = "dubbing"
    FOLEY = "foley"
    BACKGROUND_MUSIC = "background_music"
    SOUND_DESIGN = "sound_design"
    UNKNOWN = "unknown"

# 模型来源类型
class ModelSourceType(str, Enum):
    LOCAL = "local"
    API = "api"

# 模型分类
class ModelCategory(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    CODE = "code"
    UPSCALER = "upscaler"
    GENERAL = "general"

# 意图到功能类型的映射
INTENT_TO_FUNCTION: Dict[str, ModelFunctionType] = {
    "image_generation": ModelFunctionType.TEXT_TO_IMAGE,
    "image_edit": ModelFunctionType.IMAGE_EDIT,
    "image_upscale": ModelFunctionType.IMAGE_UPSCALE,
    "video_generation": ModelFunctionType.TEXT_TO_VIDEO,
    "audio_generation": ModelFunctionType.TEXT_TO_AUDIO,
    "text_generation": ModelFunctionType.TEXT_GENERATION,
    "code_generation": ModelFunctionType.CODE_GENERATION,
    "general": ModelFunctionType.TEXT_GENERATION,
    "image_to_video": ModelFunctionType.IMAGE_TO_VIDEO,
    "img2vid": ModelFunctionType.IMAGE_TO_VIDEO,
    "image_style_transfer": ModelFunctionType.IMAGE_STYLE_TRANSFER,
    "style_transfer": ModelFunctionType.IMAGE_STYLE_TRANSFER,
    "image_format_convert": ModelFunctionType.IMAGE_FORMAT_CONVERT,
    "format_convert": ModelFunctionType.IMAGE_FORMAT_CONVERT,
    "video_style_transfer": ModelFunctionType.VIDEO_STYLE_TRANSFER,
    "video_format_convert": ModelFunctionType.VIDEO_FORMAT_CONVERT,
    "audio_style_transfer": ModelFunctionType.AUDIO_STYLE_TRANSFER,
    "audio_format_convert": ModelFunctionType.AUDIO_FORMAT_CONVERT,
    "image_to_audio": ModelFunctionType.IMAGE_TO_AUDIO,
    "audio_to_text": ModelFunctionType.AUDIO_TO_TEXT,
    "asr": ModelFunctionType.AUDIO_TO_TEXT,
    "speech_to_text": ModelFunctionType.AUDIO_TO_TEXT,
    "video_to_audio": ModelFunctionType.VIDEO_TO_AUDIO,
    "video_to_text": ModelFunctionType.VIDEO_TO_TEXT,
    "image_to_text": ModelFunctionType.IMAGE_TO_TEXT,
    "ocr": ModelFunctionType.IMAGE_TO_TEXT,
    "text_to_3d": ModelFunctionType.TEXT_TO_3D,
    "image_to_3d": ModelFunctionType.IMAGE_TO_3D,
    "script_to_audio": ModelFunctionType.SCRIPT_TO_AUDIO,
    "audio_to_video": ModelFunctionType.AUDIO_TO_VIDEO,
    "av_fusion": ModelFunctionType.AV_FUSION,
    "scene_generation": ModelFunctionType.SCENE_GENERATION,
    "character_voiceover": ModelFunctionType.CHARACTER_VOICEOVER,
    "dubbing": ModelFunctionType.DUBBING,
    "foley": ModelFunctionType.FOLEY,
    "background_music": ModelFunctionType.BACKGROUND_MUSIC,
    "sound_design": ModelFunctionType.SOUND_DESIGN,
}

# 功能类型到分类的映射
FUNCTION_TO_CATEGORY: Dict[ModelFunctionType, ModelCategory] = {
    ModelFunctionType.TEXT_TO_IMAGE: ModelCategory.IMAGE,
    ModelFunctionType.IMAGE_EDIT: ModelCategory.IMAGE,
    ModelFunctionType.IMAGE_UPSCALE: ModelCategory.UPSCALER,
    ModelFunctionType.TEXT_TO_VIDEO: ModelCategory.VIDEO,
    ModelFunctionType.TEXT_TO_AUDIO: ModelCategory.AUDIO,
    ModelFunctionType.TEXT_GENERATION: ModelCategory.TEXT,
    ModelFunctionType.CODE_GENERATION: ModelCategory.CODE,
    ModelFunctionType.IMAGE_TO_VIDEO: ModelCategory.VIDEO,
    ModelFunctionType.IMAGE_STYLE_TRANSFER: ModelCategory.IMAGE,
    ModelFunctionType.IMAGE_FORMAT_CONVERT: ModelCategory.IMAGE,
    ModelFunctionType.VIDEO_STYLE_TRANSFER: ModelCategory.VIDEO,
    ModelFunctionType.VIDEO_FORMAT_CONVERT: ModelCategory.VIDEO,
    ModelFunctionType.AUDIO_STYLE_TRANSFER: ModelCategory.AUDIO,
    ModelFunctionType.AUDIO_FORMAT_CONVERT: ModelCategory.AUDIO,
    ModelFunctionType.IMAGE_TO_AUDIO: ModelCategory.AUDIO,
    ModelFunctionType.AUDIO_TO_TEXT: ModelCategory.TEXT,
    ModelFunctionType.VIDEO_TO_AUDIO: ModelCategory.AUDIO,
    ModelFunctionType.VIDEO_TO_TEXT: ModelCategory.TEXT,
    ModelFunctionType.IMAGE_TO_TEXT: ModelCategory.TEXT,
    ModelFunctionType.TEXT_TO_3D: ModelCategory.GENERAL,
    ModelFunctionType.IMAGE_TO_3D: ModelCategory.GENERAL,
    ModelFunctionType.SCRIPT_TO_AUDIO: ModelCategory.AUDIO,
    ModelFunctionType.AUDIO_TO_VIDEO: ModelCategory.VIDEO,
    ModelFunctionType.AV_FUSION: ModelCategory.GENERAL,
    ModelFunctionType.SCENE_GENERATION: ModelCategory.VIDEO,
    ModelFunctionType.CHARACTER_VOICEOVER: ModelCategory.AUDIO,
    ModelFunctionType.DUBBING: ModelCategory.AUDIO,
    ModelFunctionType.FOLEY: ModelCategory.AUDIO,
    ModelFunctionType.BACKGROUND_MUSIC: ModelCategory.AUDIO,
    ModelFunctionType.SOUND_DESIGN: ModelCategory.AUDIO,
    ModelFunctionType.UNKNOWN: ModelCategory.GENERAL,
}

# 类型别名映射
TYPE_ALIASES: Dict[str, ModelFunctionType] = {
    "txt2img": ModelFunctionType.TEXT_TO_IMAGE,
    "text2image": ModelFunctionType.TEXT_TO_IMAGE,
    "image": ModelFunctionType.TEXT_TO_IMAGE,
    "txt2vid": ModelFunctionType.TEXT_TO_VIDEO,
    "text2video": ModelFunctionType.TEXT_TO_VIDEO,
    "video": ModelFunctionType.TEXT_TO_VIDEO,
    "txt2audio": ModelFunctionType.TEXT_TO_AUDIO,
    "text2audio": ModelFunctionType.TEXT_TO_AUDIO,
    "tts": ModelFunctionType.TEXT_TO_AUDIO,
    "upscale": ModelFunctionType.IMAGE_UPSCALE,
    "esrgan": ModelFunctionType.IMAGE_UPSCALE,
    "edit": ModelFunctionType.IMAGE_EDIT,
    "inpaint": ModelFunctionType.IMAGE_EDIT,
    "outpaint": ModelFunctionType.IMAGE_EDIT,
    "llm": ModelFunctionType.TEXT_GENERATION,
    "chat": ModelFunctionType.TEXT_GENERATION,
    "completion": ModelFunctionType.TEXT_GENERATION,
    "code": ModelFunctionType.CODE_GENERATION,
    "coder": ModelFunctionType.CODE_GENERATION,
    "img2vid": ModelFunctionType.IMAGE_TO_VIDEO,
    "image2video": ModelFunctionType.IMAGE_TO_VIDEO,
    "style_transfer": ModelFunctionType.IMAGE_STYLE_TRANSFER,
    "img_style": ModelFunctionType.IMAGE_STYLE_TRANSFER,
    "img_convert": ModelFunctionType.IMAGE_FORMAT_CONVERT,
    "image_convert": ModelFunctionType.IMAGE_FORMAT_CONVERT,
    "vid_style": ModelFunctionType.VIDEO_STYLE_TRANSFER,
    "vid_convert": ModelFunctionType.VIDEO_FORMAT_CONVERT,
    "video_convert": ModelFunctionType.VIDEO_FORMAT_CONVERT,
    "aud_style": ModelFunctionType.AUDIO_STYLE_TRANSFER,
    "aud_convert": ModelFunctionType.AUDIO_FORMAT_CONVERT,
    "audio_convert": ModelFunctionType.AUDIO_FORMAT_CONVERT,
    "img2audio": ModelFunctionType.IMAGE_TO_AUDIO,
    "audio2text": ModelFunctionType.AUDIO_TO_TEXT,
    "asr": ModelFunctionType.AUDIO_TO_TEXT,
    "stt": ModelFunctionType.AUDIO_TO_TEXT,
    "vid2audio": ModelFunctionType.VIDEO_TO_AUDIO,
    "vid2text": ModelFunctionType.VIDEO_TO_TEXT,
    "img2text": ModelFunctionType.IMAGE_TO_TEXT,
    "ocr": ModelFunctionType.IMAGE_TO_TEXT,
    "txt23d": ModelFunctionType.TEXT_TO_3D,
    "img23d": ModelFunctionType.IMAGE_TO_3D,
    "script2audio": ModelFunctionType.SCRIPT_TO_AUDIO,
    "audio2video": ModelFunctionType.AUDIO_TO_VIDEO,
    "voiceover": ModelFunctionType.CHARACTER_VOICEOVER,
    "character_voice": ModelFunctionType.CHARACTER_VOICEOVER,
    "bgm": ModelFunctionType.BACKGROUND_MUSIC,
}

class ModelConfig(BaseModel):
    """统一的模型配置结构"""
    type: ModelSourceType
    model_type: ModelFunctionType
    
    # API模型字段
    api_url: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None
    cost_per_call: Optional[float] = None
    
    # 本地模型字段
    file_size_mb: Optional[int] = None
    vram_required_mb: Optional[int] = None
    quantization: Optional[str] = None
    method: Optional[str] = None
    sample_rate: Optional[int] = None
    
    @field_validator('type', mode='before')
    def validate_type(cls, v):
        if isinstance(v, str):
            return ModelSourceType(v.lower())
        return v
    
    @field_validator('model_type', mode='before')
    def validate_model_type(cls, v):
        if isinstance(v, str):
            v_lower = v.lower()
            # 尝试别名映射
            if v_lower in TYPE_ALIASES:
                return TYPE_ALIASES[v_lower]
            # 尝试直接匹配
            try:
                return ModelFunctionType(v_lower)
            except ValueError:
                logger.warning(f"未知模型类型: {v}, 使用默认值")
                return ModelFunctionType.UNKNOWN
        return v

class ModelInfo(BaseModel):
    """统一的模型信息结构"""
    id: str
    name: str
    category: ModelCategory
    function_type: ModelFunctionType
    source: ModelSourceType
    path: Optional[str] = None
    config: Optional[ModelConfig] = None
    tags: Optional[List[str]] = None
    enabled: bool = True
    version: Optional[str] = None
    
    @field_validator('category', mode='before')
    def validate_category(cls, v):
        if isinstance(v, str):
            return ModelCategory(v.lower())
        return v
    
    @field_validator('source', mode='before')
    def validate_source(cls, v):
        if isinstance(v, str):
            return ModelSourceType(v.lower())
        return v

class TypeCompatibilityManager:
    """类型兼容性管理器"""
    
    def __init__(self):
        self._intent_cache: Dict[str, ModelFunctionType] = {}
    
    def resolve_intent(self, intent: str) -> ModelFunctionType:
        """解析意图到功能类型"""
        if intent in self._intent_cache:
            return self._intent_cache[intent]
        
        intent_lower = intent.lower()
        
        # 0. 首先尝试直接匹配功能类型
        try:
            result = ModelFunctionType(intent_lower)
            self._intent_cache[intent] = result
            return result
        except ValueError:
            pass
        
        # 1. 直接映射（意图到功能）
        if intent_lower in INTENT_TO_FUNCTION:
            result = INTENT_TO_FUNCTION[intent_lower]
            self._intent_cache[intent] = result
            return result
        
        # 2. 尝试类型别名
        if intent_lower in TYPE_ALIASES:
            result = TYPE_ALIASES[intent_lower]
            self._intent_cache[intent] = result
            return result
        
        # 3. 模糊匹配
        for key, func_type in INTENT_TO_FUNCTION.items():
            if key in intent_lower or intent_lower in key:
                result = func_type
                self._intent_cache[intent] = result
                return result
        
        logger.warning(f"无法解析意图类型: {intent}")
        self._intent_cache[intent] = ModelFunctionType.UNKNOWN
        return ModelFunctionType.UNKNOWN
    
    def resolve_category(self, function_type: ModelFunctionType) -> ModelCategory:
        """从功能类型获取分类"""
        return FUNCTION_TO_CATEGORY.get(function_type, ModelCategory.GENERAL)
    
    def intent_to_category(self, intent: str) -> ModelCategory:
        """意图直接映射到分类"""
        func_type = self.resolve_intent(intent)
        return self.resolve_category(func_type)
    
    def normalize_model_config(self, raw_config: Dict[str, Any]) -> Optional[ModelConfig]:
        """标准化模型配置"""
        try:
            # 处理配置中的类型字段混乱
            normalized = {}
            
            # 统一 type 字段
            if 'type' in raw_config:
                normalized['type'] = raw_config['type']
            elif 'source' in raw_config:
                normalized['type'] = raw_config['source']
            
            # 统一 model_type 字段
            if 'model_type' in raw_config:
                normalized['model_type'] = raw_config['model_type']
            elif 'type' in raw_config and raw_config['type'] != 'api' and raw_config['type'] != 'local':
                normalized['model_type'] = raw_config['type']
            elif 'function' in raw_config:
                normalized['model_type'] = raw_config['function']
            
            # 复制其他字段
            for key in ['api_url', 'api_base', 'model', 'cost_per_call',
                        'file_size_mb', 'vram_required_mb', 'quantization',
                        'method', 'sample_rate']:
                if key in raw_config:
                    normalized[key] = raw_config[key]
            
            return ModelConfig(**normalized)
        except ValidationError as e:
            logger.error(f"模型配置标准化失败: {e}")
            return None
    
    def normalize_model_info(self, model_id: str, category: str, raw_info: Dict[str, Any]) -> Optional[ModelInfo]:
        """标准化模型信息"""
        try:
            # 解析功能类型
            func_type = ModelFunctionType.UNKNOWN
            if 'type' in raw_info:
                func_type = self.resolve_intent(raw_info['type'])
            elif 'model_type' in raw_info:
                func_type = self.resolve_intent(raw_info['model_type'])
            
            # 标准化配置
            config = None
            if 'config' in raw_info:
                config = self.normalize_model_config(raw_info['config'])
            
            return ModelInfo(
                id=model_id,
                name=raw_info.get('name', model_id),
                category=ModelCategory(category.lower()),
                function_type=func_type,
                source=ModelSourceType(raw_info.get('source', 'local').lower()),
                path=raw_info.get('path'),
                config=config,
                tags=raw_info.get('tags'),
                enabled=raw_info.get('enabled', True),
                version=raw_info.get('version'),
            )
        except Exception as e:
            logger.error(f"模型信息标准化失败 {model_id}: {e}")
            return None
    
    def validate_model_for_intent(self, model_info: ModelInfo, intent: str) -> bool:
        """验证模型是否适合处理指定意图"""
        required_func = self.resolve_intent(intent)
        
        # 完全匹配
        if model_info.function_type == required_func:
            return True
        
        # 兼容匹配：文本模型可以处理代码生成
        if required_func == ModelFunctionType.CODE_GENERATION and \
           model_info.function_type == ModelFunctionType.TEXT_GENERATION:
            return True
        
        # 兼容匹配：通用模型可以处理任何意图
        if model_info.function_type == ModelFunctionType.TEXT_GENERATION and \
           required_func in [ModelFunctionType.TEXT_GENERATION, ModelFunctionType.CODE_GENERATION]:
            return True
        
        logger.debug(f"模型 {model_info.id} 不兼容意图 {intent}: "
                     f"模型类型={model_info.function_type}, 需求类型={required_func}")
        return False
    
    def get_compatible_models(self, intent: str, models: List[ModelInfo]) -> List[ModelInfo]:
        """获取与意图兼容的模型列表"""
        return [m for m in models if self.validate_model_for_intent(m, intent)]
    
    def get_type_hierarchy(self) -> Dict[str, Any]:
        """获取类型层次结构信息"""
        return {
            "intents": {k: v.value for k, v in INTENT_TO_FUNCTION.items()},
            "functions": {v.value: FUNCTION_TO_CATEGORY[v].value for v in ModelFunctionType},
            "categories": [c.value for c in ModelCategory],
            "sources": [s.value for s in ModelSourceType],
        }

# ==================== 生成类一致性验证系统 ====================

from enum import Enum as PyEnum
from dataclasses import dataclass, field
from typing import Callable, Any, Set, Tuple, Optional


class ValidationRuleType(str, PyEnum):
    """验证规则类型"""
    INPUT_FORMAT = "input_format"
    OUTPUT_FORMAT = "output_format"
    RESOURCE_CONSTRAINT = "resource_constraint"
    QUALITY_STANDARD = "quality_standard"
    SAFETY_CHECK = "safety_check"
    PERFORMANCE_BOUND = "performance_bound"
    COMPATIBILITY = "compatibility"


class TouchPoint(str, PyEnum):
    """验证触点"""
    PRE_PROCESSING = "pre_processing"
    MODEL_INPUT = "model_input"
    MODEL_EXECUTION = "model_execution"
    MODEL_OUTPUT = "model_output"
    POST_PROCESSING = "post_processing"
    RESULT_DELIVERY = "result_delivery"


class BoundaryType(str, PyEnum):
    """边界类型"""
    HARD_BOUNDARY = "hard_boundary"
    SOFT_BOUNDARY = "soft_boundary"
    ADVISORY_BOUNDARY = "advisory_boundary"


@dataclass
class ValidationRule:
    """验证规则"""
    rule_id: str
    rule_type: ValidationRuleType
    name: str
    description: str
    touch_points: Set[TouchPoint]
    boundary_type: BoundaryType
    validator: Callable[[Any], Tuple[bool, Optional[str]]]
    priority: int = 100
    enabled: bool = True


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    rule_id: str
    rule_name: str
    touch_point: TouchPoint
    message: Optional[str] = None
    details: Any = None


@dataclass
class ConsistencyValidationReport:
    """一致性验证报告"""
    function_type: ModelFunctionType
    overall_passed: bool
    results: List[ValidationResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_result(self, result: ValidationResult) -> None:
        """添加验证结果"""
        self.results.append(result)
        if not result.passed:
            self.errors.append(f"{result.rule_name}: {result.message}")
        elif result.message:
            self.warnings.append(f"{result.rule_name}: {result.message}")
    
    def update_overall(self) -> None:
        """更新整体状态"""
        hard_errors = [r for r in self.results if not r.passed]
        self.overall_passed = len(hard_errors) == 0


class GenerationConsistencyValidator:
    """生成类一致性验证器"""
    
    def __init__(self):
        self._rules: Dict[ModelFunctionType, List[ValidationRule]] = {}
        self._register_default_rules()
    
    def _register_default_rules(self) -> None:
        """注册默认验证规则"""
        for func_type in ModelFunctionType:
            self._rules[func_type] = []
        
        self._register_image_rules()
        self._register_video_rules()
        self._register_audio_rules()
        self._register_text_rules()
    
    def _register_image_rules(self) -> None:
        """注册图片相关规则"""
        image_types = [
            ModelFunctionType.TEXT_TO_IMAGE,
            ModelFunctionType.IMAGE_EDIT,
            ModelFunctionType.IMAGE_UPSCALE,
            ModelFunctionType.IMAGE_STYLE_TRANSFER,
            ModelFunctionType.IMAGE_FORMAT_CONVERT,
            ModelFunctionType.IMAGE_TO_VIDEO,
            ModelFunctionType.IMAGE_TO_AUDIO,
            ModelFunctionType.IMAGE_TO_TEXT,
            ModelFunctionType.IMAGE_TO_3D,
        ]
        
        for func_type in image_types:
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_input_dim",
                rule_type=ValidationRuleType.INPUT_FORMAT,
                name="输入尺寸验证",
                description="验证图片输入尺寸是否在有效范围内",
                touch_points={TouchPoint.PRE_PROCESSING, TouchPoint.MODEL_INPUT},
                boundary_type=BoundaryType.HARD_BOUNDARY,
                validator=lambda data: self._validate_image_dimensions(data),
                priority=100,
            ))
            
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_safety_check",
                rule_type=ValidationRuleType.SAFETY_CHECK,
                name="内容安全检查",
                description="检查生成内容是否符合安全标准",
                touch_points={TouchPoint.MODEL_OUTPUT, TouchPoint.POST_PROCESSING},
                boundary_type=BoundaryType.HARD_BOUNDARY,
                validator=lambda data: (True, None),
                priority=90,
            ))
    
    def _register_video_rules(self) -> None:
        """注册视频相关规则"""
        video_types = [
            ModelFunctionType.TEXT_TO_VIDEO,
            ModelFunctionType.IMAGE_TO_VIDEO,
            ModelFunctionType.VIDEO_STYLE_TRANSFER,
            ModelFunctionType.VIDEO_FORMAT_CONVERT,
            ModelFunctionType.VIDEO_TO_AUDIO,
            ModelFunctionType.VIDEO_TO_TEXT,
        ]
        
        for func_type in video_types:
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_duration",
                rule_type=ValidationRuleType.PERFORMANCE_BOUND,
                name="视频时长验证",
                description="验证视频时长是否在有效范围内",
                touch_points={TouchPoint.MODEL_INPUT, TouchPoint.MODEL_EXECUTION},
                boundary_type=BoundaryType.SOFT_BOUNDARY,
                validator=lambda data: self._validate_video_duration(data),
                priority=95,
            ))
            
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_fps",
                rule_type=ValidationRuleType.QUALITY_STANDARD,
                name="帧率验证",
                description="验证视频帧率是否符合质量标准",
                touch_points={TouchPoint.PRE_PROCESSING, TouchPoint.RESULT_DELIVERY},
                boundary_type=BoundaryType.ADVISORY_BOUNDARY,
                validator=lambda data: self._validate_video_fps(data),
                priority=80,
            ))
    
    def _register_audio_rules(self) -> None:
        """注册音频相关规则"""
        audio_types = [
            ModelFunctionType.TEXT_TO_AUDIO,
            ModelFunctionType.IMAGE_TO_AUDIO,
            ModelFunctionType.VIDEO_TO_AUDIO,
            ModelFunctionType.AUDIO_STYLE_TRANSFER,
            ModelFunctionType.AUDIO_FORMAT_CONVERT,
            ModelFunctionType.AUDIO_TO_TEXT,
        ]
        
        for func_type in audio_types:
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_sample_rate",
                rule_type=ValidationRuleType.INPUT_FORMAT,
                name="采样率验证",
                description="验证音频采样率是否符合要求",
                touch_points={TouchPoint.PRE_PROCESSING, TouchPoint.MODEL_INPUT},
                boundary_type=BoundaryType.HARD_BOUNDARY,
                validator=lambda data: self._validate_audio_sample_rate(data),
                priority=95,
            ))
            
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_bit_depth",
                rule_type=ValidationRuleType.QUALITY_STANDARD,
                name="位深度验证",
                description="验证音频位深度是否符合质量标准",
                touch_points={TouchPoint.RESULT_DELIVERY},
                boundary_type=BoundaryType.SOFT_BOUNDARY,
                validator=lambda data: self._validate_audio_bit_depth(data),
                priority=85,
            ))
    
    def _register_text_rules(self) -> None:
        """注册文本相关规则"""
        text_types = [
            ModelFunctionType.TEXT_GENERATION,
            ModelFunctionType.CODE_GENERATION,
            ModelFunctionType.AUDIO_TO_TEXT,
            ModelFunctionType.VIDEO_TO_TEXT,
            ModelFunctionType.IMAGE_TO_TEXT,
        ]
        
        for func_type in text_types:
            self._add_rule(func_type, ValidationRule(
                rule_id=f"{func_type.value}_length",
                rule_type=ValidationRuleType.PERFORMANCE_BOUND,
                name="文本长度验证",
                description="验证文本长度是否在有效范围内",
                touch_points={TouchPoint.PRE_PROCESSING, TouchPoint.MODEL_OUTPUT},
                boundary_type=BoundaryType.SOFT_BOUNDARY,
                validator=lambda data: self._validate_text_length(data),
                priority=90,
            ))
    
    def _add_rule(self, func_type: ModelFunctionType, rule: ValidationRule) -> None:
        """添加验证规则"""
        if func_type not in self._rules:
            self._rules[func_type] = []
        self._rules[func_type].append(rule)
        self._rules[func_type].sort(key=lambda r: r.priority, reverse=True)
    
    def _validate_image_dimensions(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证图片尺寸"""
        if isinstance(data, dict):
            width = data.get("width", 1024)
            height = data.get("height", 1024)
            if width < 64 or width > 4096 or height < 64 or height > 4096:
                return False, f"尺寸 {width}x{height} 超出有效范围 (64-4096)"
            return True, None
        return True, None
    
    def _validate_video_duration(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证视频时长"""
        if isinstance(data, dict):
            duration = data.get("duration", 5)
            if duration <= 0:
                return False, "视频时长必须大于0"
            if duration > 300:
                return False, f"视频时长 {duration}秒 超出建议范围 (最大300秒)"
            return True, None
        return True, None
    
    def _validate_video_fps(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证视频帧率"""
        if isinstance(data, dict):
            fps = data.get("fps", 24)
            if fps < 12:
                return False, f"帧率 {fps} 较低，可能影响观看体验"
            if fps > 60:
                return False, f"帧率 {fps} 较高，可能增加计算成本"
            return True, None
        return True, None
    
    def _validate_audio_sample_rate(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证音频采样率"""
        if isinstance(data, dict):
            sample_rate = data.get("sample_rate", 44100)
            valid_rates = [8000, 16000, 22050, 44100, 48000]
            if sample_rate not in valid_rates:
                return False, f"采样率 {sample_rate} 不在支持列表中"
            return True, None
        return True, None
    
    def _validate_audio_bit_depth(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证音频位深度"""
        if isinstance(data, dict):
            bit_depth = data.get("bit_depth", 16)
            if bit_depth < 8 or bit_depth > 32:
                return False, f"位深度 {bit_depth} 超出有效范围 (8-32)"
            return True, None
        return True, None
    
    def _validate_text_length(self, data: Any) -> Tuple[bool, Optional[str]]:
        """验证文本长度"""
        if isinstance(data, dict):
            max_length = data.get("max_length", 2048)
            if max_length < 1:
                return False, "文本长度必须大于0"
            if max_length > 32768:
                return False, f"文本长度 {max_length} 超出建议范围"
            return True, None
        return True, None
    
    def validate(
        self,
        function_type: ModelFunctionType,
        data: Any,
        touch_point: Optional[TouchPoint] = None,
    ) -> ConsistencyValidationReport:
        """执行验证"""
        report = ConsistencyValidationReport(
            function_type=function_type,
            overall_passed=True,
        )
        
        rules = self._rules.get(function_type, [])
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            if touch_point and touch_point not in rule.touch_points:
                continue
            
            for tp in rule.touch_points:
                if touch_point and tp != touch_point:
                    continue
                
                try:
                    passed, message = rule.validator(data)
                    result = ValidationResult(
                        passed=passed,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        touch_point=tp,
                        message=message,
                    )
                    report.add_result(result)
                except Exception as e:
                    result = ValidationResult(
                        passed=False,
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        touch_point=tp,
                        message=f"验证执行失败: {str(e)}",
                    )
                    report.add_result(result)
        
        report.update_overall()
        return report
    
    def add_custom_rule(
        self,
        function_type: ModelFunctionType,
        rule: ValidationRule,
    ) -> None:
        """添加自定义验证规则"""
        self._add_rule(func_type=function_type, rule=rule)
    
    def get_rules(
        self,
        function_type: Optional[ModelFunctionType] = None,
        touch_point: Optional[TouchPoint] = None,
        rule_type: Optional[ValidationRuleType] = None,
    ) -> List[ValidationRule]:
        """获取验证规则"""
        result = []
        types = [function_type] if function_type else list(self._rules.keys())
        
        for ft in types:
            for rule in self._rules.get(ft, []):
                if touch_point and touch_point not in rule.touch_points:
                    continue
                if rule_type and rule.rule_type != rule_type:
                    continue
                result.append(rule)
        
        return result
    
    def get_boundary_definitions(self) -> Dict[str, Any]:
        """获取边界定义"""
        return {
            BoundaryType.HARD_BOUNDARY: {
                "description": "硬边界：违反则任务失败",
                "severity": "critical",
                "examples": ["输入格式错误", "资源不足"]
            },
            BoundaryType.SOFT_BOUNDARY: {
                "description": "软边界：违反可继续但有警告",
                "severity": "warning",
                "examples": ["超出建议尺寸", "性能下降"]
            },
            BoundaryType.ADVISORY_BOUNDARY: {
                "description": "建议边界：最佳实践提示",
                "severity": "info",
                "examples": ["质量优化建议"]
            }
        }


# ==================== 全局单例 ====================

_type_manager = None
_consistency_validator = None


def get_type_manager() -> TypeCompatibilityManager:
    """获取类型兼容性管理器实例"""
    global _type_manager
    if _type_manager is None:
        _type_manager = TypeCompatibilityManager()
    return _type_manager


def get_consistency_validator() -> GenerationConsistencyValidator:
    """获取生成类一致性验证器实例"""
    global _consistency_validator
    if _consistency_validator is None:
        _consistency_validator = GenerationConsistencyValidator()
    return _consistency_validator
