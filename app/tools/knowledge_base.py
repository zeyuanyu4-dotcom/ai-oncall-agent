"""
Knowledge Base Query Tool
"""
from app.tools.base import BaseTool, ToolResult
from app.services.api_client import backend_client


class KnowledgeBaseTool(BaseTool):
    """知识库检索工具"""

    name = "search_knowledge_base"
    description = """
    搜索知识库中的文档，用于查找相关的排查手册、FAQ、部署指南等。
    输入参数：
    - keyword: 搜索关键词
    - doc_type: 文档类型（可选：troubleshooting_manual, faq, deployment_guide, api_doc）
    - project_id: 项目ID（可选）
    返回：匹配的知识库文档列表
    """

    async def execute(self, keyword: str, doc_type: str = None,
                       project_id: int = None, **kwargs) -> ToolResult:
        try:
            result = await backend_client.search_knowledge_docs(
                keyword=keyword,
                doc_type=doc_type,
                project_id=project_id
            )

            data = result.get("data", {})
            docs = data.get("list", [])
            total = data.get("total", 0)

            if not docs:
                return ToolResult(data=[], summary="未找到相关知识库文档")

            # 生成摘要
            summaries = []
            for doc in docs[:5]:
                doc_type_name = self._get_doc_type_name(doc.get("doc_type", ""))
                summaries.append(
                    f"[{doc_type_name}] {doc.get('title', '-')} (v{doc.get('version', '1')})"
                )

            summary = f"找到 {total} 条相关文档，展示前5条:\n" + "\n".join(summaries)
            return ToolResult(data=docs, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"搜索知识库失败: {str(e)}")

    def _get_doc_type_name(self, doc_type: str) -> str:
        """文档类型中文名"""
        type_map = {
            "troubleshooting_manual": "故障排查手册",
            "faq": "常见问题",
            "deployment_guide": "部署指南",
            "api_doc": "接口文档",
            "db_doc": "数据库说明"
        }
        return type_map.get(doc_type, doc_type)


class KnowledgeDocDetailTool(BaseTool):
    """知识库文档详情工具"""

    name = "get_knowledge_doc_detail"
    description = """
    获取知识库文档的详细内容。
    输入参数：doc_id（文档ID）
    返回：文档完整内容
    """

    async def execute(self, doc_id: int, **kwargs) -> ToolResult:
        try:
            result = await backend_client.get_knowledge_doc(doc_id)
            data = result.get("data", {})

            if not data:
                return ToolResult(success=False, error="文档未找到", summary="文档未找到")

            summary = f"文档: {data.get('title', '-')} (v{data.get('version', '1')})"
            if data.get("content"):
                # 截取前500字符
                content_preview = data["content"][:500]
                summary += f"\n内容预览: {content_preview}..."

            return ToolResult(data=data, summary=summary)

        except Exception as e:
            return ToolResult(success=False, error=str(e), summary=f"获取文档详情失败: {str(e)}")