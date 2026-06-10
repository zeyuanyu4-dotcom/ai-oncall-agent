"""Go Backend API Client for Tools (gRPC 版).

历史版本：HTTP/httpx.
现在：所有工具调用通过 gRPC 走 ToolingService（Go 后端窄面）。
保留同名方法是为了让现有 tools/*.py 无需修改即可切换底层。
"""
from typing import Optional

from app.gen.grpc_client.tooling_client import tooling_client


class BackendAPIClient:
    """Go 后端 API 客户端（gRPC 薄封装）."""

    def __init__(self):
        pass

    # ========== 服务信息查询 ==========

    async def get_service(self, service_id: int) -> dict:
        svc = await tooling_client.get_service(service_id)
        return {"data": svc} if svc else {"data": None}

    async def get_service_by_name(self, project_id: int, service_name: str) -> Optional[dict]:
        services = await tooling_client.list_services_by_project(project_id)
        for svc in services:
            if svc.get("name") == service_name:
                return svc
        return None

    # ========== 历史问题查询 ==========

    async def search_history_issues(
        self,
        keyword: str,
        project_id: int = None,
        issue_type: str = None,
        page: int = 1,
    ) -> dict:
        return await tooling_client.search_history_issues(
            keyword=keyword,
            project_id=project_id or 0,
            issue_type=issue_type or "",
            page=page,
            page_size=10,
        )

    # ========== 知识库检索 ==========

    async def search_knowledge_docs(
        self,
        keyword: str,
        doc_type: str = None,
        project_id: int = None,
        page: int = 1,
    ) -> dict:
        return await tooling_client.search_knowledge_docs(
            keyword=keyword,
            doc_type=doc_type or "",
            project_id=project_id or 0,
            page=page,
            page_size=10,
        )

    async def get_knowledge_doc(self, doc_id: int) -> dict:
        d = await tooling_client.get_knowledge_doc(doc_id)
        return {"data": d} if d else {"data": None}

    # ========== 日志查询 ==========

    async def get_logs_by_trace_id(self, trace_id: str) -> dict:
        return await tooling_client.get_logs_by_trace_id(trace_id)

    async def get_logs_by_service(self, service_id: int, limit: int = 50) -> dict:
        return await tooling_client.get_logs_by_service(service_id, limit=limit)

    async def search_logs(
        self,
        project_id: int = None,
        service_id: int = None,
        level: str = None,
        keyword: str = None,
        limit: int = 50,
    ) -> dict:
        return await tooling_client.search_logs(
            project_id=project_id or 0,
            service_id=service_id or 0,
            level=level or "",
            keyword=keyword or "",
            limit=limit,
        )

    # ========== 问题单更新 ==========

    async def update_issue(self, issue_id: int, data: dict) -> dict:
        return await tooling_client.update_issue(issue_id, data)

    async def update_task_progress(
        self, task_id: int, progress: str, current_step: str
    ) -> dict:
        """进度更新.

        走 gRPC 路径时由 agent.analyze 内部维护；这里保留 HTTP 兜底
        （旧的 Go API 路由）以防 ToolingService 不可用。
        """
        return await tooling_client.update_task_progress(task_id, progress, current_step)


# 全局客户端实例
backend_client = BackendAPIClient()
