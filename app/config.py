"""
AI Oncall Agent Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Service
    APP_NAME: str = "AI Oncall Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))

    # LLM Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "qianfan")  # qianfan, openai, ollama

    # 百度千帆配置
    QIANFAN_AK: str = os.getenv("QIANFAN_AK", "")
    QIANFAN_SK: str = os.getenv("QIANFAN_SK", "")
    QIANFAN_MODEL: str = os.getenv("QIANFAN_MODEL", "ernie-4.0-8k")

    # OpenAI 配置 (可选，也支持 OpenRouter)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Ollama 配置 (可选)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama2")

    # Timeouts
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "30"))

    # RabbitMQ Configuration
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
    RABBITMQ_EXCHANGE: str = os.getenv("RABBITMQ_EXCHANGE", "analysis.exchange")
    RABBITMQ_COMMAND_QUEUE: str = os.getenv("RABBITMQ_COMMAND_QUEUE", "analysis.command.queue")
    RABBITMQ_RESULT_QUEUE: str = os.getenv("RABBITMQ_RESULT_QUEUE", "analysis.result.queue")
    RABBITMQ_PROGRESS_QUEUE: str = os.getenv("RABBITMQ_PROGRESS_QUEUE", "analysis.progress.queue")
    RABBITMQ_ENABLED: bool = os.getenv("RABBITMQ_ENABLED", "false").lower() == "true"

    # gRPC server (被 Go Worker 调用的入站 gRPC 端口)
    GRPC_ENABLED: bool = os.getenv("GRPC_ENABLED", "true").lower() == "true"
    GRPC_HOST: str = os.getenv("GRPC_HOST", "0.0.0.0")
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))
    GRPC_MAX_WORKERS: int = int(os.getenv("GRPC_MAX_WORKERS", "10"))

    # gRPC client: Agent -> Go 后端的 ToolingService
    TOOLING_GRPC_ADDR: str = os.getenv("TOOLING_GRPC_ADDR", "127.0.0.1:50061")
    TOOLING_GRPC_TIMEOUT: int = int(os.getenv("TOOLING_GRPC_TIMEOUT", "30"))

    # gRPC client: agent-orchestrator -> rag-engine
    # (agent-orchestrator 启动时会调这里；rag-engine 自己启动时不需要)
    RAG_GRPC_ADDR: str = os.getenv("RAG_GRPC_ADDR", "127.0.0.1:50052")
    RAG_GRPC_TIMEOUT: int = int(os.getenv("RAG_GRPC_TIMEOUT", "60"))
    # rag-engine 自身监听的端口（用于 K8s 部署时区分）
    RAG_GRPC_PORT: int = int(os.getenv("RAG_GRPC_PORT", "50052"))


settings = Settings()
