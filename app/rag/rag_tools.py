"""RAG Tools - 工具层.

注意：这些工具注册在 agent-orchestrator 进程里，被 IssueAgent 调用。
但实际向量化 / 检索都通过 gRPC 走独立的 rag-engine。

RAGGenerateTool 仍在这里完成 LLM 生成（agent-orchestrator 负责 LLM）。
"""
import json
import logging
from typing import Optional

from app.tools.base import BaseTool, ToolResult
from app.rag.rag_client import rag_client

logger = logging.getLogger(__name__)


class RAGSearchTool(BaseTool):
    """RAG 检索工具 - 通过 gRPC 调 rag-engine 做向量检索."""

    name = "rag_search"
    description = """
    基于向量检索的智能知识库搜索，比关键词匹配更准确。
    自动理解问题语义，返回最相关的文档内容。

    输入参数：
    - query: 搜索问题/查询（必需）
    - top_k: 返回数量，默认5
    - project_name: 按项目过滤（可选）
    - service_name: 按服务过滤（可选）

    返回：相关的文档片段列表，包含内容、来源、相似度
    """

    async def execute(self, query: str, top_k: int = 5,
                     project_name: str = None,
                     service_name: str = None,
                     **kwargs) -> ToolResult:
        try:
            results = await rag_client.search(
                query=query,
                top_k=top_k,
                project_name=project_name or "",
                service_name=service_name or "",
            )

            if not results:
                return ToolResult(
                    data=[],
                    summary="未找到相关知识库内容"
                )

            # 生成摘要
            summaries = []
            for i, result in enumerate(results[:5]):
                metadata = result.get('metadata') or {}
                similarity = result.get('similarity', 0)
                similarity_percent = f"{similarity * 100:.0f}%"

                title = metadata.get('title', '-')
                heading = metadata.get('heading_path', '-')
                content = result.get('content', '')[:200]
                summaries.append(
                    f"[{i+1}] {title} / {heading} "
                    f"(相似度: {similarity_percent})\n"
                    f"内容: {content}..."
                )

            summary = f"找到 {len(results)} 条相关内容，展示前5条:\n" + "\n".join(summaries)

            return ToolResult(
                data=results,
                summary=summary
            )

        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                summary=f"RAG 检索失败: {str(e)}"
            )


class RAGGenerateTool(BaseTool):
    """RAG 生成工具 - 检索 + LLM 生成（LLM 由 agent-orchestrator 提供）."""

    name = "rag_generate"
    description = """
    基于知识库检索结果生成回答，确保回答有据可依。
    适合需要生成具体建议或解决方案的场景。

    输入参数：
    - query: 问题（必需）
    - context: 上下文信息（可选，用于补充问题背景）

    返回：基于知识库内容生成的回答，包含引用来源
    """

    async def execute(self, query: str, context: str = None, **kwargs) -> ToolResult:
        try:
            from app.services.llm_service import llm_service

            # 检索通过 gRPC 走 rag-engine
            results = await rag_client.search(query=query, top_k=5)

            if not results:
                return ToolResult(
                    success=False,
                    error="知识库中未找到相关内容",
                    summary="未找到相关知识库内容"
                )

            # 构建上下文
            context_parts = []
            for i, result in enumerate(results):
                metadata = result.get('metadata') or {}
                context_parts.append(
                    f"[来源{i+1}] {metadata.get('title', '-')}\n"
                    f"章节: {metadata.get('heading_path', '-')}\n"
                    f"内容: {result.get('content', '')}"
                )

            knowledge_context = "\n\n".join(context_parts)

            prompt = f"""## 知识库内容:
{knowledge_context}

## 用户问题:
{query}

{f'## 上下文信息:\n{context}' if context else ''}

## 要求:
1. 基于知识库内容回答，不要编造信息
2. 引用具体来源，格式: [来源X]
3. 如果知识库内容不足以完整回答，说明缺少什么
4. 回答要具体、可操作
"""

            system_prompt = """你是一个专业的运维工程师，基于提供的知识库内容回答问题。
必须仅使用提供的知识库内容回答，不要编造信息。
如果知识库中没有相关信息，请明确说明'知识库中未找到相关内容'。
在回答中引用来源，格式: [来源X]"""

            # LLM 由 agent-orchestrator 自己调（不在 rag-engine 进程里）
            response = await llm_service.chat(system_prompt, prompt)

            result_text = f"基于知识库生成的回答:\n\n{response}\n\n---\n相关文档来源:"
            for i, r in enumerate(results[:3]):
                metadata = r.get('metadata') or {}
                result_text += f"\n[{i+1}] {metadata.get('title', '-')} - {metadata.get('heading_path', '-')}"

            return ToolResult(
                data={
                    "answer": response,
                    "sources": [
                        {
                            "title": (r.get('metadata') or {}).get('title', '-'),
                            "heading": (r.get('metadata') or {}).get('heading_path', '-'),
                            "content": (r.get('content') or '')[:300]
                        }
                        for r in results[:3]
                    ]
                },
                summary=result_text
            )

        except Exception as e:
            logger.error(f"RAG generate error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                summary=f"RAG 生成失败: {str(e)}"
            )


class RAGStatsTool(BaseTool):
    """RAG 统计工具 - 走 gRPC 调 rag-engine."""

    name = "rag_stats"
    description = """
    查看知识库向量化的统计信息。
    无需输入参数，返回知识库中的文档数量、块数量等。

    返回：知识库统计信息
    """

    async def execute(self, **kwargs) -> ToolResult:
        try:
            stats = await rag_client.get_stats()

            summary = f"知识库统计:\n" \
                     f"- 总文档块数: {stats.get('total_chunks', 0)}\n" \
                     f"- 向量模型: {stats.get('embedding_model', '-')}\n" \
                     f"- 存储集合: {stats.get('collection_name', '-')}"

            return ToolResult(data=stats, summary=summary)

        except Exception as e:
            logger.error(f"RAG stats error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                summary=f"获取统计信息失败: {str(e)}"
            )
