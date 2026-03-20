"""Vinaya FastAPI 中间件。

对匹配路径的请求自动执行 Vinaya 判断，
stop 返回 403，defer 可配置行为。
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from typing import Any


class VinayaMiddleware:
    """FastAPI / Starlette ASGI 中间件。

    对匹配路径的请求自动调用 Vinaya 判断：
    - allow → 放行并在 request.state.vinaya 附加判断结果
    - stop  → 返回 403
    - defer → 根据 defer_action 决定（默认 403）

    Args:
        app: ASGI 应用
        client: VinayaClient / VinayaLocalClient / AsyncVinayaClient 实例
        paths: 需要拦截的路径正则列表（为 None 时拦截所有请求）
        domain: 领域
        risk_level: 风险等级
        defer_action: defer 时的行为 - "block"(403) 或 "pass"(放行)

    Example:
        >>> from fastapi import FastAPI
        >>> from vinaya import VinayaClient
        >>> from vinaya.middleware import VinayaMiddleware
        >>> app = FastAPI()
        >>> client = VinayaClient()
        >>> app.add_middleware(
        ...     VinayaMiddleware,
        ...     client=client,
        ...     paths=["/api/dangerous/.*"],
        ... )
    """

    def __init__(
        self,
        app: Any,
        client: Any,
        paths: list[str] | None = None,
        domain: str = "api",
        risk_level: str = "medium",
        defer_action: str = "block",
    ):
        self.app = app
        self.client = client
        self.path_patterns = [re.compile(p) for p in paths] if paths else None
        self.domain = domain
        self.risk_level = risk_level
        self.defer_action = defer_action

    def _should_check(self, path: str) -> bool:
        if self.path_patterns is None:
            return True
        return any(p.fullmatch(path) for p in self.path_patterns)

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if not self._should_check(path):
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        title = f"{method} {path}"
        request_text = f"HTTP {method} request to {path}"

        try:
            if hasattr(self.client, "judge") and inspect.iscoroutinefunction(self.client.judge):
                result = await self.client.judge(
                    title=title,
                    request_text=request_text,
                    domain=self.domain,
                    risk_level=self.risk_level,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.judge(
                        title=title,
                        request_text=request_text,
                        domain=self.domain,
                        risk_level=self.risk_level,
                    ),
                )
        except Exception:
            # 判断失败时放行，避免阻断正常请求
            await self.app(scope, receive, send)
            return

        decision = result.summary.decision

        if decision == "stop":
            await self._send_403(send, "Vinaya: 请求已被止行")
            return

        if decision == "defer" and self.defer_action == "block":
            await self._send_403(send, "Vinaya: 请求需要人工复核")
            return

        # allow 或 defer(pass 模式) → 放行
        # 通过 scope 传递判断结果（Starlette/FastAPI 会映射到 request.state）
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["vinaya"] = result

        await self.app(scope, receive, send)

    async def _send_403(self, send: Any, message: str) -> None:
        body = json.dumps({"detail": message}, ensure_ascii=False).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
