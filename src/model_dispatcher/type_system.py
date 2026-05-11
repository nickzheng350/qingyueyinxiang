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

# 全局单例
_type_manager = None

def get_type_manager() -> TypeCompatibilityManager:
    """获取类型兼容性管理器实例"""
    global _type_manager
    if _type_manager is None:
        _type_manager = TypeCompatibilityManager()
    return _type_manager
