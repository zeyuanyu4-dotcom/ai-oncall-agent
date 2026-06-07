"""
Analysis API Routes
"""
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import IssueAnalysisRequest, AnalysisResponse, AnalysisResult
from app.services.analysis_service import analysis_service
from app.mq import RabbitMQClient, MQConfig
from app.middleware.rate_limit import limiter, ai_analysis_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# 全局 MQ 客户端
mq_client: RabbitMQClient = None


def init_mq_client(config: MQConfig):
    """初始化 MQ 客户端"""
    global mq_client
    mq_client = RabbitMQClient(config)
    if mq_client.connect():
        logger.info("RabbitMQ client initialized")
        # 启动命令消费者
        asyncio.create_task(start_command_consumer())
    else:
        logger.warning("RabbitMQ client initialization failed, running in HTTP-only mode")


async def start_command_consumer():
    """启动命令消费者"""
    if not mq_client or not mq_client.channel:
        return

    def handle_command(message: dict):
        """处理分析命令"""
        try:
            task_id = message.get("task_id")
            issue_id = message.get("issue_id")
            payload = message.get("payload", {})

            logger.info(f"Received analysis command for task {task_id}")

            # 发布进度：开始分析
            mq_client.publish_progress(task_id, "1/8", "正在接收分析任务...")

            # 执行分析（同步调用）
            result = asyncio.run(analysis_service.analyze(payload))

            # 发布结果
            mq_client.publish_result(
                task_id=task_id,
                issue_id=issue_id,
                success=True,
                summary=result.summary,
                result={
                    "summary": result.summary,
                    "root_cause": result.root_cause,
                    "solutions": result.solutions,
                    "tool_calls": result.tool_calls
                }
            )

            logger.info(f"Analysis completed for task {task_id}")

        except Exception as e:
            logger.error(f"Failed to handle command: {e}")
            # 发布失败结果
            mq_client.publish_result(
                task_id=message.get("task_id"),
                issue_id=message.get("issue_id"),
                success=False,
                error=str(e)
            )

    mq_client.consume_commands(handle_command)


@router.post("/analyze", response_model=AnalysisResponse)
@limiter.limit("20/hour")
async def analyze_issue(request: Request, req: IssueAnalysisRequest):
    """
    分析问题单（HTTP 方式，保持兼容）

    接收问题单信息，返回结构化分析结果
    限流：20次/小时/用户
    """
    try:
        logger.info(f"Analyzing issue: {req.issue_no}")

        # 构建问题数据
        issue_data = {
            "issue_id": req.issue_id,
            "issue_no": req.issue_no,
            "title": req.title,
            "description": req.description or "",
            "error_message": req.error_message or "",
            "log_excerpt": req.log_excerpt or "",
            "environment": req.environment or "",
            "project_name": req.project_name or "",
            "service_name": req.service_name or "",
            "impact_scope": req.impact_scope or ""
        }

        # 执行分析
        result = await analysis_service.analyze(issue_data)

        logger.info(f"Analysis completed for issue: {req.issue_no}")

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
