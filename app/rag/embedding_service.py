"""
Embedding Service - 文档向量化
使用 SentenceTransformer 生成向量，存入 Chroma
"""
import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings

from app.rag.document_parser import DocumentChunk, document_parser

logger = logging.getLogger(__name__)

# Chroma 数据目录
CHROMA_PATH = "./data/chroma"
COLLECTION_NAME = "knowledge_base"


@dataclass
class ChunkWithEmbedding:
    """带向量的文档块"""
    chunk: DocumentChunk
    embedding: List[float]


class EmbeddingService:
    """向量化服务"""

    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """初始化模型和数据库"""
        try:
            # 初始化 SentenceTransformer
            from sentence_transformers import SentenceTransformer
            # 使用轻量级模型
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded: all-MiniLM-L6-v2")

            # 初始化 Chroma
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False)
            )

            # 获取或创建 collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Knowledge base vector store"}
            )
            logger.info(f"Chroma collection initialized: {COLLECTION_NAME}")

        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """生成文本向量"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def vectorize_chunks(self, chunks: List[DocumentChunk]) -> List[ChunkWithEmbedding]:
        """向量化文档块"""
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embed_texts(texts)

        result = []
        for chunk, embedding in zip(chunks, embeddings):
            result.append(ChunkWithEmbedding(chunk=chunk, embedding=embedding))

        return result

    def store_chunks(self, chunks: List[ChunkWithEmbedding]) -> int:
        """
        存储文档块到向量库

        Returns:
            存储的块数量
        """
        if not chunks:
            return 0

        # 准备数据
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk_with_emb in enumerate(chunks):
            chunk = chunk_with_emb.chunk

            # 生成唯一 ID
            chunk_id = f"doc_{chunk.doc_id}_chunk_{chunk.chunk_index}"

            ids.append(chunk_id)
            embeddings.append(chunk_with_emb.embedding)
            documents.append(chunk.content)
            metadatas.append({
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "doc_type": chunk.doc_type,
                "project_name": chunk.project_name,
                "service_name": chunk.service_name,
                "heading_path": chunk.heading_path,
                "chunk_index": chunk.chunk_index
            })

        # 批量添加
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(f"Stored {len(chunks)} chunks to vector store")
        return len(chunks)

    def search(self, query: str, top_k: int = 5,
               project_name: str = None,
               service_name: str = None,
               doc_type: str = None) -> List[Dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            top_k: 返回数量
            project_name: 按项目过滤
            service_name: 按服务过滤
            doc_type: 按类型过滤

        Returns:
            检索结果列表
        """
        # 生成查询向量
        query_embedding = self.embed_texts([query])[0]

        # 构建过滤条件
        where_filter = {}
        if project_name:
            where_filter["project_name"] = project_name
        if service_name:
            where_filter["service_name"] = service_name
        if doc_type:
            where_filter["doc_type"] = doc_type

        # 执行检索
        if where_filter:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )
        else:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )

        # 格式化结果
        formatted_results = []
        if results and results.get('ids') and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "chunk_id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results.get('distances', [[]])[0][i] if results.get('distances') else 0,
                    "similarity": 1 - results.get('distances', [[1]])[0][i] if results.get('distances') else 0
                })

        return formatted_results

    def delete_by_doc_id(self, doc_id: int) -> int:
        """
        删除文档的所有块

        Returns:
            删除的块数量
        """
        # 查找该文档的所有块
        results = self.collection.get(
            where={"doc_id": doc_id}
        )

        if not results or not results.get('ids'):
            return 0

        ids_to_delete = results['ids']
        self.collection.delete(ids=ids_to_delete)

        logger.info(f"Deleted {len(ids_to_delete)} chunks for doc_id={doc_id}")
        return len(ids_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": COLLECTION_NAME,
            "embedding_model": "all-MiniLM-L6-v2"
        }


# 全局服务实例（延迟初始化）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取向量化服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
