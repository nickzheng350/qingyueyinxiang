"""RAG 嵌入模型 - 支持本地和远程嵌入"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import asyncio
import logging

logger = logging.getLogger("hydraflow.rag")


class EmbeddingModel(ABC):
    """嵌入模型抽象基类"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """将文本嵌入为向量"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入文本"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回嵌入向量的维度"""
        pass


class LocalEmbedding(EmbeddingModel):
    """本地嵌入模型 - 使用 sentence-transformers"""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        normalize: bool = True,
    ):
        self._model_name = model_name
        self._device = device
        self._normalize = normalize
        self._model = None
        self._dimension = 384

    async def _load_model(self) -> Any:
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name, device=self._device)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, using simple hash embedding"
                )
                self._model = None
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """嵌入单个文本"""
        model = await self._load_model()
        if model is None:
            return self._simple_hash_embedding(text)

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, normalize_embeddings=self._normalize)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量嵌入"""
        model = await self._load_model()
        if model is None:
            return [self._simple_hash_embedding(text) for text in texts]

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts, normalize_embeddings=self._normalize, show_progress_bar=False)
        )
        return embeddings.tolist()

    def _simple_hash_embedding(self, text: str) -> list[float]:
        """简单的 hash 嵌入（备用方案）"""
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(min(self._dimension, len(hash_bytes) * 4)):
            byte_idx = i // 4
            offset = (i % 4) * 8
            value = (hash_bytes[byte_idx] >> offset) & 0xFF
            embedding.append((value / 255.0) * 2 - 1)
        while len(embedding) < self._dimension:
            embedding.append(0.0)
        return embedding[:self._dimension]


class RemoteEmbedding(EmbeddingModel):
    """远程嵌入模型 - 支持 OpenAI、Anthropic 等 API"""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-ada-002",
        base_url: Optional[str] = None,
        dimension: int = 1536,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url or "https://api.openai.com/v1"
        self._dimension = dimension
        self._client = None

    async def _get_client(self) -> Any:
        """获取 HTTP 客户端"""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        """通过 API 嵌入单个文本"""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """通过 API 批量嵌入"""
        client = await self._get_client()

        async with client as c:
            response = await c.post(
                "/embeddings",
                json={
                    "input": texts,
                    "model": self._model,
                },
            )
            response.raise_for_status()
            data = response.json()

        return [item["embedding"] for item in data["data"]]


class HuggingFaceEmbedding(EmbeddingModel):
    """HuggingFace Inference API 嵌入"""

    def __init__(
        self,
        api_key: str,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        dimension: int = 384,
    ):
        self._api_key = api_key
        self._model = model
        self._dimension = dimension
        self._client = None

    async def _get_client(self) -> Any:
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url="https://api-inference.huggingface.co/models",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                },
                timeout=60.0,
            )
        return self._client

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> list[float]:
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        client = await self._get_client()

        async with client as c:
            response = await c.post(
                f"/{self._model}",
                json={"inputs": texts},
            )
            response.raise_for_status()
            data = response.json()

        if isinstance(data, list):
            return [item.tolist() if hasattr(item, 'tolist') else item for item in data]
        return [data.tolist() if hasattr(data, 'tolist') else data]


def create_embedding_model(
    model_type: str = "local",
    **kwargs,
) -> EmbeddingModel:
    """工厂函数创建嵌入模型"""
    if model_type == "local":
        return LocalEmbedding(**kwargs)
    elif model_type == "openai":
        return RemoteEmbedding(**kwargs)
    elif model_type == "huggingface":
        return HuggingFaceEmbedding(**kwargs)
    else:
        raise ValueError(f"Unknown embedding model type: {model_type}")
