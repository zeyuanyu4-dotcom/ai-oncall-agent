"""
Analysis API Routes
"""
import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import IssueAnalysisRequest, AnalysisResponse, AnalysisResult
from app.services.analysis_service import analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_issue(request: IssueAnalysisRequest):
    """
    分析问题单

    接收问题单信息，返回结构化分析结果
    """
    try:
        logger.info(f"Analyzing issue: {request.issue_no}")

        # 构建问题数据
        issue_data = {
            "issue_id": request.issue_id,
            "issue_no": request.issue_no,
            "title": request.title,
            "description": request.description or "",
            "error_message": request.error_message or "",
            "log_excerpt": request.log_excerpt or "",
            "environment": request.environment or "",
            "project_name": request.project_name or "",
            "service_name": request.service_name or "",
            "impact_scope": request.impact_scope or ""
        }

        # 执行分析
        result = await analysis_service.analyze(issue_data)

        logger.info(f"Analysis completed for issue: {request.issue_no}")

        return AnalysisResponse(
            code=0,
            message="success",
            data=result
        )

    except ValueError as e:
        logger.error(f"Analysis error: {e}")
        return AnalysisResponse(
            code=400,
            message=str(e),
            data=None
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/simple")
async def analyze_simple(title: str, description: str = ""):
    """
    简单分析接口（用于测试）
    """
    try:
        issue_data = {
            "issue_no": "TEST",
            "title": title,
            "description": description
        }

        result = await analysis_service.analyze(issue_data)

        return AnalysisResponse(
            code=0,
            message="success",
            data=result
        )

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
