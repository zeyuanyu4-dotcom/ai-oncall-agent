"""
Go Backend API Client for Tools
"""
import httpx
from typing import Optional, Dict
from app.config import settings
from app.core.context import get_current_token


class BackendAPIClient:
    """Go 后端 API 客户端"""

    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(30.0)

    def _get_headers(self) -> dict:
        """获取请求头，自动从上下文获取当前用户的 JWT"""
        headers = {"Content-Type": "application/json"}
        # 从上下文获取当前请求的 JWT token
        token = get_current_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """发送请求"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            url = f"{self.base_url}{path}"
            response = await client.request(
                method, url, headers=self._get_headers(), **kwargs
            )
            response.raise_for_status()
            return response.json()

    # ========== 服务信息查询 ==========

    async def get_service(self, service_id: int) -> dict:
        """获取服务信息"""
        return await self._request("GET", f"/api/services/{service_id}")

    async def get_service_by_name(self, project_id: int, service_name: str) -> Optional[dict]:
        """根据名称获取服务"""
        result = await self._request("GET", f"/api/projects/{project_id}/services")
        services = result.get("data", {}).get("list", [])
        for svc in services:
            if svc.get("name") == service_name:
                return svc
        return None

    # ========== 历史问题查询 ==========

    async def search_history_issues(self, keyword: str, project_id: int = None,
                                     issue_type: str = None, page: int = 1) -> dict:
        """搜索历史问题"""
        params = {"keyword": keyword, "page": page, "page_size": 10}
        if project_id:
            params["project_id"] = project_id
        if issue_type:
            params["issue_type"] = issue_type
        return await self._request("GET", "/api/issues/history/search", params=params)

    # ========== 知识库检索 ==========

    async def search_knowledge_docs(self, keyword: str, doc_type: str = None,
                                     project_id: int = None, page: int = 1) -> dict:
        """搜索知识库文档"""
        params = {"keyword": keyword, "page": page, "page_size": 10}
        if doc_type:
            params["doc_type"] = doc_type
        if project_id:
            params["project_id"] = project_id
        return await self._request("GET", "/api/knowledge-docs/search", params=params)

    async def get_knowledge_doc(self, doc_id: int) -> dict:
        """获取知识库文档详情"""
        return await self._request("GET", f"/api/knowledge-docs/{doc_id}")

    # ========== 日志查询 ==========

    async def get_logs_by_trace_id(self, trace_id: str) -> dict:
        """根据 TraceID 查询日志"""
        return await self._request("GET", f"/api/logs/trace/{trace_id}")

    async def get_logs_by_service(self, service_id: int, limit: int = 50) -> dict:
        """查询服务的日志"""
        params = {"page_size": limit}
        return await self._request("GET", f"/api/services/{service_id}/logs", params=params)

    async def search_logs(self, project_id: int = None, service_id: int = None,
                          level: str = None, keyword: str = None, limit: int = 50) -> dict:
        """搜索日志"""
        params = {"page_size": limit}
        if project_id:
            params["project_id"] = project_id
        if service_id:
            params["service_id"] = service_id
        if level:
            params["log_level"] = level
        if keyword:
            params["keyword"] = keyword
        return await self._request("GET", "/api/logs", params=params)

    # ========== 问题单更新 ==========

    async def update_issue(self, issue_id: int, data: dict) -> dict:
        """更新问题单"""
        return await self._request("PUT", f"/api/issues/{issue_id}", json=data)

    async def update_task_progress(self, task_id: int, progress: str, current_step: str) -> dict:
        """更新任务进度"""
        return await self._request(
            "POST",
            f"/api/agent-tasks/{task_id}/progress",
            json={"progress": progress, "current_step": current_step}
        )


# 全局客户端实例
backend_client = BackendAPIClient()
