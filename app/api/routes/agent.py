"""
Agent Analysis API Routes
"""
import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import AgentAnalysisRequest, AnalysisResponse
from app.agents.issue_agent import issue_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/analyze")
async def analyze_issue(request: AgentAnalysisRequest):
    """
    Agent 深度分析接口

    接收问题单信息，调用 Agent 进行深度分析（带工具调用）
    """
    try:
        logger.info(f"Agent analyzing issue: {request.issue_no} (task: {request.task_id})")

        # 构建问题数据
        issue_data = {
            "task_id": request.task_id,
            "issue_id": request.issue_id,
            "issue_no": request.issue_no,
            "title": request.title,
            "description": request.description or "",
            "error_message": request.error_message or "",
            "log_excerpt": request.log_excerpt or "",
            "environment": request.environment or "",
            "project_id": request.project_id,
            "project_name": request.project_name or "",
            "service_name": request.service_name or "",
            "impact_scope": request.impact_scope or ""
        }

        # 执行分析
        result = await issue_agent.analyze(issue_data, request.task_id)

        logger.info(f"Agent analysis completed for issue: {request.issue_no}")

        return {
            "code": 0,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Agent analysis error: {e}")
        return {
            "code": 1,
            "message": str(e),
            "data": None
        }


@router.post("/analyze/simple")
async def analyze_simple(title: str, description: str = ""):
    """
    简单分析接口（用于测试，不使用工具）
    """
    try:
        issue_data = {
            "issue_no": "TEST",
            "title": title,
            "description": description
        }

        result = await issue_agent.analyze(issue_data, None)

        return {
            "code": 0,
            "message": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))