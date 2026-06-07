"""
Rate Limiting Middleware
基于 SlowAPI 实现限流
"""
import logging
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logger = logging.getLogger(__name__)


def get_user_id(request: Request) -> str:
    """获取用户ID作为限流key"""
    # 从请求状态中获取用户ID
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    # 未登录用户使用IP
    return f"ip:{get_remote_address(request)}"


# 创建限流器
limiter = Limiter(
    key_func=get_user_id,
    default_limits=["200/hour"],  # 默认限制
    storage_uri="redis://127.0.0.1:6379/0",  # Redis 存储
    storage_options={"socket_connect_timeout": 3},
    strategy="fixed-window",  # 固定窗口策略
    enabled=True,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """限流异常处理"""
    logger.warning(f"Rate limit exceeded: {exc.detail}")

    # 计算重试时间
    retry_after = exc.detail.split("Retry in ")[-1].split(" ")[0] if "Retry in" in exc.detail else "60"

    raise HTTPException(
        status_code=429,
        detail=f"请求过于频繁，请{retry_after}秒后重试",
        headers={
            "Retry-After": retry_after,
            "X-RateLimit-Limit": str(exc.limit),
            "X-RateLimit-Remaining": "0",
        }
    )


def setup_rate_limiting(app):
    """设置限流中间件"""
    # 添加限流状态
    app.state.limiter = limiter

    # 添加异常处理
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # 添加中间件
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting middleware initialized")


# 预定义限流装饰器
def login_rate_limit():
    """登录限流：5次/分钟/IP"""
    return limiter.limit("5/minute", key_func=lambda: f"ip:{get_remote_address}")


def ai_analysis_rate_limit():
    """AI 分析限流：20次/小时/用户"""
    return limiter.limit("20/hour")


def vectorize_rate_limit():
    """向量化限流：50次/小时/用户"""
    return limiter.limit("50/hour")


def upload_rate_limit():
    """上传限流：20次/小时/用户"""
    return limiter.limit("20/hour")
