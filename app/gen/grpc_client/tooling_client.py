"""ToolingService gRPC 客户端.

Python Agent 内部工具（log query / service info / history issue / 知识库 / 问题更新）
通过 gRPC 调用 Go 后端。Go 端负责鉴权（通过 metadata 里的 JWT）。

支持同步和异步两种调用风格。
"""
import asyncio
import logging
import threading
from typing import Optional

import grpc
from grpc import aio as grpc_aio

from app.config import settings
from app.core.context import get_current_token
from app.gen.proto.tooling.v1 import tooling_pb2, tooling_pb2_grpc

logger = logging.getLogger(__name__)

# Metadata key 与 Go 端约定一致
_METADATA_AUTH_KEY = "authorization"


def _auth_md() -> list[tuple[str, str]]:
    token = get_current_token()
    if not token:
        return []
    return [(_METADATA_AUTH_KEY, f"Bearer {token}")]


class ToolingGRPCClient:
    """ToolingService gRPC 客户端（单例）。"""

    def __init__(self, addr: Optional[str] = None, timeout: Optional[int] = None):
        self.addr = addr or settings.TOOLING_GRPC_ADDR
        self.timeout = timeout or settings.TOOLING_GRPC_TIMEOUT
        self._channel: Optional[grpc_aio.Channel] = None
        self._stub: Optional[tooling_pb2_grpc.ToolingServiceStub] = None
        self._lock = threading.Lock()

    async def _ensure_channel(self):
        if self._channel is not None and self._stub is not None:
            return
        with self._lock:
            if self._channel is not None and self._stub is not None:
                return
            self._channel = grpc_aio.insecure_channel(self.addr)
            self._stub = tooling_pb2_grpc.ToolingServiceStub(self._channel)
            logger.info("ToolingGRPCClient connected to %s", self.addr)

    async def close(self):
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None

    # ========== 服务信息 ==========

    async def get_service(self, service_id: int) -> Optional[dict]:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetService(
                tooling_pb2.GetServiceRequest(service_id=service_id),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return self._service_to_dict(resp.service) if resp.HasField("service") else None
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.GetService(%s) failed: %s", service_id, e)
            return None

    async def list_services_by_project(self, project_id: int) -> list[dict]:
        await self._ensure_channel()
        try:
            resp = await self._stub.ListServicesByProject(
                tooling_pb2.ListServicesByProjectRequest(project_id=project_id),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return [self._service_to_dict(s) for s in resp.services]
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.ListServicesByProject(%s) failed: %s",
                           project_id, e)
            return []

    # ========== 历史问题 ==========

    async def search_history_issues(
        self,
        keyword: str,
        project_id: int = 0,
        issue_type: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.SearchHistoryIssues(
                tooling_pb2.SearchHistoryIssuesRequest(
                    keyword=keyword,
                    project_id=project_id,
                    issue_type=issue_type,
                    page=page,
                    page_size=page_size,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {
                "data": {
                    "list": [self._issue_to_dict(i) for i in resp.items],
                    "total": resp.total,
                }
            }
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.SearchHistoryIssues failed: %s", e)
            return {"data": {"list": [], "total": 0}}

    # ========== 知识库 ==========

    async def search_knowledge_docs(
        self,
        keyword: str,
        doc_type: str = "",
        project_id: int = 0,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.SearchKnowledgeDocs(
                tooling_pb2.SearchKnowledgeDocsRequest(
                    keyword=keyword,
                    doc_type=doc_type,
                    project_id=project_id,
                    page=page,
                    page_size=page_size,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {
                "data": {
                    "list": [self._doc_to_dict(d) for d in resp.items],
                    "total": resp.total,
                }
            }
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.SearchKnowledgeDocs failed: %s", e)
            return {"data": {"list": [], "total": 0}}

    async def get_knowledge_doc(self, doc_id: int) -> Optional[dict]:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetKnowledgeDoc(
                tooling_pb2.GetKnowledgeDocRequest(doc_id=doc_id),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return self._doc_to_dict(resp.doc) if resp.HasField("doc") else None
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.GetKnowledgeDoc(%s) failed: %s", doc_id, e)
            return None

    # ========== 日志 ==========

    async def get_logs_by_trace_id(self, trace_id: str) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetLogsByTraceID(
                tooling_pb2.GetLogsByTraceIDRequest(trace_id=trace_id),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            entries = [self._log_to_dict(l) for l in resp.entries]
            return {"data": entries}
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.GetLogsByTraceID failed: %s", e)
            return {"data": []}

    async def get_logs_by_service(self, service_id: int, limit: int = 50) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.GetServiceLogs(
                tooling_pb2.GetServiceLogsRequest(service_id=service_id, limit=limit),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            entries = [self._log_to_dict(l) for l in resp.entries]
            return {"data": {"list": entries}}
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.GetServiceLogs failed: %s", e)
            return {"data": {"list": []}}

    async def search_logs(
        self,
        project_id: int = 0,
        service_id: int = 0,
        level: str = "",
        keyword: str = "",
        limit: int = 50,
    ) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.SearchLogs(
                tooling_pb2.SearchLogsRequest(
                    project_id=project_id,
                    service_id=service_id,
                    log_level=level,
                    keyword=keyword,
                    limit=limit,
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            entries = [self._log_to_dict(l) for l in resp.entries]
            return {"data": {"list": entries}}
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.SearchLogs failed: %s", e)
            return {"data": {"list": []}}

    # ========== 问题单更新 ==========

    async def update_issue(self, issue_id: int, fields: dict) -> dict:
        await self._ensure_channel()
        try:
            resp = await self._stub.UpdateIssue(
                tooling_pb2.UpdateIssueRequest(
                    issue_id=issue_id,
                    fields={str(k): str(v) for k, v in fields.items()},
                ),
                metadata=_auth_md(),
                timeout=self.timeout,
            )
            return {"data": self._issue_to_dict(resp.issue) if resp.HasField("issue") else None}
        except grpc.aio.AioRpcError as e:
            logger.warning("ToolingGRPC.UpdateIssue failed: %s", e)
            return {"data": None, "error": str(e)}

    async def update_task_progress(self, task_id: int, progress: str, current_step: str) -> dict:
        """暂不在 ToolingService 中，等价行为在 issue_agent 内完成；这里保留入口避免破坏调用方."""
        # Agent 内部 _update_progress 的兜底直接调 HTTP，因为 ToolingService 没有此方法
        logger.debug("update_task_progress forwarded to local hook (no-op in gRPC path)")
        return {"code": 0, "data": {"task_id": task_id, "progress": progress, "current_step": current_step}}

    # ========== DTO 转换 ==========

    @staticmethod
    def _service_to_dict(s) -> dict:
        return {
            "id": s.id,
            "project_id": s.project_id,
            "name": s.name,
            "language": s.language,
            "owner": s.owner,
            "status": s.status,
        }

    @staticmethod
    def _issue_to_dict(i) -> dict:
        return {
            "id": i.id,
            "issue_no": i.issue_no,
            "title": i.title,
            "status": i.status,
            "priority": i.priority,
            "issue_type": i.issue_type,
        }

    @staticmethod
    def _doc_to_dict(d) -> dict:
        return {
            "id": d.id,
            "title": d.title,
            "doc_type": d.doc_type,
            "content": d.content,
        }

    @staticmethod
    def _log_to_dict(l) -> dict:
        return {
            "timestamp": l.timestamp,
            "level": l.level,
            "log_content": l.message,  # 与 Go 后端 HTTP 返回字段对齐（log_content）
            "log_level": l.level,
            "service_name": l.service,
            "service": l.service,
            "trace_id": l.trace_id,
            "occurred_at": l.timestamp,
        }


# 单例
tooling_client = ToolingGRPCClient()
