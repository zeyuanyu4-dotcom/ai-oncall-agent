"""gRPC Server 拦截器：从入站 metadata 提取 JWT.

注：gRPC Python 的 ServerInterceptor 只在 service 路由时触发，
不能在 RPC handler 内部插入 before/after 钩子。因此本拦截器只负责：
1. 日志：记录每个调用是否带 token、token 前缀
2. 透传：服务实现（agent_service.py / capability_service.py）内部
   从 context.invocation_metadata() 重新读取并写入 ContextVar。

这种方式与 Go 端 gRPC interceptor 模型等价。
"""
import logging
from typing import Optional

import grpc

logger = logging.getLogger(__name__)

_METADATA_AUTH_KEY = "authorization"


def _extract_token(md_invocation_metadata) -> Optional[str]:
    """从 gRPC 元数据中提取 bearer token.

    md 可能是 dict、tuple of (key, value) 对、list of pairs.
    """
    if md_invocation_metadata is None:
        return None
    raw: Optional[str] = None
    # 先用 dict-like 访问
    if hasattr(md_invocation_metadata, "get") and not isinstance(md_invocation_metadata, (list, tuple)):
        raw = md_invocation_metadata.get(_METADATA_AUTH_KEY)
    # 退路：遍历 items
    if raw is None:
        items = None
        if hasattr(md_invocation_metadata, "items"):
            items = list(md_invocation_metadata.items())
        elif isinstance(md_invocation_metadata, (list, tuple)):
            items = list(md_invocation_metadata)
        if items:
            for k, v in items:
                if isinstance(k, str) and k.lower() == _METADATA_AUTH_KEY:
                    raw = v
                    break
    if not raw:
        return None
    raw = raw.strip()
    if raw.lower().startswith("bearer "):
        return raw[7:].strip()
    return raw


def _token_prefix(token: Optional[str], n: int = 10) -> str:
    if not token:
        return ""
    return token[:n] + "..." if len(token) > n else token


class JWTAuthServerInterceptor(grpc.ServerInterceptor):
    """Server interceptor: 记录调用方身份（脱敏 token 前缀）.

    实际的 JWT 注入由各服务实现从 context.invocation_metadata() 自行处理。
    """

    def intercept_service(self, continuation, handler_call_details):
        md = handler_call_details.invocation_metadata
        token = _extract_token(md)
        method = handler_call_details.method

        if token:
            logger.debug(
                "gRPC call with token | method=%s | token_prefix=%s",
                method, _token_prefix(token),
            )
        else:
            logger.warning("gRPC call WITHOUT token | method=%s", method)

        return continuation(handler_call_details)


# 保留旧名以免破坏引用
JWTAuthUnaryInterceptor = JWTAuthServerInterceptor
JWTAuthStreamInterceptor = JWTAuthServerInterceptor
