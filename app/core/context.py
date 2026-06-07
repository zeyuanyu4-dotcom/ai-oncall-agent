"""
请求上下文管理

使用 contextvars 在异步环境中传递请求级别的数据（如 JWT token）
"""
from contextvars import ContextVar
from typing import Optional

# 当前请求的 JWT token
_current_token: ContextVar[Optional[str]] = ContextVar("current_token", default=None)


def set_current_token(token: Optional[str]) -> None:
    """设置当前请求的 JWT token"""
    _current_token.set(token)


def get_current_token() -> Optional[str]:
    """获取当前请求的 JWT token"""
    return _current_token.get()


def clear_current_token() -> None:
    """清除当前请求的 JWT token（请求结束时调用）"""
    _current_token.set(None)
