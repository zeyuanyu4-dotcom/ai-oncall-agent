"""gRPC server bootstrap.

启动一个 aio gRPC server，注册 AgentService / CapabilityService 两个服务。
与 FastAPI HTTP 服务共用一个进程。
"""
import asyncio
import logging
from concurrent import futures

import grpc
from grpc import aio as grpc_aio
from grpc_reflection.v1alpha import reflection

from app.config import settings
from app.gen.proto.agent.v1 import agent_pb2
from app.gen.proto.capability.v1 import capability_pb2
from app.grpc_server.agent_service import AgentServiceServicer
from app.grpc_server.capability_service import CapabilityServiceServicer

logger = logging.getLogger(__name__)


async def serve_grpc() -> grpc_aio.Server:
    """启动并返回 aio gRPC server（不阻塞），调用方负责 wait_for_termination."""
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

    # 注册服务
    from app.gen.proto.agent.v1 import agent_pb2_grpc
    from app.gen.proto.capability.v1 import capability_pb2_grpc

    agent_pb2_grpc.add_AgentServiceServicer_to_server(AgentServiceServicer(), server)
    capability_pb2_grpc.add_CapabilityServiceServicer_to_server(
        CapabilityServiceServicer(), server
    )

    # 开启 reflection：方便 grpcurl/grpcui 调试
    service_names = (
        agent_pb2.DESCRIPTOR.services_by_name["AgentService"].full_name,
        capability_pb2.DESCRIPTOR.services_by_name["CapabilityService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    addr = f"{settings.GRPC_HOST}:{settings.GRPC_PORT}"
    server.add_insecure_port(addr)
    await server.start()
    logger.info("gRPC server listening on %s | services=%s",
                addr, [s for s in service_names if s != reflection.SERVICE_NAME])
    return server


async def start_grpc_in_background() -> grpc_aio.Server | None:
    """在 FastAPI lifespan 启动时调用；返回 None 表示未启用."""
    if not settings.GRPC_ENABLED:
        logger.info("gRPC server disabled by config")
        return None
    server = await serve_grpc()
    return server


async def stop_grpc(server: grpc_aio.Server | None) -> None:
    if server is None:
        return
    logger.info("Stopping gRPC server...")
    await server.stop(grace=5.0)
    logger.info("gRPC server stopped")
