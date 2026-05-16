"""统一 AI API 客户端 - 支持多提供者调用"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

import httpx

logger = logging.getLogger("hydraflow.ai_client")

# ============================================================================
# 配置与枚举
# ============================================================================

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"          # 通义千问 (Dashscope)
    OLLAMA = "ollama"       # 本地 Ollama
    LM_STUDIO = "lm_studio" # 本地 LM Studio
    UNKNOWN = "unknown"


@dataclass
class AIResponse:
    """统一响应格式"""
    content: str
    provider: AIProvider
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    raw: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and bool(self.content)


# ============================================================================
# 消息格式
# ============================================================================

def _build_openai_messages(prompt: str, system: Optional[str] = None) -> List[Dict[str, str]]:
    """构建 OpenAI 兼容的消息格式"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


# ============================================================================
# 各提供者客户端
# ============================================================================

class BaseAIClient:
    """AI 客户端基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get("timeout", 120)

    async def generate(
        self,
        prompt: str,
        model: str,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        raise NotImplementedError

    def _parse_usage(self, raw: Dict[str, Any]) -> Dict[str, int]:
        """从原始响应解析 token 使用量"""
        usage = raw.get("usage", {})
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }


class OpenAIClient(BaseAIClient):
    """OpenAI API 客户端"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", os.environ.get("OPENAI_API_KEY", ""))
        self.api_base = config.get("api_base", "https://api.openai.com/v1")
        self.default_model = config.get("model", "gpt-4")

    async def generate(
        self,
        prompt: str,
        model: str = "",
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        model = model or self.default_model
        messages = _build_openai_messages(prompt, system)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if kwargs.get("top_p"):
            payload["top_p"] = kwargs["top_p"]
        if kwargs.get("stop"):
            payload["stop"] = kwargs["stop"]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                raw = response.json()

                content = ""
                if "choices" in raw and len(raw["choices"]) > 0:
                    content = raw["choices"][0]["message"].get("content", "")

                return AIResponse(
                    content=content,
                    provider=AIProvider.OPENAI,
                    model=model,
                    usage=self._parse_usage(raw),
                    raw=raw,
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API 错误: {e.response.status_code} - {e.response.text}")
            return AIResponse(
                content="", provider=AIProvider.OPENAI, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"OpenAI 请求异常: {e}")
            return AIResponse(
                content="", provider=AIProvider.OPENAI, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=str(e)
            )


class AnthropicClient(BaseAIClient):
    """Anthropic Claude API 客户端"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", os.environ.get("ANTHROPIC_API_KEY", ""))
        self.api_base = config.get("api_base", "https://api.anthropic.com/v1")
        self.default_model = config.get("model", "claude-3-sonnet-20240229")

    async def generate(
        self,
        prompt: str,
        model: str = "",
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        model = model or self.default_model

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        messages = [{"role": "user", "content": prompt}]
        body = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            body["system"] = system
        if kwargs.get("top_p"):
            body["top_p"] = kwargs["top_p"]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                raw = response.json()

                content = ""
                if "content" in raw:
                    for block in raw["content"]:
                        if block.get("type") == "text":
                            content = block.get("text", "")

                usage = {
                    "prompt_tokens": raw.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": raw.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": sum([
                        raw.get("usage", {}).get("input_tokens", 0),
                        raw.get("usage", {}).get("output_tokens", 0),
                    ]),
                }

                return AIResponse(
                    content=content, provider=AIProvider.ANTHROPIC,
                    model=model, usage=usage, raw=raw,
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API 错误: {e.response.status_code}")
            return AIResponse(
                content="", provider=AIProvider.ANTHROPIC, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"Anthropic 请求异常: {e}")
            return AIResponse(
                content="", provider=AIProvider.ANTHROPIC, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=str(e)
            )


class QwenClient(BaseAIClient):
    """通义千问客户端 - 支持 Dashscope API"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key", os.environ.get("DASHSCOPE_API_KEY", ""))
        self.api_base = config.get(
            "api_base",
            os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        )
        self.default_model = config.get("model", "qwen-turbo")

    def _detect_model_family(self, model: str) -> str:
        """检测模型家族以选择正确的 API 格式"""
        model_lower = model.lower()
        if any(x in model_lower for x in ["qwen-turbo", "qwen-plus", "qwen-max", "qwen2"]):
            return "chat"
        return "chat"

    async def generate(
        self,
        prompt: str,
        model: str = "",
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        model = model or self.default_model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": {"messages": messages},
            "parameters": {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "result_format": "message",
            },
        }
        if kwargs.get("top_p"):
            payload["parameters"]["top_p"] = kwargs["top_p"]
        if kwargs.get("stop"):
            payload["parameters"]["stop"] = kwargs["stop"]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                raw = response.json()

                content = ""
                if "output" in raw and "choices" in raw["output"]:
                    for choice in raw["output"]["choices"]:
                        if choice.get("finish_reason") == "stop":
                            content = choice.get("message", {}).get("content", "")
                            break

                usage = raw.get("usage", {})
                return AIResponse(
                    content=content, provider=AIProvider.QWEN,
                    model=model,
                    usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    raw=raw,
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"Dashscope API 错误: {e.response.status_code} - {e.response.text}")
            return AIResponse(
                content="", provider=AIProvider.QWEN, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"Dashscope 请求异常: {e}")
            return AIResponse(
                content="", provider=AIProvider.QWEN, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=str(e)
            )


class LocalAIClient(BaseAIClient):
    """本地模型客户端 (Ollama / LM Studio) - OpenAI 兼容接口"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = config.get("api_base", "http://localhost:1234/v1")
        self.api_key = config.get("api_key", config.get("api_key", "lm-studio"))
        self.default_model = config.get("model", "")
        self.provider_type = config.get("provider", AIProvider.OLLAMA)  # ollama or lm_studio

    async def generate(
        self,
        prompt: str,
        model: str = "",
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        model = model or self.default_model
        if not model:
            return AIResponse(
                content="", provider=self.provider_type, model="",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error="No model specified and no default model configured"
            )

        messages = _build_openai_messages(prompt, system)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if kwargs.get("top_p"):
            payload["top_p"] = kwargs["top_p"]
        if kwargs.get("stop"):
            payload["stop"] = kwargs["stop"]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                raw = response.json()

                content = ""
                if "choices" in raw and len(raw["choices"]) > 0:
                    content = raw["choices"][0]["message"].get("content", "")

                return AIResponse(
                    content=content, provider=self.provider_type,
                    model=model, usage=self._parse_usage(raw), raw=raw,
                )
        except httpx.HTTPStatusError as e:
            logger.error(f"本地模型 API 错误: {e.response.status_code} - {e.response.text}")
            return AIResponse(
                content="", provider=self.provider_type, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"本地模型请求异常: {e}")
            return AIResponse(
                content="", provider=self.provider_type, model=model,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                error=str(e)
            )


# ============================================================================
# 统一 AI 客户端管理器
# ============================================================================

class AIClientManager:
    """AI 客户端管理器 - 根据模型类型选择对应客户端"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._clients: Dict[AIProvider, BaseAIClient] = {}
        self._api_keys: Dict[str, str] = {}
        self._load_api_keys()
        self._init_clients()

    def _load_api_keys(self) -> None:
        """从配置文件和环境变量加载 API 密钥"""
        # 尝试从 config/api_keys.json 加载
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "api_keys.json"
        )
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    keys = json.load(f)
                    for name, info in keys.items():
                        if isinstance(info, dict) and info.get("api_key"):
                            self._api_keys[name] = info["api_key"]
            except Exception as e:
                logger.warning(f"无法加载 api_keys.json: {e}")

        # 加载 .env 文件（如果存在）
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            ".env"
        )
        if os.path.exists(env_path):
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, _, value = line.partition("=")
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
            except Exception:
                pass

        # 也从环境变量加载
        for env_var in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DASHSCOPE_API_KEY",
                        "LM_STUDIO_API_KEY", "OLLAMA_API_KEY"]:
            if env_var in os.environ:
                name = env_var.lower().replace("_api_key", "")
                self._api_keys[name] = os.environ[env_var]

    def _init_clients(self) -> None:
        """根据可用密钥初始化各提供者客户端"""
        # OpenAI
        if self._api_keys.get("openai"):
            self._clients[AIProvider.OPENAI] = OpenAIClient({
                "api_key": self._api_keys["openai"],
                "model": "gpt-4",
            })

        # Anthropic
        if self._api_keys.get("anthropic"):
            self._clients[AIProvider.ANTHROPIC] = AnthropicClient({
                "api_key": self._api_keys["anthropic"],
                "model": "claude-3-sonnet-20240229",
            })

        # Qwen / Dashscope
        if self._api_keys.get("dashscope"):
            self._clients[AIProvider.QWEN] = QwenClient({
                "api_key": self._api_keys["dashscope"],
                "model": "qwen-turbo",
            })

        # 本地部署
        local_deployments = self._get_local_deployments()
        for dep_name, dep_config in local_deployments.items():
            if not dep_config.get("enabled"):
                continue
            api_base = dep_config.get("api_base", "http://localhost:1234/v1")
            model = dep_config.get("model", "")
            provider = AIProvider.OLLAMA if dep_name == "ollama" else AIProvider.LM_STUDIO
            self._clients[provider] = LocalAIClient({
                "api_base": api_base,
                "api_key": dep_config.get("api_key", "lm-studio"),
                "model": model,
                "provider": provider,
            })

        logger.info(f"已初始化 AI 客户端: {[p.value for p in self._clients.keys()]}")

    def _get_local_deployments(self) -> Dict[str, Any]:
        """从模型配置中获取本地部署信息"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "models.json"
        )
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get("local_deployment", {})
            except Exception:
                pass
        return {}

    def _detect_provider(self, model_id: str) -> AIProvider:
        """根据模型 ID 推断 AI 提供者"""
        model_lower = model_id.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return AIProvider.OPENAI
        if "claude" in model_lower or "anthropic" in model_lower:
            return AIProvider.ANTHROPIC
        if "qwen" in model_lower or "tongyi" in model_lower or "dashscope" in model_lower:
            return AIProvider.QWEN
        if "ollama" in model_lower:
            return AIProvider.OLLAMA
        if "lm" in model_lower or "lm_studio" in model_lower:
            return AIProvider.LM_STUDIO
        return AIProvider.UNKNOWN

    def get_client(self, provider: AIProvider) -> Optional[BaseAIClient]:
        """获取指定提供者的客户端"""
        return self._clients.get(provider)

    def get_client_for_model(self, model_id: str) -> Optional[BaseAIClient]:
        """根据模型 ID 获取对应客户端"""
        provider = self._detect_provider(model_id)
        client = self._clients.get(provider)
        if client:
            return client
        # 回退：尝试任意可用客户端
        if self._clients:
            return next(iter(self._clients.values()))
        return None

    async def generate(
        self,
        prompt: str,
        model: str = "",
        provider: Optional[AIProvider] = None,
        system: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AIResponse:
        """统一生成接口"""
        if provider and provider in self._clients:
            client = self._clients[provider]
            return await client.generate(
                prompt=prompt, model=model, system=system,
                max_tokens=max_tokens, temperature=temperature, **kwargs
            )

        if model:
            client = self.get_client_for_model(model)
            if client:
                return await client.generate(
                    prompt=prompt, model=model, system=system,
                    max_tokens=max_tokens, temperature=temperature, **kwargs
                )

        return AIResponse(
            content="", provider=AIProvider.UNKNOWN, model=model or "",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            error="无可用的 AI 客户端"
        )

    def list_providers(self) -> List[Dict[str, Any]]:
        """列出已配置的提供者"""
        return [
            {"provider": p.value, "available": True}
            for p in self._clients.keys()
        ]


# ============================================================================
# 全局单例
# ============================================================================

_ai_client_manager = None


def get_ai_client_manager() -> AIClientManager:
    global _ai_client_manager
    if _ai_client_manager is None:
        _ai_client_manager = AIClientManager()
    return _ai_client_manager