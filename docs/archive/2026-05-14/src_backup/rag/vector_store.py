"""RAG 向量存储 - 支持多种向量存储后端"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import math
import asyncio


@dataclass
class Document:
    """文档数据结构"""
    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    distance: float


class VectorStore(ABC):
    """向量存储抽象基类"""

    @abstractmethod
    async def add_document(self, doc: Document) -> None:
        """添加文档"""
        pass

    @abstractmethod
    async def add_documents(self, docs: list[Document]) -> None:
        """批量添加文档"""
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[SearchResult]:
        """搜索相似文档"""
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    async def get(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        pass

    @abstractmethod
    async def count(self) -> int:
        """文档数量"""
        pass

    @abstractmethod
    async def list_documents(self) -> list[str]:
        """获取所有文档ID列表"""
        pass


class InMemoryVectorStore(VectorStore):
    """内存向量存储 - 单机使用"""

    def __init__(self):
        self._documents: dict[str, Document] = {}
        self._lock = asyncio.Lock()

    async def add_document(self, doc: Document) -> None:
        """添加单个文档"""
        async with self._lock:
            self._documents[doc.id] = doc

    async def add_documents(self, docs: list[Document]) -> None:
        """批量添加文档"""
        async with self._lock:
            for doc in docs:
                self._documents[doc.id] = doc

    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[SearchResult]:
        """余弦相似度搜索"""
        async with self._lock:
            results = []
            for doc in self._documents.values():
                if doc.embedding is None:
                    continue
                distance = self._cosine_distance(query_embedding, doc.embedding)
                score = 1.0 - distance
                if score >= threshold:
                    results.append(SearchResult(
                        document=doc,
                        score=score,
                        distance=distance,
                    ))
            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        async with self._lock:
            if doc_id in self._documents:
                del self._documents[doc_id]
                return True
            return False

    async def get(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        async with self._lock:
            return self._documents.get(doc_id)

    async def count(self) -> int:
        """文档数量"""
        async with self._lock:
            return len(self._documents)

    async def list_documents(self) -> list[str]:
        """获取所有文档ID列表"""
        async with self._lock:
            return list(self._documents.keys())

    @staticmethod
    def _cosine_distance(a: list[float], b: list[float]) -> float:
        """计算余弦距离"""
        if len(a) != len(b):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 1.0

        similarity = dot_product / (norm_a * norm_b)
        return 1.0 - similarity


class BM25VectorStore(VectorStore):
    """BM25 关键词搜索 - 无需嵌入模型"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self._documents: dict[str, Document] = {}
        self._k1 = k1
        self._b = b
        self._avg_doc_len = 0.0
        self._doc_freqs: dict[str, int] = {}
        self._total_docs = 0
        self._lock = asyncio.Lock()
        self._initialized = False

    def _tokenize(self, text: str) -> list[str]:
        """简单分词"""
        import re
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]

    def _calculate_idf(self) -> None:
        """计算 IDF"""
        self._doc_freqs = {}
        for doc in self._documents.values():
            tokens = set(self._tokenize(doc.content))
            for token in tokens:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str], doc_len: int) -> float:
        """计算 BM25 分数"""
        score = 0.0
        for token in query_tokens:
            if token not in self._doc_freqs:
                continue
            df = self._doc_freqs[token]
            idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1)
            tf = doc_tokens.count(token)
            numerator = tf * (self._k1 + 1)
            denominator = tf + self._k1 * (1 - self._b + self._b * doc_len / self._avg_doc_len)
            score += idf * numerator / denominator
        return score

    async def add_document(self, doc: Document) -> None:
        """添加文档"""
        async with self._lock:
            self._documents[doc.id] = doc
            self._total_docs += 1
            self._initialized = False

    async def add_documents(self, docs: list[Document]) -> None:
        """批量添加"""
        async with self._lock:
            for doc in docs:
                self._documents[doc.id] = doc
                self._total_docs += 1
            self._initialized = False

    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """BM25 搜索（忽略 query_embedding）"""
        query_tokens = self._tokenize(" ".join(query_embedding) if isinstance(query_embedding[0], (int, float)) else str(query_embedding))

        async with self._lock:
            if not self._initialized:
                self._calculate_idf()
                self._avg_doc_len = sum(
                    len(self._tokenize(doc.content)) for doc in self._documents.values()
                ) / max(len(self._documents), 1)
                self._initialized = True

            results = []
            for doc in self._documents.values():
                doc_tokens = self._tokenize(doc.content)
                score = self._bm25_score(query_tokens, doc_tokens, len(doc_tokens))
                if score > threshold:
                    results.append(SearchResult(
                        document=doc,
                        score=score,
                        distance=1.0 - score,
                    ))

            results.sort(key=lambda r: r.score, reverse=True)
            return results[:top_k]

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        async with self._lock:
            if doc_id in self._documents:
                del self._documents[doc_id]
                self._total_docs -= 1
                self._initialized = False
                return True
            return False

    async def get(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        async with self._lock:
            return self._documents.get(doc_id)

    async def count(self) -> int:
        """文档数量"""
        async with self._lock:
            return len(self._documents)

    async def list_documents(self) -> list[str]:
        """获取所有文档ID列表"""
        async with self._lock:
            return list(self._documents.keys())


class VectorStoreFactory:
    """向量存储工厂"""

    @staticmethod
    def create(
        store_type: str = "memory",
        **kwargs,
    ) -> VectorStore:
        """创建向量存储实例"""
        if store_type == "memory":
            return InMemoryVectorStore()
        elif store_type == "bm25":
            return BM25VectorStore(**kwargs)
        else:
            raise ValueError(f"Unknown vector store type: {store_type}")
