"""Vinaya SDK — AI judgment purification engine.

这个包提供了两种使用方式：
1. VinayaClient: 远程 HTTP 客户端，连接到 Vinaya API 服务器
2. VinayaLocalClient: 本地客户端，直接调用 engine（适合嵌入 AI 系统）

Example:
    # 远程模式
    from vinaya import VinayaClient
    client = VinayaClient(base_url="http://localhost:8000")
    result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")

    # 本地模式
    from vinaya import VinayaLocalClient
    client = VinayaLocalClient()  # 使用 mock 模式
    result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")
"""

from __future__ import annotations

from vinaya.client import VinayaClient
from vinaya.local import VinayaLocalClient
from vinaya.types import Decision, JudgmentResult, JudgmentSummary, RiskLevel

__all__ = [
    "VinayaClient",
    "VinayaLocalClient",
    "JudgmentResult",
    "JudgmentSummary",
    "Decision",
    "RiskLevel",
]

__version__ = "0.1.0"
