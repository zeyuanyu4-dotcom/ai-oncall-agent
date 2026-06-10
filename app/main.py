"""
AI Oncall Agent - Main Application

启动：
1. FastAPI HTTP server（兼容旧调用）
2. gRPC server（AgentService + CapabilityService，给 Go 后端使用）

两个 server 跑在同一个 Python 进程内。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.models.schemas import HealthResponse
from app.api.routes import analysis
from app.api.routes import agent
from app.api.routes import rag
from app.api.routes import generate
from app.core.context import set_current_token, clear_current_token
from app.mq import RabbitMQClient, MQConfig
from app.middleware import setup_rate_limiting
from app.grpc_server.server import start_grpc_in_background, stop_grpc

# 配置日志
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class JWTContextMiddleware(BaseHTTPMiddleware):
    """JWT 上下文中间件 - 提取请求中的 JWT 并存入上下文"""

    # 不打印 token 的 endpoint（健康检查等会产生大量噪音）
    _SKIP_LOG_PATHS = {"/", "/health"}

    async def dispatch(self, request: Request, call_next):
        # 提取 Authorization header 中的 JWT
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀

        # 存入上下文
        set_current_token(token)

        # 调试日志：脱敏后记录 token 状态
        if request.url.path not in self._SKIP_LOG_PATHS:
            if token:
                logger.info(
                    "AI request received with user token",
                    extra={"path": request.url.path, "token_prefix": token[:10] + "..."},
                )
            else:
                logger.warning(
                    "AI request received WITHOUT user token (内部工具调用将 401)",
                    extra={"path": request.url.path, "client": request.client.host if request.client else "unknown"},
                )

        try:
            response = await call_next(request)
        finally:
            # 请求结束后清理
            clear_current_token()

        return response


# 在模块级持有 gRPC server 实例，lifespan 里 start/stop
_grpc_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    global _grpc_server
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")

    # 启动 gRPC server（与 HTTP 并行）
    _grpc_server = await start_grpc_in_background()
    if _grpc_server is not None:
        logger.info("gRPC server started")
    else:
        logger.info("gRPC server not started (disabled by config)")

    # 初始化 RabbitMQ（如果启用）
    if settings.RABBITMQ_ENABLED:
        mq_config = MQConfig(
            url=settings.RABBITMQ_URL,
            exchange=settings.RABBITMQ_EXCHANGE,
            command_queue=settings.RABBITMQ_COMMAND_QUEUE,
            result_queue=settings.RABBITMQ_RESULT_QUEUE,
            progress_queue=settings.RABBITMQ_PROGRESS_QUEUE,
            enabled=True
        )
        analysis.init_mq_client(mq_config)
        logger.info("RabbitMQ client initialized")
    else:
        logger.info("RabbitMQ disabled, running in HTTP-only mode")

    yield

    # 关闭 MQ 连接
    if analysis.mq_client:
        analysis.mq_client.close()

    # 关闭 gRPC server
    await stop_grpc(_grpc_server)
    _grpc_server = None

    logger.info("Shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Oncall Agent - 智能问题分析服务",
    lifespan=lifespan
)

# JWT 上下文中间件（先添加，后执行）
app.add_middleware(JWTContextMiddleware)

# 配置 CORS（后添加，先执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化限流（必须在模块级，因为 add_middleware 不能在 lifespan 里调用）
setup_rate_limiting(app)
logger.info("Rate limiting initialized")

# 注册路由
app.include_router(analysis.router)
app.include_router(agent.router)
app.include_router(rag.router)
app.include_router(generate.router)


@app.get("/", response_model=HealthResponse)
async def root():
    """根路径 - 健康检查"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        llm_provider=settings.LLM_PROVIDER
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        llm_provider=settings.LLM_PROVIDER
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
