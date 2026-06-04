"""
LLM Service - 统一的 LLM 调用封装
"""
import json
import logging
from typing import Optional
from abc import ABC, abstractmethod

from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""

    @abstractmethod
    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 进行对话"""
        pass


class QianfanProvider(BaseLLMProvider):
    """百度千帆 LLM 提供商"""

    def __init__(self):
        import qianfan
        self.client = qianfan.ChatCompletion(ak=settings.QIANFAN_AK, sk=settings.QIANFAN_SK)
        self.model = settings.QIANFAN_MODEL

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用千帆 API"""
        try:
            response = self.client.do(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                top_p=0.9
            )
            return response.body.get("result", "")
        except Exception as e:
            logger.error(f"Qianfan API error: {e}")
            raise


class OpenAIProvider(BaseLLMProvider):
    """OpenAI / OpenRouter LLM 提供商"""

    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.OPENAI_MODEL

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 OpenAI / OpenRouter API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI/OpenRouter API error: {e}")
            raise


class MockProvider(BaseLLMProvider):
    """Mock LLM 提供商（用于测试）"""

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """返回模拟的分析结果"""
        return json.dumps({
            "summary": "模拟分析：这是一个测试环境的登录接口异常问题",
            "issue_type": "service_exception",
            "environment": "test",
            "related_services": ["auth-service", "redis"],
            "priority": "P2",
            "confidence": 0.75,
            "key_info": {
                "error_code": "500",
                "error_type": "internal_error",
                "affected_endpoint": "/api/login",
                "error_time": None,
                "trace_id": None,
                "additional_info": {}
            },
            "missing_info": ["Trace ID", "具体发生时间", "请求参数"],
            "suggestions": [
                "检查 auth-service 服务状态和日志",
                "确认 Redis 连接是否正常",
                "查看最近的配置变更",
                "检查数据库连接状态"
            ]
        }, ensure_ascii=False)


class LLMService:
    """LLM 服务"""

    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self) -> BaseLLMProvider:
        """根据配置获取 LLM 提供商"""
        provider = settings.LLM_PROVIDER.lower()

        if provider == "qianfan":
            if not settings.QIANFAN_AK or not settings.QIANFAN_SK:
                logger.warning("Qianfan credentials not configured, using mock provider")
                return MockProvider()
            return QianfanProvider()

        elif provider == "openai" or provider == "openrouter":
            if not settings.OPENAI_API_KEY:
                logger.warning("OpenAI/OpenRouter API key not configured, using mock provider")
                return MockProvider()
            return OpenAIProvider()

        elif provider == "mock":
            return MockProvider()

        else:
            logger.warning(f"Unknown LLM provider: {provider}, using mock provider")
            return MockProvider()

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 进行对话"""
        return await self.provider.chat(system_prompt, user_prompt)

    async def analyze_issue(self, issue_data: dict) -> dict:
        """
        分析问题单
        """
        from app.prompts.issue_analysis import ISSUE_ANALYSIS_PROMPT, SYSTEM_PROMPT

        # 构建用户提示
        user_prompt = ISSUE_ANALYSIS_PROMPT.format(
            issue_no=issue_data.get("issue_no", ""),
            title=issue_data.get("title", ""),
            description=issue_data.get("description", "无"),
            error_message=issue_data.get("error_message", "无"),
            log_excerpt=issue_data.get("log_excerpt", "无"),
            environment=issue_data.get("environment", "未知"),
            project_name=issue_data.get("project_name", "未知"),
            service_name=issue_data.get("service_name", "未知"),
            impact_scope=issue_data.get("impact_scope", "未知")
        )

        # 调用 LLM
        response = await self.chat(SYSTEM_PROMPT, user_prompt)

        # 解析 JSON 响应
        try:
            # 尝试提取 JSON
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            raise ValueError("LLM 返回的不是有效的 JSON 格式")

    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON"""
        text = text.strip()

        # 如果被 markdown 代码块包裹
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # 尝试找到 JSON 对象
        start = text.find("{")
        if start != -1:
            # 找到最后一个 }
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


# 全局 LLM 服务实例
llm_service = LLMService()
