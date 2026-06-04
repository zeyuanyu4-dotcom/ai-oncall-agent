"""
Base Tool Definition
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    summary: str = ""  # 工具结果摘要，供 LLM 理解


class BaseTool(ABC):
    """工具基类"""

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def get_schema(self) -> dict:
        """获取工具 schema（供 LangChain 使用）"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }

    def _get_parameters_schema(self) -> dict:
        """获取参数 schema"""
        return {"type": "object", "properties": {}, "required": []}
