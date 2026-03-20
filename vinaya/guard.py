"""Vinaya Guard 装饰器。

用于在函数执行前自动调用 Vinaya 判断，
根据结果决定是否允许执行。
"""

from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any


class VinayaDeferError(Exception):
    """判断结果为 defer 时抛出。"""

    def __init__(self, summary: Any = None):
        self.summary = summary
        super().__init__(
            f"Vinaya defer: {summary.reasoning if summary else 'deferred'}"
        )


class VinayaStopError(Exception):
    """判断结果为 stop 时抛出。"""

    def __init__(self, summary: Any = None):
        self.summary = summary
        super().__init__(
            f"Vinaya stop: {summary.reasoning if summary else 'stopped'}"
        )


def vinaya_guard(
    client: Any,
    *,
    domain: str = "general",
    risk_level: str = "medium",
):
    """Vinaya 守卫装饰器。

    在被装饰函数执行前调用 Vinaya 判断：
    - allow → 正常执行函数
    - defer → raise VinayaDeferError
    - stop  → raise VinayaStopError

    支持同步和异步函数。

    Args:
        client: VinayaClient 或 VinayaLocalClient 实例
        domain: 领域
        risk_level: 风险等级

    Example:
        >>> from vinaya import VinayaLocalClient, vinaya_guard
        >>> client = VinayaLocalClient(use_mock=True)
        >>> @vinaya_guard(client, domain="ops", risk_level="low")
        ... def do_something(action: str):
        ...     return f"executed: {action}"
        >>> do_something("test")  # Vinaya 判断 allow 时正常返回
    """
    def decorator(fn):
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                title = f"{fn.__module__}.{fn.__qualname__}"
                request_text = f"调用函数 {fn.__qualname__}，参数: {args}, {kwargs}"

                # 判断客户端是否为异步
                if hasattr(client, "judge") and inspect.iscoroutinefunction(client.judge):
                    result = await client.judge(
                        title=title,
                        request_text=request_text,
                        domain=domain,
                        risk_level=risk_level,
                    )
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: client.judge(
                            title=title,
                            request_text=request_text,
                            domain=domain,
                            risk_level=risk_level,
                        ),
                    )

                decision = result.summary.decision
                if decision == "stop":
                    raise VinayaStopError(result.summary)
                if decision == "defer":
                    raise VinayaDeferError(result.summary)

                return await fn(*args, **kwargs)

            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                title = f"{fn.__module__}.{fn.__qualname__}"
                request_text = f"调用函数 {fn.__qualname__}，参数: {args}, {kwargs}"

                result = client.judge(
                    title=title,
                    request_text=request_text,
                    domain=domain,
                    risk_level=risk_level,
                )

                decision = result.summary.decision
                if decision == "stop":
                    raise VinayaStopError(result.summary)
                if decision == "defer":
                    raise VinayaDeferError(result.summary)

                return fn(*args, **kwargs)

            return sync_wrapper

    return decorator
