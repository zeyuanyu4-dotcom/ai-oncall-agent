"""
RAG Tool - 基于向量检索的增强生成
"""
import json
import logging
from typing import List, Dict, Any, Optional

from app.tools.base import BaseTool, ToolResult
from app.rag.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class RAGSearchTool(BaseTool):
    """RAG 检索工具 - 使用向量检索增强生成"""

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
            # 获取向量化服务
            embedding_service = get_embedding_service()

            # 执行检索
            results = embedding_service.search(
                query=query,
                top_k=top_k,
                project_name=project_name,
                service_name=service_name
            )

            if not results:
                return ToolResult(
                    data=[],
                    summary="未找到相关知识库内容"
                )

            # 生成摘要
            summaries = []
            for i, result in enumerate(results[:5]):
                metadata = result.get('metadata', {})
                similarity = result.get('similarity', 0)
                similarity_percent = f"{similarity * 100:.0f}%"

                summaries.append(
                    f"[{i+1}] {metadata.get('title', '-')} / {metadata.get('heading_path', '-')} "
                    f"(相似度: {similarity_percent})\n"
                    f"内容: {result['content'][:200]}..."
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
    """RAG 生成工具 - 基于检索结果生成回答"""

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

            # 先检索相关文档
            embedding_service = get_embedding_service()
            results = embedding_service.search(query=query, top_k=5)

            if not results:
                return ToolResult(
                    success=False,
                    error="知识库中未找到相关内容",
                    summary="未找到相关知识库内容"
                )

            # 构建上下文
            context_parts = []
            for i, result in enumerate(results):
                metadata = result.get('metadata', {})
                context_parts.append(
                    f"[来源{i+1}] {metadata.get('title', '-')}\n"
                    f"章节: {metadata.get('heading_path', '-')}\n"
                    f"内容: {result['content']}"
                )

            knowledge_context = "\n\n".join(context_parts)

            # 构建 Prompt
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

            # 调用 LLM 生成
            response = await llm_service.chat(system_prompt, prompt)

            # 格式化结果
            result_text = f"基于知识库生成的回答:\n\n{response}\n\n---\n相关文档来源:"
            for i, r in enumerate(results[:3]):
                metadata = r.get('metadata', {})
                result_text += f"\n[{i+1}] {metadata.get('title', '-')} - {metadata.get('heading_path', '-')}"

            return ToolResult(
                data={
                    "answer": response,
                    "sources": [
                        {
                            "title": r['metadata'].get('title', '-'),
                            "heading": r['metadata'].get('heading_path', '-'),
                            "content": r['content'][:300]
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
    """RAG 统计工具 - 查看知识库状态"""

    name = "rag_stats"
    description = """
    查看知识库向量化的统计信息。
    无需输入参数，返回知识库中的文档数量、块数量等。

    返回：知识库统计信息
    """

    async def execute(self, **kwargs) -> ToolResult:
        try:
            embedding_service = get_embedding_service()
            stats = embedding_service.get_stats()

            summary = f"知识库统计:\n" \
                     f"- 总文档块数: {stats['total_chunks']}\n" \
                     f"- 向量模型: {stats['embedding_model']}\n" \
                     f"- 存储集合: {stats['collection_name']}"

            return ToolResult(data=stats, summary=summary)

        except Exception as e:
            logger.error(f"RAG stats error: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                summary=f"获取统计信息失败: {str(e)}"
            )
