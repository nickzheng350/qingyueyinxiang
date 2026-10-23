"""HydraFlow AI RAG 模块 - 检索增强生成系统"""

from src.rag.embeddings import (
    EmbeddingModel,
    LocalEmbedding,
    RemoteEmbedding,
    HuggingFaceEmbedding,
    create_embedding_model,
)
from src.rag.vector_store import (
    Document,
    SearchResult,
    VectorStore,
    InMemoryVectorStore,
    BM25VectorStore,
    VectorStoreFactory,
)
from src.rag.rag_engine import (
    RAGEngine,
    RAGEngineManager,
    get_rag_manager,
    get_default_rag_engine,
)

__all__ = [
    "EmbeddingModel",
    "LocalEmbedding",
    "RemoteEmbedding",
    "HuggingFaceEmbedding",
    "create_embedding_model",
    "Document",
    "SearchResult",
    "VectorStore",
    "InMemoryVectorStore",
    "BM25VectorStore",
    "VectorStoreFactory",
    "RAGEngine",
    "RAGEngineManager",
    "get_rag_manager",
    "get_default_rag_engine",
]
