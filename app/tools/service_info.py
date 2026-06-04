"""
Service Info Query Tool
"""
from app.tools.base import BaseTool, ToolResult
from app.services.api_client import backend_client


class ServiceInfoTool(BaseTool):
    """服务信息查询工具"""

    name = "get_service_info"
    description = """
    查询服务的详细信息，包括服务配置、依赖关系、API接口等。
    输入参数：service_name（服务名称）或 service_id（服务ID）
    返回：服务详细信息
    """

    async def execute(self, service_name: str = None, service_id: int = None,
                       project_id: int = None, **kwargs) -> ToolResult:
        try:
            if service_id:
                result = await backend_client.get_service(service_id)
                data = result.get("data", {})
            elif service_name and project_id:
                data = await backend_client.get_service_by_name(project_id, service_name)
                if not data:
                    return ToolResult(success=False, error="服务未找到", summary="服务未找到")
            else:
                return ToolResult(
                    success=False,
                    error="需要提供 service_name + project_id 或 service_id",
                    summary="参数不完整"
                )

            summary = self._summarize_service(data)
            return ToolResult(data=data, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"查询服务信息失败: {str(e)}")

    def _summarize_service(self, data: dict) -> str:
        """生成摘要"""
        parts = []
        if data.get("name"):
            parts.append(f"服务名: {data['name']}")
        if data.get("description"):
            parts.append(f"描述: {data['description']}")
        if data.get("endpoint"):
            parts.append(f"端点: {data['endpoint']}")
        if data.get("dependencies"):
            parts.append(f"依赖服务: {', '.join([d.get('name', '') for d in data['dependencies'][:3]])}")
        return " | ".join(parts) if parts else "服务信息"