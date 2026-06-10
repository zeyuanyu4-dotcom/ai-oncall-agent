"""CapabilityService gRPC 实现.

暴露给 Go 后端调用：
- GenerateText: 让 Go 后端复用 Python 的 LLM 调用

注意：VectorizeText 已迁出到 RagService（独立 rag-engine 进程）。
本服务不再含向量化能力。
"""
import logging

import grpc
from grpc.aio import ServicerContext

from app.core.context import set_current_token, clear_current_token
from app.gen.proto.capability.v1 import capability_pb2, capability_pb2_grpc
from app.grpc_server.interceptor import _extract_token
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class CapabilityServiceServicer(capability_pb2_grpc.CapabilityServiceServicer):
    """CapabilityService - GenerateText（向量化已迁到 RagService）."""

    async def GenerateText(
        self,
        request: capability_pb2.GenerateTextRequest,
        context: ServicerContext,
    ) -> capability_pb2.GenerateTextResponse:
        token = _extract_token(context.invocation_metadata())
        set_current_token(token)
        try:
            logger.info(
                "Capability.GenerateText | has_token=%s | model=%s | max_tokens=%s",
                bool(token), request.model, request.max_tokens,
            )
            sys_prompt = (
                "你是一个专业的运维工程师，请根据用户提供的信息生成简洁、专业的分析内容。"
            )
            text = await llm_service.chat(sys_prompt, request.prompt)
            return capability_pb2.GenerateTextResponse(
                text=text, prompt_tokens=0, completion_tokens=0,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Capability.GenerateText failed: %s", e)
            await context.abort(grpc.StatusCode.INTERNAL, f"GenerateText failed: {e}")
            return capability_pb2.GenerateTextResponse()
        finally:
            clear_current_token()

    async def VectorizeText(
        self,
        request: capability_pb2.VectorizeTextRequest,
        context: ServicerContext,
    ) -> capability_pb2.VectorizeTextResponse:
        """已废弃: 向量化功能已迁到 RagService.

        保留空实现以满足 proto 兼容性。
        Go 后端应改调 RagService.VectorizeText。
        """
        logger.warning(
            "CapabilityService.VectorizeText is deprecated; "
            "use RagService.VectorizeText instead."
        )
        await context.abort(
            grpc.StatusCode.UNIMPLEMENTED,
            "VectorizeText has been moved to RagService",
        )
        return capability_pb2.VectorizeTextResponse()
