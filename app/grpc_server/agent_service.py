"""AgentService gRPC 实现.

Worker 通过 gRPC streaming 调 RunAgent:
- 持续产出 ProgressUpdate 事件
- 结束时发出 AgentResult（成功）或 ErrorInfo（失败）

进度事件双写策略：
- 工具内 _update_progress 走 gRPC stream（不发 HTTP）
- HTTP 入口仍走 HTTP 进度（保持兼容）
"""
import asyncio
import logging
from datetime import datetime
from typing import AsyncIterator

import grpc
from grpc.aio import ServicerContext

from app.agents.issue_agent import issue_agent
from app.core.context import set_current_token, clear_current_token
from app.gen.proto.agent.v1 import agent_pb2, agent_pb2_grpc
from app.grpc_server.interceptor import _extract_token

logger = logging.getLogger(__name__)


def _safe_prefix(token: str | None, n: int = 10) -> str:
    if not token:
        return ""
    return token[:n] + "..." if len(token) > n else token


class AgentServiceServicer(agent_pb2_grpc.AgentServiceServicer):
    """AgentService.RunAgent - server streaming."""

    async def RunAgent(
        self,
        request: agent_pb2.RunAgentRequest,
        context: ServicerContext,
    ) -> AsyncIterator[agent_pb2.RunAgentResponse]:
        # 从入站 metadata 提取 JWT 并塞入 ContextVar，
        # 工具内部 get_current_token() 才能读到。
        md = context.invocation_metadata()
        token = _extract_token(md)

        set_current_token(token)
        logger.info(
            "RunAgent started | task_id=%s | issue_no=%s | has_token=%s | token_prefix=%s",
            request.task_id, request.issue_no, bool(token), _safe_prefix(token),
        )

        try:
            # 启动事件
            yield agent_pb2.RunAgentResponse(
                progress=agent_pb2.ProgressUpdate(
                    step=1, step_label="1/8", message="正在启动分析任务..."
                )
            )

            # 构建 issue_data
            issue_data = {
                "task_id": request.task_id,
                "issue_id": request.issue_id,
                "issue_no": request.issue_no,
                "title": request.title,
                "description": request.description,
                "error_message": request.error_message,
                "log_excerpt": request.log_excerpt,
                "environment": request.environment,
                "project_id": request.project_id,
                "project_name": request.project_name,
                "service_name": request.service_name,
                "impact_scope": request.impact_scope,
            }

            # 进度回调：当 agent 走到每个 step 时，由 stream 推送给 Go 端
            last_step_sent = {"v": 0}
            lock = asyncio.Lock()

            async def progress_callback(step: int, label: str, message: str):
                # 这个函数是从 agent.analyze 内部 await 的协程，
                # 不能直接 yield（yield 必须在 RPC 协程中）。
                # 因此只能更新共享状态 + 把事件存进队列。
                async with lock:
                    if step > last_step_sent["v"]:
                        last_step_sent["v"] = step

            # 真正推送进度的队列
            progress_queue: asyncio.Queue = asyncio.Queue()

            async def queue_progress_callback(step: int, label: str, message: str):
                await progress_queue.put(
                    agent_pb2.RunAgentResponse(
                        progress=agent_pb2.ProgressUpdate(
                            step=step, step_label=label, message=message
                        )
                    )
                )

            # 启动 agent.analyze 在后台任务
            result_holder: dict = {}
            err_holder: dict = {}

            async def _run_agent():
                try:
                    r = await issue_agent.analyze(
                        issue_data,
                        task_id=int(request.task_id) if request.task_id else None,
                        progress_callback=queue_progress_callback,
                        skip_http_progress=True,  # gRPC 模式下不写 HTTP 进度
                    )
                    result_holder["v"] = r
                except Exception as e:  # noqa: BLE001
                    err_holder["v"] = e
                finally:
                    await progress_queue.put(None)  # 哨兵

            agent_task = asyncio.create_task(_run_agent())

            # 消费进度事件
            while True:
                ev = await progress_queue.get()
                if ev is None:
                    break
                yield ev

            # 等结果
            if err_holder.get("v") is not None:
                e = err_holder["v"]
                logger.error("RunAgent failed: %s", e, exc_info=True)
                yield agent_pb2.RunAgentResponse(
                    error=agent_pb2.ErrorInfo(code="AGENT_ERROR", message=str(e))
                )
                return

            result = result_holder.get("v", {})

            # 构造 AgentResult
            evidence = [
                agent_pb2.EvidenceItem(
                    source=e.get("source", ""),
                    content=e.get("content", ""),
                    relevance=e.get("relevance", ""),
                )
                for e in result.get("evidence", []) or []
            ]
            tool_calls = [
                agent_pb2.ToolCallRecord(
                    step=tc.get("step", 0),
                    tool_name=tc.get("tool_name", ""),
                    input=tc.get("input", ""),
                    output=tc.get("output", ""),
                    thought=tc.get("thought", ""),
                    executed_at=tc.get("executed_at", "") or datetime.now().isoformat(),
                    duration_ms=int(tc.get("duration_ms", 0) or 0),
                )
                for tc in result.get("tool_calls", []) or []
            ]
            ar = agent_pb2.AgentResult(
                summary=result.get("summary", "") or request.title,
                issue_type=result.get("issue_type", ""),
                related_services=list(result.get("related_services", []) or []),
                suspected_cause=result.get("suspected_cause", ""),
                evidence=evidence,
                suggestions=list(result.get("suggestions", []) or []),
                missing_info=list(result.get("missing_info", []) or []),
                next_steps=list(result.get("next_steps", []) or []),
                confidence=float(result.get("confidence", 0.0) or 0.0),
                tool_calls=tool_calls,
            )
            yield agent_pb2.RunAgentResponse(result=ar)
            logger.info(
                "RunAgent completed | task_id=%s | issue_no=%s | tools=%d",
                request.task_id, request.issue_no, len(tool_calls),
            )

        except Exception as e:  # noqa: BLE001
            logger.exception("RunAgent unexpected error: %s", e)
            try:
                yield agent_pb2.RunAgentResponse(
                    error=agent_pb2.ErrorInfo(
                        code="UNEXPECTED", message=f"{type(e).__name__}: {e}"
                    )
                )
            except Exception:
                pass
        finally:
            clear_current_token()
