"""
Tool Registry
"""
from app.tools.base import BaseTool
from app.tools.service_info import ServiceInfoTool
from app.tools.history_issue import HistoryIssueTool, SimilarIssueTool
from app.tools.log_query import LogQueryTool, LogDetailTool
from app.tools.issue_update import IssueUpdateTool
from app.tools.knowledge_base import KnowledgeBaseTool
from app.rag.rag_tools import RAGSearchTool, RAGGenerateTool, RAGStatsTool


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self.tools: list[BaseTool] = []
        self._register_tools()

    def _register_tools(self):
        """注册所有工具"""
        self.tools = [
            # 日志查询（最常用，放前面）
            LogQueryTool(),
            LogDetailTool(),
            # RAG 知识库检索（增强版）
            RAGSearchTool(),
            RAGGenerateTool(),
            # 传统知识库搜索（降级方案）
            KnowledgeBaseTool(),
            # 服务信息
            ServiceInfoTool(),
            # 历史问题
            HistoryIssueTool(),
            SimilarIssueTool(),
            # 问题单更新
            IssueUpdateTool(),
            # RAG 统计
            RAGStatsTool(),
        ]

    def get_tools(self) -> list[BaseTool]:
        """获取所有工具"""
        return self.tools

    def get_tool_schemas(self) -> list[dict]:
        """获取所有工具的 schema（供 LLM 使用）"""
        return [tool.get_schema() for tool in self.tools]

    def get_tool_by_name(self, name: str) -> BaseTool:
        """根据名称获取工具"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None


# 全局工具注册表
tool_registry = ToolRegistry()