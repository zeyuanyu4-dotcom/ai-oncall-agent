"""
Log Query Tool
"""
from app.tools.base import BaseTool, ToolResult
from app.services.api_client import backend_client


class LogQueryTool(BaseTool):
    """日志查询工具"""

    name = "query_logs"
    description = """
    查询日志信息，用于追踪问题发生时的上下文。
    输入参数（至少提供一个）：
    - trace_id: Trace ID，用于精确定位单次请求
    - service_id: 服务ID，查询该服务的日志
    - keyword: 关键词搜索日志内容
    - level: 日志级别（ERROR, WARN, INFO, DEBUG）
    - limit: 返回条数（默认50）
    返回：日志列表
    """

    async def execute(self, trace_id: str = None, service_id: int = None,
                     keyword: str = None, level: str = None, limit: int = 50,
                     project_id: int = None, **kwargs) -> ToolResult:
        try:
            if trace_id:
                # 根据 TraceID 查询
                result = await backend_client.get_logs_by_trace_id(trace_id)
                logs = result.get("data", [])
            elif service_id:
                # 根据服务ID查询
                result = await backend_client.get_logs_by_service(service_id, limit=limit)
                logs = result.get("data", {}).get("list", [])
            else:
                # 通用搜索
                result = await backend_client.search_logs(
                    project_id=project_id,
                    service_id=service_id,
                    level=level,
                    keyword=keyword,
                    limit=limit
                )
                logs = result.get("data", {}).get("list", [])

            if not logs:
                return ToolResult(data=[], summary="未找到相关日志")

            # 生成摘要
            summaries = []
            for log in logs[:10]:
                log_level = log.get("log_level", "-")
                log_content = log.get("log_content", "")[:100]
                time_str = log.get("occurred_at", "")[:19]
                summaries.append(f"[{log_level}] {time_str} - {log_content}")

            summary = f"找到 {len(logs)} 条日志，展示前10条:\n" + "\n".join(summaries)
            return ToolResult(data=logs, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"查询日志失败: {str(e)}")


class LogDetailTool(BaseTool):
    """日志详情工具"""

    name = "get_log_detail"
    description = """
    获取单条日志的详细信息，包括完整的堆栈信息。
    输入参数：log_id（日志ID）
    返回：日志详情
    """

    async def execute(self, log_id: int, **kwargs) -> ToolResult:
        try:
            from app.services.api_client import backend_client
            result = await backend_client._request("GET", f"/api/logs/{log_id}")
            data = result.get("data", {})

            if not data:
                return ToolResult(success=False, error="日志未找到", summary="日志未找到")

            summary = f"日志详情 [{data.get('log_level', '-')}]: {data.get('log_content', '')[:200]}"
            if data.get("stack_trace"):
                summary += f"\n堆栈: {data['stack_trace'][:300]}..."

            return ToolResult(data=data, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"获取日志详情失败: {str(e)}")