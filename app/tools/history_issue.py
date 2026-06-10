"""
History Issue Query Tool
"""
from app.tools.base import BaseTool, ToolResult
from app.services.api_client import backend_client


class HistoryIssueTool(BaseTool):
    """历史问题查询工具"""

    name = "search_history_issues"
    description = """
    搜索已解决的历史问题，用于查找类似问题的解决方案。
    输入参数：
    - keyword: 搜索关键词（如错误类型、服务名、错误信息）
    - project_id: 项目ID（可选）
    - issue_type: 问题类型（可选）
    返回：相似历史问题列表，包含解决方案
    """

    async def execute(self, keyword: str, project_id: int = None,
                       issue_type: str = None, **kwargs) -> ToolResult:
        try:
            result = await backend_client.search_history_issues(
                keyword=keyword,
                project_id=project_id,
                issue_type=issue_type
            )

            data = result.get("data", {})
            issues = data.get("list", [])
            total = data.get("total", 0)

            if not issues:
                return ToolResult(data=[], summary="未找到历史问题")

            # 生成摘要
            summaries = []
            for issue in issues[:5]:
                summaries.append(self._summarize_issue(issue))

            summary = f"找到 {total} 条历史问题，展示前5条:\n" + "\n".join(summaries)
            return ToolResult(data=issues, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"查询历史问题失败: {str(e)}")

    def _summarize_issue(self, issue: dict) -> str:
        """生成问题摘要"""
        return f"[{issue.get('issue_no', '-')}] {issue.get('title', '-')} - 状态:{issue.get('status', '-')}"


class SimilarIssueTool(BaseTool):
    """相似问题查询工具"""

    name = "get_similar_issues"
    description = """
    基于问题ID查找相似的历史问题。
    输入参数：issue_id（当前问题的ID）
    返回：相似问题列表
    """

    async def execute(self, issue_id: int, limit: int = 5, **kwargs) -> ToolResult:
        try:
            # ToolingService proto 当前未提供 similar-issues 端点；
            # 走 gRPC 路径时返回空结果并记录日志，避免在 agent 分析时炸。
            logger.info(
                "SimilarIssueTool not supported in gRPC mode | issue_id=%s | limit=%s",
                issue_id, limit,
            )
            return ToolResult(
                data=[],
                summary="相似问题检索在 gRPC 模式下暂未实现（请通过 HTTP 端的 GET /api/issues/<id>/similar 调用）",
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"查询相似问题失败: {str(e)}")