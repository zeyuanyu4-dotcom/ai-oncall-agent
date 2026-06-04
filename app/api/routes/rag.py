"""
RAG API Routes - 文档向量化接口
供 Go 后端调用
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.rag.document_parser import document_parser
from app.rag.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


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
    向量化文档

    上传文档文件，解析、切分、向量化后存入向量库

    Args:
        file: 文档文件 (markdown/word/pdf)
        doc_id: 文档ID
        title: 文档标题
        doc_type: 文档类型
        project_name: 项目名称
        service_name: 服务名称

    Returns:
        存储结果
    """
    try:
        # 读取文件内容
        file_content = await file.read()

        # 解析文档
        chunks = document_parser.parse(
            file_content=file_content,
            filename=file.filename,
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            project_name=project_name,
            service_name=service_name
        )

        if not chunks:
            return JSONResponse({
                "code": 1,
                "message": "文档解析失败或内容为空",
                "data": None
            })

        # 获取向量化服务
        embedding_service = get_embedding_service()

        # 删除旧文档（如果存在）
        deleted_count = embedding_service.delete_by_doc_id(doc_id)

        # 向量化并存储
        chunks_with_emb = embedding_service.vectorize_chunks(chunks)
        stored_count = embedding_service.store_chunks(chunks_with_emb)

        logger.info(f"Vectorized document {doc_id}: stored {stored_count} chunks, deleted {deleted_count} old chunks")

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": doc_id,
                "title": title,
                "total_chunks": len(chunks),
                "stored_chunks": stored_count,
                "deleted_chunks": deleted_count
            }
        })

    except ValueError as e:
        logger.error(f"Vectorize error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })
    except Exception as e:
        logger.error(f"Vectorize error: {e}")
        return JSONResponse({
            "code": 1,
            "message": f"向量化失败: {str(e)}",
            "data": None
        })


@router.post("/vectorize/text")
async def vectorize_text(
    doc_id: int = Form(...),
    title: str = Form(""),
    doc_type: str = Form(""),
    project_name: str = Form(""),
    service_name: str = Form(""),
    content: str = Form(...),
    heading_path: str = Form("")
):
    """
    向量化纯文本

    直接提交文本内容进行向量化

    Args:
        doc_id: 文档ID
        title: 文档标题
        doc_type: 文档类型
        project_name: 项目名称
        service_name: 服务名称
        content: 文本内容
        heading_path: 章节路径

    Returns:
        存储结果
    """
    try:
        from app.rag.document_parser import DocumentChunk

        # 构建单个块
        chunk = DocumentChunk(
            content=content,
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            project_name=project_name,
            service_name=service_name,
            heading_path=heading_path,
            chunk_index=0
        )

        # 获取向量化服务
        embedding_service = get_embedding_service()

        # 删除旧文档
        deleted_count = embedding_service.delete_by_doc_id(doc_id)

        # 向量化并存储
        chunks_with_emb = embedding_service.vectorize_chunks([chunk])
        stored_count = embedding_service.store_chunks(chunks_with_emb)

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": doc_id,
                "stored_chunks": stored_count,
                "deleted_chunks": deleted_count
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
    """
    删除文档的向量

    Args:
        doc_id: 文档ID

    Returns:
        删除结果
    """
    try:
        embedding_service = get_embedding_service()
        deleted_count = embedding_service.delete_by_doc_id(doc_id)

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": {
                "doc_id": doc_id,
                "deleted_chunks": deleted_count
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
    """
    获取知识库统计信息

    Returns:
        统计信息
    """
    try:
        embedding_service = get_embedding_service()
        stats = embedding_service.get_stats()

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": stats
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
    """
    搜索知识库

    Args:
        query: 搜索查询
        top_k: 返回数量
        project_name: 按项目过滤
        service_name: 按服务过滤
        doc_type: 按类型过滤

    Returns:
        搜索结果
    """
    try:
        embedding_service = get_embedding_service()
        results = embedding_service.search(
            query=query,
            top_k=top_k,
            project_name=project_name,
            service_name=service_name,
            doc_type=doc_type
        )

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": results
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })
