"""
Issue Analysis Service
"""
import logging
from typing import Dict, Any

from app.models.schemas import AnalysisResult, KeyInfo
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AnalysisService:
    """问题分析服务"""

    async def analyze(self, issue_data: Dict[str, Any]) -> AnalysisResult:
        """
        分析问题单

        Args:
            issue_data: 问题数据

        Returns:
            AnalysisResult: 分析结果
        """
        try:
            # 调用 LLM 进行分析
            raw_result = await llm_service.analyze_issue(issue_data)

            # 构建结构化结果
            key_info = None
            if raw_result.get("key_info"):
                key_info_data = raw_result["key_info"]
                key_info = KeyInfo(
                    error_code=key_info_data.get("error_code"),
                    error_type=key_info_data.get("error_type"),
                    affected_endpoint=key_info_data.get("affected_endpoint"),
                    error_time=key_info_data.get("error_time"),
                    trace_id=key_info_data.get("trace_id"),
                    additional_info=key_info_data.get("additional_info")
                )

            result = AnalysisResult(
                summary=raw_result.get("summary", ""),
                issue_type=raw_result.get("issue_type", "other"),
                environment=raw_result.get("environment"),
                related_services=raw_result.get("related_services", []),
                priority=raw_result.get("priority", "P3"),
                confidence=raw_result.get("confidence", 0.5),
                key_info=key_info,
                missing_info=raw_result.get("missing_info", []),
                suggestions=raw_result.get("suggestions", [])
            )

            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise


# 全局分析服务实例
analysis_service = AnalysisService()
