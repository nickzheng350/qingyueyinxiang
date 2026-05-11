"""模型调度器 - 路由请求到合适的模型"""

import logging
from typing import Any

from src.core.config import get_config
from src.core.exceptions import ModelNotFoundError

logger = logging.getLogger("hydraflow.model_dispatcher")


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
        self._loaded_models: dict[str, Any] = {}
        self._model_status: dict[str, str] = {}
        self._load_model_registry()

    def _load_model_registry(self) -> None:
        config = get_config()
        models_config = config.models_config
        models = models_config.get("models", {})
        for category, model_list in models.items():
            if isinstance(model_list, dict):
                for model_id, model_info in model_list.items():
                    if isinstance(model_info, dict):
                        self._model_status[model_id] = "registered"
                        logger.debug(f"注册模型: {model_id} ({category})")

    def get_model(self, model_id: str) -> dict[str, Any]:
        config = get_config()
        models_config = config.models_config
        models = models_config.get("models", {})
        for category, model_list in models.items():
            if isinstance(model_list, dict) and model_id in model_list:
                model_info = model_list[model_id]
                if isinstance(model_info, dict):
                    return model_info
        raise ModelNotFoundError(model_id)

    def list_models(self, category: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
        config = get_config()
        models_config = config.models_config
        models = models_config.get("models", {})
        result = []
        for cat, model_list in models.items():
            if category and cat != category:
                continue
            if isinstance(model_list, dict):
                for model_id, model_info in model_list.items():
                    if isinstance(model_info, dict):
                        entry = {"id": model_id, "category": cat, **model_info}
                        if source and model_info.get("source") != source:
                            continue
                        result.append(entry)
        return result

    def select_model(self, intent_type: str, model_suggestions: list[str] | None = None) -> dict[str, Any]:
        if model_suggestions:
            for model_id in model_suggestions:
                try:
                    model = self.get_model(model_id)
                    if model.get("enabled", True):
                        return {"id": model_id, **model}
                except ModelNotFoundError:
                    continue
        intent_to_category = {
            "image_generation": "image",
            "image_edit": "image",
            "image_upscale": "upscaler",
            "video_generation": "video",
            "audio_generation": "audio",
            "text_generation": "image",
            "code_generation": "image",
            "general": "image",
        }
        category = intent_to_category.get(intent_type, "image")
        available = self.list_models(category=category)
        for model in available:
            if model.get("enabled", True):
                return model
        if available:
            return available[0]
        raise ModelNotFoundError(f"无可用模型 (intent={intent_type}, category={category})")

    def get_model_status(self, model_id: str) -> str:
        return self._model_status.get(model_id, "unknown")

    def get_local_deployment_config(self, provider: str) -> dict[str, Any]:
        config = get_config()
        models_config = config.models_config
        deployments = models_config.get("local_deployment", {})
        return deployments.get(provider, {})

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._model_status)
        by_status: dict[str, int] = {}
        for status in self._model_status.values():
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total_models": total,
            "by_status": by_status,
        }
