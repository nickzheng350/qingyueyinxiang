"""RAG 引擎 - 检索增强生成核心引擎"""

from typing import Any, Optional
import asyncio
import logging

from src.rag.embeddings import EmbeddingModel, LocalEmbedding, create_embedding_model
from src.rag.vector_store import (
    Document,
    SearchResult,
    VectorStore,
    InMemoryVectorStore,
    VectorStoreFactory,
)

logger = logging.getLogger("hydraflow.rag")


class RAGEngine:
    """RAG 引擎 - 检索增强生成核心"""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        default_top_k: int = 5,
        default_threshold: float = 0.7,
    ):
        self._embedding_model = embedding_model or LocalEmbedding()
        self._vector_store = vector_store or InMemoryVectorStore()
        self._default_top_k = default_top_k
        self._default_threshold = default_threshold

    @property
    def embedding_dimension(self) -> int:
        """嵌入向量维度"""
        return self._embedding_model.dimension

    async def add_documents(
        self,
        documents: list[str],
        *,
        metadata: Optional[dict[str, Any]] = None,
        ids: Optional[list[str]] = None,
        batch_size: int = 32,
    ) -> int:
        """添加文档到知识库

        Args:
            documents: 文档内容列表
            metadata: 共享元数据
            ids: 文档 ID 列表
            batch_size: 批处理大小

        Returns:
            添加的文档数量
        """
        import uuid

        docs_to_embed = []
        for i, content in enumerate(documents):
            doc_id = ids[i] if ids and i < len(ids) else str(uuid.uuid4())
            doc = Document(
                id=doc_id,
                content=content,
                metadata=metadata or {},
            )
            docs_to_embed.append(doc)

        for i in range(0, len(docs_to_embed), batch_size):
            batch = docs_to_embed[i:i + batch_size]
            contents = [doc.content for doc in batch]

            embeddings = await self._embedding_model.embed_batch(contents)

            for doc, embedding in zip(batch, embeddings):
                doc.embedding = embedding

            await self._vector_store.add_documents(batch)

        logger.info(f"Added {len(documents)} documents to knowledge base")
        return len(documents)

    async def add_document(
        self,
        content: str,
        *,
        doc_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """添加单个文档"""
        import uuid

        doc_id = doc_id or str(uuid.uuid4())
        embedding = await self._embedding_model.embed(content)

        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {},
            embedding=embedding,
        )

        await self._vector_store.add_document(doc)
        logger.debug(f"Added document {doc_id}")
        return doc_id

    async def query(
        self,
        question: str,
        *,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
        return_context: bool = True,
    ) -> dict[str, Any]:
        """查询知识库

        Args:
            question: 用户问题
            top_k: 返回结果数量
            threshold: 相似度阈值
            return_context: 是否返回上下文

        Returns:
            查询结果字典
        """
        top_k = top_k or self._default_top_k
        threshold = threshold or self._default_threshold

        query_embedding = await self._embedding_model.embed(question)
        results = await self._vector_store.search(
            query_embedding,
            top_k=top_k,
            threshold=threshold,
        )

        response: dict[str, Any] = {
            "question": question,
            "answer": "",
            "sources": [],
            "total_results": len(results),
        }

        if results:
            context_parts = []
            for i, result in enumerate(results):
                source_info = {
                    "id": result.document.id,
                    "content": result.document.content[:200] + "..."
                        if len(result.document.content) > 200
                        else result.document.content,
                    "score": round(result.score, 4),
                    "metadata": result.document.metadata,
                }
                response["sources"].append(source_info)

                if return_context:
                    context_parts.append(f"[Source {i+1}]\n{result.document.content}")

            if return_context:
                response["context"] = "\n\n".join(context_parts)

        return response

    async def query_with_prompt(
        self,
        question: str,
        *,
        system_prompt: str = "You are a helpful AI assistant. Use the provided context to answer the question.",
        user_prompt_template: str = "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> dict[str, Any]:
        """带提示模板的查询"""
        query_result = await self.query(
            question,
            top_k=top_k,
            threshold=threshold,
            return_context=True,
        )

        if not query_result["sources"]:
            return {
                "question": question,
                "answer": "I don't have enough information to answer this question.",
                "sources": [],
                "context": "",
            }

        context = query_result["context"]
        user_prompt = user_prompt_template.format(
            context=context,
            question=question,
        )

        return {
            "question": question,
            "answer": "",
            "sources": query_result["sources"],
            "context": context,
            "prompts": {
                "system": system_prompt,
                "user": user_prompt,
            },
        }

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        result = await self._vector_store.delete(doc_id)
        if result:
            logger.debug(f"Deleted document {doc_id}")
        return result

    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return await self._vector_store.get(doc_id)

    async def document_count(self) -> int:
        """文档数量"""
        return await self._vector_store.count()

    async def clear(self) -> int:
        """清空知识库"""
        count = await self._vector_store.count()
        docs = []
        async with asyncio.Lock():
            for doc_id in []:
                doc = await self._vector_store.get(doc_id)
                if doc:
                    docs.append(doc_id)

        for doc_id in docs:
            await self._vector_store.delete(doc_id)

        logger.info(f"Cleared {count} documents from knowledge base")
        return count

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "embedding_model": self._embedding_model.__class__.__name__,
            "vector_store": self._vector_store.__class__.__name__,
            "embedding_dimension": self.embedding_dimension,
            "default_top_k": self._default_top_k,
            "default_threshold": self._default_threshold,
        }


class RAGEngineManager:
    """RAG 引擎管理器 - 多知识库支持"""

    _instance: Optional["RAGEngineManager"] = None

    def __new__(cls) -> "RAGEngineManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._engines: dict[str, RAGEngine] = {}
        self._default_engine: Optional[RAGEngine] = None

    def create_engine(
        self,
        name: str = "default",
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        set_default: bool = True,
    ) -> RAGEngine:
        """创建 RAG 引擎"""
        engine = RAGEngine(
            embedding_model=embedding_model,
            vector_store=vector_store,
        )
        self._engines[name] = engine
        if set_default or self._default_engine is None:
            self._default_engine = engine
        logger.info(f"Created RAG engine: {name}")
        return engine

    def get_engine(self, name: str = "default") -> Optional[RAGEngine]:
        """获取引擎"""
        return self._engines.get(name)

    def get_default_engine(self) -> Optional[RAGEngine]:
        """获取默认引擎"""
        return self._default_engine

    def list_engines(self) -> list[str]:
        """列出所有引擎"""
        return list(self._engines.keys())

    def delete_engine(self, name: str) -> bool:
        """删除引擎"""
        if name in self._engines:
            del self._engines[name]
            if self._default_engine is not None:
                for engine_name, engine in self._engines.items():
                    if engine is self._default_engine:
                        break
                else:
                    self._default_engine = next(iter(self._engines.values()), None)
            return True
        return False


_rag_manager: Optional[RAGEngineManager] = None


def get_rag_manager() -> RAGEngineManager:
    """获取 RAG 管理器单例"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGEngineManager()
    return _rag_manager


def get_default_rag_engine() -> RAGEngine:
    """获取默认 RAG 引擎"""
    manager = get_rag_manager()
    engine = manager.get_default_engine()
    if engine is None:
        engine = manager.create_engine("default")
    return engine
