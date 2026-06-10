"""rag-engine 进程入口.

启动：
- 一个 aio gRPC server，监听 RAG_GRPC_PORT（默认 50052）
- 注册 RagService
- 启用 reflection（grpcurl 调试）

与 agent-orchestrator 不在同进程，所以 Chroma 锁、sentence-transformers 模型
都不会和 Agent 抢资源。

启动方式：
    python -m app.rag_engine.main
"""
import asyncio
import logging
import os
import signal
from concurrent import futures

import grpc
from grpc import aio as grpc_aio
from grpc_reflection.v1alpha import reflection

from app.config import settings  # 复用同一份 settings
from app.gen.proto.rag.v1 import rag_pb2, rag_pb2_grpc
from app.rag_engine.rag_service import RagServiceServicer

logger = logging.getLogger(__name__)


async def serve() -> grpc_aio.Server:
    """启动并返回 aio gRPC server（不阻塞）."""
    server = grpc_aio.server(
        migration_thread_pool=futures.ThreadPoolExecutor(
            max_workers=settings.GRPC_MAX_WORKERS
        ),
        options=[
            ("grpc.so_reuseport", 0),
            ("grpc.max_send_message_length", 64 * 1024 * 1024),
            ("grpc.max_receive_message_length", 64 * 1024 * 1024),
        ],
    )

    rag_pb2_grpc.add_RagServiceServicer_to_server(RagServiceServicer(), server)

    # reflection
    service_names = (
        rag_pb2.DESCRIPTOR.services_by_name["RagService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    addr = f"{settings.GRPC_HOST}:{settings.RAG_GRPC_PORT}"
    server.add_insecure_port(addr)
    await server.start()
    logger.info(
        "rag-engine gRPC server listening on %s | service=%s",
        addr, rag_pb2.DESCRIPTOR.services_by_name["RagService"].full_name,
    )
    return server


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting rag-engine ...")
    logger.info("CHROMA_PATH=%s", os.getenv("CHROMA_PATH", "./data/chroma"))
    logger.info("EMBEDDING_MODEL=%s", os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    server = await serve()

    # 信号处理：优雅停机
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _on_signal(signame):
        logger.info("Received signal %s, stopping rag-engine ...", signame)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _on_signal, sig.name)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler；忽略
            pass

    try:
        await stop_event.wait()
    finally:
        logger.info("Stopping gRPC server (grace=10s) ...")
        await server.stop(grace=10.0)
        logger.info("rag-engine stopped")


if __name__ == "__main__":
    asyncio.run(main())
