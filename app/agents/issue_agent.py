"""
Issue Agent - 带工具调用的智能分析 Agent
使用 LangChain 的 ReAct 模式，结合预定义步骤
"""
import json
import logging
import time
from datetime import datetime
from typing import Optional

from app.services.llm_service import llm_service
from app.services.api_client import backend_client
from app.tools.registry import tool_registry
from app.tools.base import ToolResult

logger = logging.getLogger(__name__)


# 预定义的关键步骤
PREDEFINED_STEPS = [
    {"step": 1, "name": "提取关键信息", "action": "extract_info"},
    {"step": 2, "name": "查询日志", "action": "query_logs_if_available"},
    {"step": 3, "name": "查询服务信息", "action": "query_service_if_available"},
    {"step": 4, "name": "LLM 自主决策", "action": "llm_decision"},
    {"step": 5, "name": "查询历史问题", "action": "query_history_if_needed"},
    {"step": 6, "name": "查询知识库", "action": "query_knowledge_if_needed"},
    {"step": 7, "name": "生成分析报告", "action": "generate_report"},
    {"step": 8, "name": "保存结果", "action": "save_result"},
]


class IssueAgent:
    """问题分析 Agent"""

    def __init__(self):
        self.llm = llm_service
        self.tools = tool_registry.get_tools()
        self.tool_schemas = tool_registry.get_tool_schemas()
        self.api_client = backend_client

    async def analyze(self, issue_data: dict, task_id: int = None) -> dict:
        start_time = time.time()
        tool_call_records = []
        evidence = []

        extracted_info = {
            "trace_id": None,
            "error_type": None,
            "related_services": [],
            "environment": issue_data.get("environment", ""),
            "keywords": [],
        }

        current_step = 1
        total_steps = len(PREDEFINED_STEPS)

        try:
            # Step 1: 提取关键信息
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "正在提取关键信息...")
            extracted_info = await self._extract_key_info(issue_data)
            tool_call_records.append(self._create_tool_record(1, "extract_info", str(extracted_info), "成功"))

            # Step 2: 查询日志
            current_step = 2
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "正在查询日志...")
            if extracted_info.get("trace_id"):
                log_result = await self._query_logs(extracted_info["trace_id"])
                if log_result.success:
                    evidence.append({"source": "log_query", "content": log_result.summary, "relevance": "提供了问题发生时的详细上下文"})
                    tool_call_records.append(self._create_tool_record(2, "query_logs", extracted_info["trace_id"], log_result.summary))

            # Step 3: 查询服务信息
            current_step = 3
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "正在查询服务信息...")
            service_name = extracted_info.get("related_services", [issue_data.get("service_name")])[0] if extracted_info.get("related_services") or issue_data.get("service_name") else None
            if service_name:
                service_result = await self._query_service_info(service_name, issue_data.get("project_id"))
                if service_result.success:
                    evidence.append({"source": "service_info", "content": service_result.summary, "relevance": "提供了服务的配置和依赖信息"})
                    tool_call_records.append(self._create_tool_record(3, "get_service_info", service_name, service_result.summary))

            # Step 4: LLM 自主决策
            current_step = 4
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "LLM 正在分析是否需要更多数据...")
            llm_decision = await self._llm_decide_more_data(issue_data, extracted_info, evidence)
            tool_call_records.append(self._create_tool_record(4, "llm_decision", "", llm_decision.get("reason", "")))

            if llm_decision.get("needs_history"):
                await self._query_history_issues(issue_data, evidence, tool_call_records)
            if llm_decision.get("needs_knowledge"):
                await self._query_knowledge_base(issue_data, evidence, tool_call_records)

            # Step 7: 生成分析报告
            current_step = 7
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "正在生成分析报告...")
            report = await self._generate_report(issue_data, extracted_info, evidence)
            tool_call_records.append(self._create_tool_record(7, "generate_report", "", "报告已生成"))

            # Step 8: 保存结果
            current_step = 8
            await self._update_progress(task_id, f"{current_step}/{total_steps}", "正在保存结果...")

            duration = int((time.time() - start_time) * 1000)
            report["tool_calls"] = tool_call_records
            report["duration_ms"] = duration

            return report

        except Exception as e:
            logger.error(f"Agent analysis error: {e}")
            return {"summary": f"分析失败: {str(e)}", "issue_type": "unknown", "error": str(e), "tool_calls": tool_call_records}

    async def _update_progress(self, task_id: Optional[int], progress: str, current_step: str):
        if task_id:
            try:
                await self.api_client.update_task_progress(task_id, progress, current_step)
            except Exception as e:
                logger.warning(f"Failed to update progress: {e}")

    async def _extract_key_info(self, issue_data: dict) -> dict:
        prompt = f"""从以下问题描述中提取关键信息：

问题标题: {issue_data.get('title', '')}
问题描述: {issue_data.get('description', '')}
错误信息: {issue_data.get('error_message', '')}
日志片段: {issue_data.get('log_excerpt', '')}

请提取以下信息（JSON格式）：
- trace_id: Trace ID（如果有）
- error_type: 错误类型
- related_services: 相关的服务名称列表
- keywords: 用于搜索的关键词列表
- environment: 环境（dev/test/staging/prod）

只返回 JSON，不要其他文字。"""

        from app.prompts.issue_analysis import SYSTEM_PROMPT
        response = await self.llm.chat(SYSTEM_PROMPT, prompt)

        try:
            json_str = self._extract_json(response)
            return json.loads(json_str)
        except:
            return {"trace_id": None, "error_type": None, "related_services": [], "keywords": []}

    async def _query_logs(self, trace_id: str) -> ToolResult:
        for tool in self.tools:
            if tool.name == "query_logs":
                return await tool.execute(trace_id=trace_id)
        return ToolResult(success=False, error="日志查询工具未找到")

    async def _query_service_info(self, service_name: str, project_id: int) -> ToolResult:
        for tool in self.tools:
            if tool.name == "get_service_info":
                return await tool.execute(service_name=service_name, project_id=project_id)
        return ToolResult(success=False, error="服务信息工具未找到")

    async def _llm_decide_more_data(self, issue_data: dict, extracted_info: dict, evidence: list) -> dict:
        context = f"""当前问题: {issue_data.get('title', '')}

已提取的关键信息:
{json.dumps(extracted_info, ensure_ascii=False)}

已获取的证据:
{json.dumps(evidence, ensure_ascii=False)}

根据已有信息，判断是否需要查询以下内容：
1. 历史问题: 如果需要参考类似问题的解决方案
2. 知识库: 如果需要查阅排查文档

请返回 JSON：
- needs_history: true/false
- needs_knowledge: true/false
- reason: 判断理由

只返回 JSON。"""

        from app.prompts.issue_analysis import SYSTEM_PROMPT
        response = await self.llm.chat(SYSTEM_PROMPT, context)

        try:
            json_str = self._extract_json(response)
            return json.loads(json_str)
        except:
            return {"needs_history": True, "needs_knowledge": True, "reason": "默认需要查询"}

    async def _query_history_issues(self, issue_data: dict, evidence: list, tool_call_records: list):
        keywords = issue_data.get('title', '') + ' ' + issue_data.get('error_message', '')
        for tool in self.tools:
            if tool.name == "search_history_issues":
                result = await tool.execute(keyword=keywords[:100], project_id=issue_data.get('project_id'))
                if result.success and result.data:
                    evidence.append({"source": "history_issues", "content": result.summary, "relevance": "提供了类似问题的历史解决方案"})
                    tool_call_records.append(self._create_tool_record(5, "search_history_issues", keywords[:50], result.summary))
                break

    async def _query_knowledge_base(self, issue_data: dict, evidence: list, tool_call_records: list):
        """查询知识库 - 优先使用 RAG 检索"""
        keywords = issue_data.get('title', '')

        # 优先使用 RAG 检索
        for tool in self.tools:
            if tool.name == "rag_search":
                result = await tool.execute(query=keywords[:100], top_k=5)
                if result.success and result.data:
                    evidence.append({"source": "knowledge_base", "content": result.summary, "relevance": "提供了基于语义检索的排查文档"})
                    tool_call_records.append(self._create_tool_record(6, "rag_search", keywords[:50], result.summary))
                return

        # 降级：使用传统关键词搜索
        for tool in self.tools:
            if tool.name == "search_knowledge_base":
                result = await tool.execute(keyword=keywords[:100])
                if result.success and result.data:
                    evidence.append({"source": "knowledge_base", "content": result.summary, "relevance": "提供了相关的排查文档"})
                    tool_call_records.append(self._create_tool_record(6, "search_knowledge_base", keywords[:50], result.summary))
                break

    async def _generate_report(self, issue_data: dict, extracted_info: dict, evidence: list) -> dict:
        context = f"""请根据以下信息生成问题分析报告：

## 问题信息
标题: {issue_data.get('title', '')}
描述: {issue_data.get('description', '')}
环境: {issue_data.get('environment', '')}

## 已提取的关键信息
{json.dumps(extracted_info, ensure_ascii=False)}

## 获取的证据
{json.dumps(evidence, ensure_ascii=False)}

请生成以下格式的报告（JSON）：
- summary: 问题摘要（一句话）
- issue_type: 问题类型
- related_services: 关联服务列表
- suspected_cause: 疑似原因
- suggestions: 排查建议列表（3-5条）
- missing_info: 缺失信息列表
- next_steps: 后续待办列表
- confidence: 置信度（0-1）

只返回 JSON。"""

        from app.prompts.issue_analysis import SYSTEM_PROMPT
        response = await self.llm.chat(SYSTEM_PROMPT, context)

        try:
            json_str = self._extract_json(response)
            report = json.loads(json_str)
            return report
        except:
            return {"summary": issue_data.get('title', ''), "issue_type": "unknown", "suspected_cause": "分析失败", "suggestions": ["请人工排查"], "confidence": 0.3}

    def _create_tool_record(self, step: int, tool_name: str, input_data: str, output: str) -> dict:
        return {"step": step, "tool_name": tool_name, "input": input_data[:200] if input_data else "", "output": output[:500] if output else "", "thought": "", "executed_at": datetime.now().isoformat(), "duration_ms": 0}

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        start = text.find("{")
        if start != -1:
            depth = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                return text[start:end]
        return text


# 全局 Agent 实例
issue_agent = IssueAgent()
