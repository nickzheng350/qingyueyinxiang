"""模型调度器 - 路由请求到合适的模型"""

import logging
from typing import Any, List, Dict, Optional

from src.core.config import get_config
from src.core.exceptions import ModelNotFoundError
from .type_system import get_type_manager, ModelInfo, ModelCategory, ModelFunctionType, ModelSourceType

logger = logging.getLogger("hydraflow.model_dispatcher")

# 延迟导入避免循环依赖
def _get_ai_client():
    from src.api.ai_client import get_ai_client_manager
    return get_ai_client_manager()


class ModelDispatcher:
    _instance: "ModelDispatcher | None" = None

    def __new__(cls) -> "ModelDispatcher":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._type_manager = get_type_manager()
        self._loaded_models: Dict[str, ModelInfo] = {}
        self._model_status: Dict[str, str] = {}
        self._load_model_registry()

    def _load_model_registry(self) -> None:
        """加载模型注册表并标准化"""
        config = get_config()
        models_config = config.models_config
        models = models_config.get("models", {})
        for category, model_list in models.items():
            if isinstance(model_list, dict):
                for model_id, model_info in model_list.items():
                    if isinstance(model_info, dict):
                        normalized = self._type_manager.normalize_model_info(
                            model_id, category, model_info
                        )
                        if normalized:
                            self._loaded_models[model_id] = normalized
                            self._model_status[model_id] = "registered"
                            logger.debug(f"注册模型: {model_id} ({category})")
                        else:
                            self._model_status[model_id] = "invalid"
                            logger.warning(f"模型配置无效: {model_id}")

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息（向后兼容的字典格式）"""
        if model_id in self._loaded_models:
            model_info = self._loaded_models[model_id]
            return self._model_info_to_dict(model_info)
        
        # 尝试从配置中查找（兼容旧逻辑）
        config = get_config()
        models_config = config.models_config
        models = models_config.get("models", {})
        for category, model_list in models.items():
            if isinstance(model_list, dict) and model_id in model_list:
                model_info = model_list[model_id]
                if isinstance(model_info, dict):
                    normalized = self._type_manager.normalize_model_info(
                        model_id, category, model_info
                    )
                    if normalized:
                        self._loaded_models[model_id] = normalized
                        return self._model_info_to_dict(normalized)
                    return {"category": category, **model_info}
        raise ModelNotFoundError(model_id)

    def _model_info_to_dict(self, model_info: ModelInfo) -> Dict[str, Any]:
        """将标准化的 ModelInfo 转换为字典格式（向后兼容）"""
        result = {
            "id": model_info.id,
            "name": model_info.name,
            "category": model_info.category.value,
            "function_type": model_info.function_type.value,
            "source": model_info.source.value,
            "enabled": model_info.enabled,
        }
        if model_info.path:
            result["path"] = model_info.path
        if model_info.tags:
            result["tags"] = model_info.tags
        if model_info.version:
            result["version"] = model_info.version
        if model_info.config:
            result["config"] = model_info.config.dict(exclude_none=True)
        return result

    def list_models(
        self, 
        category: Optional[str] = None, 
        source: Optional[str] = None,
        function_type: Optional[str] = None,
        by_intent: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出模型，支持多维度筛选
        
        参数:
            category: 按模型分类筛选（如 image, text, video）
            source: 按模型来源筛选（local, api）
            function_type: 按功能类型精确匹配筛选（如 text_to_image, text_generation）
            by_intent: 按意图筛选，会自动验证模型兼容性（如 image_generation, code_generation）
        """
        result = []
        for model_id, model_info in self._loaded_models.items():
            # 按分类筛选
            if category and model_info.category.value != category:
                continue
            # 按来源筛选
            if source and model_info.source.value != source:
                continue
            # 按功能类型精确匹配筛选
            if function_type and model_info.function_type.value != function_type:
                continue
            # 按意图筛选（通过兼容性验证）
            if by_intent and not self._type_manager.validate_model_for_intent(model_info, by_intent):
                continue
            result.append(self._model_info_to_dict(model_info))
        return result

    def select_model(
        self, 
        intent_type: str, 
        model_suggestions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """为意图选择最合适的模型"""
        # 1. 首先尝试用户指定的模型建议
        if model_suggestions:
            for model_id in model_suggestions:
                try:
                    model = self.get_model(model_id)
                    if model.get("enabled", True):
                        # 验证模型兼容性
                        model_info = self._loaded_models.get(model_id)
                        if model_info and self._type_manager.validate_model_for_intent(model_info, intent_type):
                            return {"id": model_id, **model}
                except ModelNotFoundError:
                    continue
        
        # 2. 使用类型系统解析意图并选择模型
        target_category = self._type_manager.intent_to_category(intent_type)
        available = self.list_models(category=target_category.value)
        
        # 3. 按兼容性排序：首选完全匹配的模型
        compatible_models = []
        fallback_models = []
        
        for model in available:
            model_info = self._loaded_models.get(model["id"])
            if model_info:
                if self._type_manager.validate_model_for_intent(model_info, intent_type):
                    compatible_models.append(model)
                elif model.get("enabled", True):
                    fallback_models.append(model)
        
        # 4. 返回兼容模型或降级模型
        for model in compatible_models:
            if model.get("enabled", True):
                return model
        if compatible_models:
            return compatible_models[0]
        
        # 5. 回退到其他类别
        fallback_categories = [ModelCategory.IMAGE, ModelCategory.TEXT, ModelCategory.CODE]
        for fb_cat in fallback_categories:
            if fb_cat == target_category:
                continue
            fb_models = self.list_models(category=fb_cat.value)
            for model in fb_models:
                if model.get("enabled", True):
                    return model
            if fb_models:
                return fb_models[0]
        
        raise ModelNotFoundError(f"无可用模型 (intent={intent_type}, category={target_category.value})")

    def generate_text(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        intent_type: str = "text_generation",
        model_suggestions: Optional[List[str]] = None,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """调用模型生成文本

        参数:
            prompt: 提示词
            model_id: 指定模型 ID
            intent_type: 意图类型（用于模型选择）
            model_suggestions: 模型建议列表
            system: 系统提示词
            max_tokens: 最大 token 数
            temperature: 温度参数

        返回:
            包含 content, provider, model, usage 等字段的字典
        """
        # 1. 选择模型
        if model_id:
            try:
                model_info = self.get_model(model_id)
            except ModelNotFoundError:
                selected = self.select_model(intent_type, model_suggestions)
                model_id = selected.get("id")
                model_info = selected
        else:
            selected = self.select_model(intent_type, model_suggestions)
            model_id = selected.get("id")
            model_info = selected

        if not model_id:
            return {
                "success": False,
                "error": "无可用模型",
                "content": "",
                "model": None,
            }

        # 2. 获取模型配置
        config = model_info.get("config", {})
        model_name = config.get("model") or model_id

        # 3. 调用 AI 客户端
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._async_generate(
                            prompt, model_name, model_id,
                            system, max_tokens, temperature, **kwargs
                        )
                    )
                    response = future.result()
            else:
                response = loop.run_until_complete(
                    self._async_generate(
                        prompt, model_name, model_id,
                        system, max_tokens, temperature, **kwargs
                    )
                )
        except RuntimeError:
            response = asyncio.run(
                self._async_generate(
                    prompt, model_name, model_id,
                    system, max_tokens, temperature, **kwargs
                )
            )

        return {
            "success": response.success,
            "error": response.error,
            "content": response.content,
            "provider": response.provider.value,
            "model": response.model,
            "usage": response.usage,
            "raw": response.raw,
        }

    async def _async_generate(
        self,
        prompt: str,
        model_name: str,
        model_id: str,
        system: Optional[str],
        max_tokens: int,
        temperature: float,
        **kwargs
    ):
        """异步生成文本"""
        from src.api.ai_client import AIProvider

        client_manager = _get_ai_client()

        model_lower = model_id.lower()
        provider = None
        if "gpt" in model_lower or "openai" in model_lower:
            provider = AIProvider.OPENAI
        elif "claude" in model_lower or "anthropic" in model_lower:
            provider = AIProvider.ANTHROPIC
        elif "qwen" in model_lower:
            provider = AIProvider.QWEN

        return await client_manager.generate(
            prompt=prompt,
            model=model_name,
            provider=provider,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def get_model_status(self, model_id: str) -> str:
        """获取模型状态"""
        return self._model_status.get(model_id, "unknown")

    def get_local_deployment_config(self, provider: str) -> Dict[str, Any]:
        """获取本地部署配置"""
        config = get_config()
        models_config = config.models_config
        deployments = models_config.get("local_deployment", {})
        return deployments.get(provider, {})

    def get_statistics(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        total = len(self._model_status)
        by_status: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        
        for model_id, status in self._model_status.items():
            by_status[status] = by_status.get(status, 0) + 1
            
            model_info = self._loaded_models.get(model_id)
            if model_info:
                by_category[model_info.category.value] = by_category.get(model_info.category.value, 0) + 1
                by_source[model_info.source.value] = by_source.get(model_info.source.value, 0) + 1
        
        return {
            "total_models": total,
            "by_status": by_status,
            "by_category": by_category,
            "by_source": by_source,
        }

    def validate_models(self) -> Dict[str, Any]:
        """验证所有模型的配置完整性"""
        results = {
            "valid": [],
            "invalid": [],
            "warnings": [],
        }
        
        for model_id, model_info in self._loaded_models.items():
            issues = []
            
            # 检查必需字段
            if not model_info.name:
                issues.append("缺少名称")
            if not model_info.path and model_info.source == ModelSourceType.LOCAL:
                issues.append("本地模型缺少路径")
            if model_info.source == ModelSourceType.API:
                config = model_info.config
                if config and not (config.api_url or config.api_base):
                    issues.append("API模型缺少API地址")
            
            # 检查VRAM需求（本地模型）
            if model_info.config and model_info.config.vram_required_mb:
                # 可以添加系统VRAM检查
                pass
            
            if issues:
                results["invalid"].append({
                    "model_id": model_id,
                    "issues": issues,
                })
            else:
                results["valid"].append(model_id)
        
        return results

    def get_type_info(self) -> Dict[str, Any]:
        """获取类型系统信息"""
        return self._type_manager.get_type_hierarchy()
