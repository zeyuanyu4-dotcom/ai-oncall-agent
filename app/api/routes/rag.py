"""
RAG API Routes - 文档向量化接口
供 Go 后端 / 内部工具调用。

gRPC 迁移说明：
- 旧：HTTP /api/rag/* → 直接调本进程的 EmbeddingService（in-process）
- 新：HTTP /api/rag/* → gRPC RagService（跨进程调用 rag-engine）
- 对调用方接口不变；底层实现切到 gRPC
"""
import logging
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.rag.rag_client import rag_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


# ========== Pydantic Models ==========

class VectorizeTextRequest(BaseModel):
    """向量化文本请求"""
    doc_id: int
    title: str = ""
    doc_type: str = ""
    project_name: str = ""
    service_name: str = ""
    content: str
    heading_path: str = ""


class VectorizeTextResponse(BaseModel):
    """向量化文本响应"""
    doc_id: int
    stored_chunks: int
    deleted_chunks: int


# ========== API Routes ==========

@router.post("/vectorize")
async def vectorize_document(
    file: UploadFile = File(...),
    doc_id: int = Form(...),
    title: str = Form(""),
    doc_type: str = Form(""),
    project_name: str = Form(""),
    service_name: str = Form("")
):
    """
    向量化文档（文件上传）

    接收文件（markdown/word/pdf），通过 gRPC 转发到 rag-engine 完成解析+向量化+存储。
    """
    try:
        file_content = await file.read()

        result = await rag_client.vectorize_document(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            project_name=project_name,
            service_name=service_name,
            filename=file.filename or "upload.bin",
            content=file_content,
        )

        if result.get("error") or result.get("stored_chunks", 0) == 0:
            return JSONResponse({
                "code": 1,
                "message": result.get("error", "向量化失败或内容为空"),
                "data": None,
            })

        logger.info(
            f"Vectorized document {doc_id}: stored {result['stored_chunks']} chunks, "
            f"deleted {result['deleted_chunks']} old chunks"
        )

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": doc_id,
                "title": title,
                "stored_chunks": result["stored_chunks"],
                "deleted_chunks": result["deleted_chunks"],
            }
        })

    except Exception as e:
        logger.error(f"Vectorize error: {e}")
        return JSONResponse({
            "code": 1,
            "message": f"向量化失败: {str(e)}",
            "data": None,
        })


@router.post("/vectorize/text")
async def vectorize_text(request: VectorizeTextRequest):
    """
    向量化纯文本

    直接提交文本内容进行向量化，使用 JSON Body 格式。
    转发到 rag-engine 完成 embedding+存储。
    """
    try:
        result = await rag_client.vectorize_text(
            doc_id=request.doc_id,
            title=request.title,
            doc_type=request.doc_type,
            project_name=request.project_name,
            service_name=request.service_name,
            heading_path=request.heading_path,
            content=request.content,
        )

        if result.get("error"):
            return JSONResponse({
                "code": 1,
                "message": result["error"],
                "data": None,
            })

        logger.info(
            f"Vectorized text doc {request.doc_id}: stored {result['stored_chunks']} chunks"
        )

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": request.doc_id,
                "stored_chunks": result["stored_chunks"],
                "deleted_chunks": result["deleted_chunks"],
            }
        })

    except Exception as e:
        logger.error(f"Vectorize text error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })


@router.post("/delete/{doc_id}")
async def delete_document_vector(doc_id: int):
    """删除文档的向量（转发到 rag-engine）"""
    try:
        deleted = await rag_client.delete_by_doc_id(doc_id)
        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": doc_id,
                "deleted_chunks": deleted,
            }
        })

    except Exception as e:
        logger.error(f"Delete vector error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })


@router.get("/stats")
async def get_stats():
    """获取知识库统计信息（转发到 rag-engine）"""
    try:
        stats = await rag_client.get_stats()
        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": stats,
        })

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })


@router.get("/search")
async def search(
    query: str,
    top_k: int = 5,
    project_name: str = None,
    service_name: str = None,
    doc_type: str = None
):
    """搜索知识库（转发到 rag-engine）"""
    try:
        results = await rag_client.search(
            query=query,
            top_k=top_k,
            project_name=project_name or "",
            service_name=service_name or "",
            doc_type=doc_type or "",
        )
        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": results,
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })
