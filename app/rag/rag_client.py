"""RagService gRPC 客户端.

agent-orchestrator 进程内的工具 / HTTP 路由 都通过此 client 调 rag-engine。
- 调通 gRPC 时 JWT 自动从 contextvars 注入到 metadata
- 失败时降级为友好错误（不要让 agent 整个崩）
"""
import logging
import threading
from typing import Optional

import grpc
from grpc import aio as grpc_aio

from app.config import settings
from app.core.context import get_current_token
from app.gen.proto.rag.v1 import rag_pb2, rag_pb2_grpc

logger = logging.getLogger(__name__)

_METADATA_AUTH_KEY = "authorization"


def _auth_md() -> list[tuple[str, str]]:
    token = get_current_token()
    if not token:
        return []
    return [(_METADATA_AUTH_KEY, f"Bearer {token}")]


class RagGRPCClient:
    """RagService gRPC 客户端（单例）."""

    def __init__(self, addr: Optional[str] = None, timeout: Optional[int] = None):
        self.addr = addr or settings.RAG_GRPC_ADDR
        self.timeout = timeout or settings.RAG_GRPC_TIMEOUT
        self._channel: Optional[grpc_aio.Channel] = None
        self._stub: Optional[rag_pb2_grpc.RagServiceStub] = None
        self._lock = threading.Lock()

    async def _ensure_channel(self):
        if self._channel is not None and self._stub is not None:
            return
        with self._lock:
            if self._channel is not None and self._stub is not None:
                return
            self._channel = grpc_aio.insecure_channel(self.addr)
            self._stub = rag_pb2_grpc.RagServiceStub(self._channel)
            logger.info("RagGRPCClient connected to %s", self.addr)

    async def close(self):
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    # ========== 向量化文本 ==========

    async def vectorize_text(
        self,
        doc_id: int,
        title: str,
        doc_type: str,
        project_name: str,
        service_name: str,
        heading_path: str,
        content: str,
    ) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.VectorizeText(
                rag_pb2.VectorizeTextRequest(
                    doc_id=doc_id,
                    title=title,
                    doc_type=doc_type,
                    project_name=project_name,
                    service_name=service_name,
                    heading_path=heading_path,
                    content=content,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {
                "stored_chunks": resp.stored_chunks,
                "deleted_chunks": resp.deleted_chunks,
            }
        except grpc.aio.AioRpcError as e:
            logger.warning("RagGRPC.VectorizeText(%s) failed: %s", doc_id, e)
            return {"stored_chunks": 0, "deleted_chunks": 0, "error": str(e)}

    # ========== 向量化文件 ==========

    async def vectorize_document(
        self,
        doc_id: int,
        title: str,
        doc_type: str,
        project_name: str,
        service_name: str,
        filename: str,
        content: bytes,
    ) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.VectorizeDocument(
                rag_pb2.VectorizeDocumentRequest(
                    doc_id=doc_id,
                    title=title,
                    doc_type=doc_type,
                    project_name=project_name,
                    service_name=service_name,
                    filename=filename,
                    content=content,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {
                "stored_chunks": resp.stored_chunks,
                "deleted_chunks": resp.deleted_chunks,
            }
        except grpc.aio.AioRpcError as e:
            logger.warning("RagGRPC.VectorizeDocument(%s) failed: %s", doc_id, e)
            return {"stored_chunks": 0, "deleted_chunks": 0, "error": str(e)}

    # ========== 删除 ==========

    async def delete_by_doc_id(self, doc_id: int) -> int:
        await self._ensure_channel()
        try:
            resp = await self._stub.DeleteByDocId(
                rag_pb2.DeleteByDocIdRequest(doc_id=doc_id),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return int(resp.deleted_chunks)
        except grpc.aio.AioRpcError as e:
            logger.warning("RagGRPC.DeleteByDocId(%s) failed: %s", doc_id, e)
            return 0

    # ========== 检索 ==========

    async def search(
        self,
        query: str,
        top_k: int = 5,
        project_name: str = "",
        service_name: str = "",
        doc_type: str = "",
    ) -> list[dict]:
        await self._ensure_channel()
        try:
            resp = await self._stub.Search(
                rag_pb2.SearchRequest(
                    query=query,
                    top_k=top_k,
                    project_name=project_name,
                    service_name=service_name,
                    doc_type=doc_type,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            out = []
            for h in resp.hits:
                out.append({
                    "chunk_id": h.chunk_id,
                    "content": h.content,
                    "metadata": dict(h.metadata),
                    "distance": h.distance,
                    "similarity": h.similarity,
                })
            return out
        except grpc.aio.AioRpcError as e:
            logger.warning("RagGRPC.Search failed: %s", e)
            return []

    # ========== 统计 ==========

    async def get_stats(self) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetStats(
                rag_pb2.GetStatsRequest(),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {
                "total_chunks": int(resp.total_chunks),
                "collection_name": resp.collection_name,
                "embedding_model": resp.embedding_model,
            }
        except grpc.aio.AioRpcError as e:
            logger.warning("RagGRPC.GetStats failed: %s", e)
            return {"total_chunks": 0, "collection_name": "", "embedding_model": "", "error": str(e)}


# 单例
rag_client = RagGRPCClient()
