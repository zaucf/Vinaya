"""Vinaya SDK — AI judgment purification engine.

这个包提供了多种使用方式：
1. VinayaClient: 远程 HTTP 客户端，连接到 Vinaya API 服务器
2. VinayaLocalClient: 本地客户端，直接调用 engine（适合嵌入 AI 系统）
3. AsyncVinayaClient: 异步客户端，支持 asyncio
4. vinaya_guard: 装饰器，函数执行前自动判断
5. VinayaMiddleware: FastAPI 中间件，自动拦截匹配路径

Example:
    # 远程模式
    from vinaya import VinayaClient
    client = VinayaClient(base_url="http://localhost:8000")
    result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")

    # 本地模式
    from vinaya import VinayaLocalClient
    client = VinayaLocalClient(use_mock=True)
    result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")

    # 异步模式
    from vinaya import AsyncVinayaClient
    client = AsyncVinayaClient()
    result = await client.judge(title="测试", request_text="...", domain="test", risk_level="low")

    # 装饰器
    from vinaya import VinayaLocalClient, vinaya_guard
    client = VinayaLocalClient(use_mock=True)
    @vinaya_guard(client, domain="ops")
    def do_action(): ...
"""

from __future__ import annotations

from vinaya.async_client import AsyncVinayaClient
from vinaya.client import VinayaClient
from vinaya.guard import VinayaDeferError, VinayaStopError, vinaya_guard
from vinaya.local import VinayaLocalClient
from vinaya.types import (
    Decision,
    JudgmentResult,
    JudgmentSummary,
    ReviewResult,
    RiskLevel,
    StageEvent,
)

__all__ = [
    "AsyncVinayaClient",
    "VinayaClient",
    "VinayaLocalClient",
    "JudgmentResult",
    "JudgmentSummary",
    "StageEvent",
    "ReviewResult",
    "Decision",
    "RiskLevel",
    "vinaya_guard",
    "VinayaDeferError",
    "VinayaStopError",
]

__version__ = "0.2.0"
