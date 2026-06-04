"""
Issue Update Tool
"""
from app.tools.base import BaseTool, ToolResult
from app.services.api_client import backend_client


class IssueUpdateTool(BaseTool):
    """问题单更新工具"""

    name = "update_issue"
    description = """
    更新问题单字段。根据分析结果更新问题的相关字段。
    输入参数：
    - issue_id: 问题ID
    - update_data: 更新内容，dict类型，包含以下字段（至少提供一个）：
      * issue_type: 问题类型
      * priority: 优先级（P0/P1/P2/P3）
      * root_cause: 根本原因
      * solution: 解决方案
      * assignee_id: 分配给谁
    返回：更新结果
    """

    async def execute(self, issue_id: int, update_data: dict = None, **kwargs) -> ToolResult:
        try:
            if not update_data:
                return ToolResult(
                    success=False,
                    error="需要提供 update_data",
                    summary="参数不完整"
                )

            # 过滤有效字段
            valid_fields = ["issue_type", "priority", "root_cause", "solution", "assignee_id"]
            filtered_data = {k: v for k, v in (update_data or {}).items() if k in valid_fields}

            if not filtered_data:
                return ToolResult(
                    success=False,
                    error="没有有效的更新字段",
                    summary="没有可更新的内容"
                )

            result = await backend_client.update_issue(issue_id, filtered_data)

            if result.get("code") == 0:
                summary = f"成功更新问题 {issue_id} 的字段: {', '.join(filtered_data.keys())}"
                return ToolResult(data=result.get("data"), summary=summary)
            else:
                return ToolResult(
                    success=False,
                    error=result.get("message", "更新失败"),
                    summary=f"更新失败: {result.get('message', '未知错误')}"
                )

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"更新问题失败: {str(e)}")