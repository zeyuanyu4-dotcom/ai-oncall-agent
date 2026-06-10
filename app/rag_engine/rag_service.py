"""RagService gRPC 实现 - 部署在独立的 rag-engine 进程.

提供：
- VectorizeText：纯文本向量化（调用方已解析/分块）
- VectorizeDocument：文件向量化（rag-engine 内部解析）
- DeleteByDocId：删除指定 doc 的所有 chunks
- Search：向量检索
- GetStats：统计

JWT：与 AgentService / CapabilityService 同样的 metadata 约定。
"""
import logging
from typing import Optional

import grpc
from grpc.aio import ServicerContext

from app.core.context import set_current_token, clear_current_token
from app.gen.proto.rag.v1 import rag_pb2, rag_pb2_grpc
from app.grpc_server.interceptor import _extract_token
from app.rag_engine.embedding_service import get_embedding_service, document_parser

logger = logging.getLogger(__name__)


def _safe_prefix(token: Optional[str], n: int = 10) -> str:
    if not token:
        return ""
    return token[:n] + "..." if len(token) > n else token


class RagServiceServicer(rag_pb2_grpc.RagServiceServicer):
    """rag-engine 进程内的 RagService 实现."""

    async def VectorizeText(
        self,
        request: rag_pb2.VectorizeTextRequest,
        context: ServicerContext,
    ) -> rag_pb2.VectorizeTextResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            logger.info(
                "Rag.VectorizeText | doc_id=%s | has_token=%s | content_len=%d",
                request.doc_id, bool(token), len(request.content or ""),
            )
            from app.rag_engine.embedding_service import EmbeddingService
            from app.rag_engine.document_parser import DocumentChunk

            emb = get_embedding_service()
            # 删旧
            deleted = emb.delete_by_doc_id(request.doc_id)

            # 单 chunk 模式（调用方已切好）
            chunk = DocumentChunk(
                content=request.content,
                doc_id=request.doc_id,
                title=request.title,
                doc_type=request.doc_type,
                project_name=request.project_name,
                service_name=request.service_name,
                heading_path=request.heading_path,
                chunk_index=0,
            )
            with_emb = emb.vectorize_chunks([chunk])
            stored = emb.store_chunks(with_emb)
            return rag_pb2.VectorizeTextResponse(
                stored_chunks=stored, deleted_chunks=deleted,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Rag.VectorizeText failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"VectorizeText failed: {e}")
            return rag_pb2.VectorizeTextResponse()
        finally:
            clear_current_token()

    async def VectorizeDocument(
        self,
        request: rag_pb2.VectorizeDocumentRequest,
        context: ServicerContext,
    ) -> rag_pb2.VectorizeDocumentResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            logger.info(
                "Rag.VectorizeDocument | doc_id=%s | filename=%s | has_token=%s | size=%d",
                request.doc_id, request.filename, bool(token), len(request.content or b""),
            )
            emb = get_embedding_service()
            deleted = emb.delete_by_doc_id(request.doc_id)

            chunks = document_parser.parse(
                file_content=request.content,
                filename=request.filename or "upload.bin",
                doc_id=request.doc_id,
                title=request.title,
                doc_type=request.doc_type,
                project_name=request.project_name,
                service_name=request.service_name,
            )
            if not chunks:
                return rag_pb2.VectorizeDocumentResponse(
                    stored_chunks=0, deleted_chunks=deleted,
                )
            with_emb = emb.vectorize_chunks(chunks)
            stored = emb.store_chunks(with_emb)
            return rag_pb2.VectorizeDocumentResponse(
                stored_chunks=stored, deleted_chunks=deleted,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Rag.VectorizeDocument failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"VectorizeDocument failed: {e}")
            return rag_pb2.VectorizeDocumentResponse()
        finally:
            clear_current_token()

    async def DeleteByDocId(
        self,
        request: rag_pb2.DeleteByDocIdRequest,
        context: ServicerContext,
    ) -> rag_pb2.DeleteByDocIdResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            emb = get_embedding_service()
            deleted = emb.delete_by_doc_id(request.doc_id)
            return rag_pb2.DeleteByDocIdResponse(deleted_chunks=deleted)
        except Exception as e:  # noqa: BLE001
            logger.exception("Rag.DeleteByDocId failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"DeleteByDocId failed: {e}")
            return rag_pb2.DeleteByDocIdResponse()
        finally:
            clear_current_token()

    async def Search(
        self,
        request: rag_pb2.SearchRequest,
        context: ServicerContext,
    ) -> rag_pb2.SearchResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            emb = get_embedding_service()
            top_k = request.top_k or 5
            results = emb.search(
                query=request.query,
                top_k=top_k,
                project_name=request.project_name or None,
                service_name=request.service_name or None,
                doc_type=request.doc_type or None,
            )
            hits = []
            for r in results:
                hits.append(rag_pb2.SearchHit(
                    chunk_id=r.get("chunk_id", ""),
                    content=r.get("content", ""),
                    metadata={k: str(v) for k, v in (r.get("metadata") or {}).items()},
                    distance=float(r.get("distance", 0.0) or 0.0),
                    similarity=float(r.get("similarity", 0.0) or 0.0),
                ))
            logger.info(
                "Rag.Search | q='%s' | top_k=%d | hits=%d",
                (request.query or "")[:50], top_k, len(hits),
            )
            return rag_pb2.SearchResponse(hits=hits)
        except Exception as e:  # noqa: BLE001
            logger.exception("Rag.Search failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"Search failed: {e}")
            return rag_pb2.SearchResponse()
        finally:
            clear_current_token()

    async def GetStats(
        self,
        request: rag_pb2.GetStatsRequest,
        context: ServicerContext,
    ) -> rag_pb2.GetStatsResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            emb = get_embedding_service()
            stats = emb.get_stats()
            return rag_pb2.GetStatsResponse(
                total_chunks=int(stats.get("total_chunks", 0) or 0),
                collection_name=str(stats.get("collection_name", "")),
                embedding_model=str(stats.get("embedding_model", "")),
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Rag.GetStats failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"GetStats failed: {e}")
            return rag_pb2.GetStatsResponse()
        finally:
            clear_current_token()
