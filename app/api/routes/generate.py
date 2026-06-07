"""
Generate API Routes - 文本生成接口
供 Go 后端调用，用于报告分析等场景
"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["generate"])


class GenerateRequest(BaseModel):
    """文本生成请求"""
    prompt: str


@router.post("/generate")
async def generate_text(request: GenerateRequest):
    """
    生成文本

    接收 prompt，调用 LLM 生成文本内容

    Args:
        request: 生成请求参数

    Returns:
        生成的文本内容
    """
    try:
        # 调用 LLM 生成
        result = await llm_service.chat(
            system_prompt="你是一个专业的运维工程师，请根据用户提供的信息生成简洁、专业的分析内容。",
            user_prompt=request.prompt
        )

        logger.info(f"Generated text for prompt: {request.prompt[:50]}...")

        return JSONResponse({
            "code": 0,
            "message": "success",
            "data": result
        })

    except Exception as e:
        logger.error(f"Generate text error: {e}")
        return JSONResponse({
            "code": 1,
            "message": str(e),
            "data": None
        })
