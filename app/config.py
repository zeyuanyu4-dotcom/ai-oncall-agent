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


settings = Settings()
