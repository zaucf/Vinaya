"""Vinaya 本地客户端。

直接调用 engine，不需要 HTTP 服务���。适合嵌入到 AI 系统中。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from vinaya.types import Decision, JudgmentResult, JudgmentSummary, RiskLevel


class VinayaLocalClient:
    """Vinaya 本地客户端。

    直接调用 engine，无需 HTTP 服务器。

    Example:
        >>> # Mock 模式（用于测试）
        >>> client = VinayaLocalClient(use_mock=True)
        >>> result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")

        >>> # 本地 LLM 模式
        >>> from my_llm import my_chat_json
        >>> from my_rules import get_rules
        >>> client = VinayaLocalClient(
        ...     chat_fn=my_chat_json,
        ...     rules_provider=get_rules
        ... )
        >>> result = client.judge(...)
    """

    def __init__(
        self,
        *,
        use_mock: bool = False,
        chat_fn: Callable[[str, str], dict[str, Any]] | None = None,
        rules_provider: Callable | None = None,
    ):
        """初始化本地客户端。

        Args:
            use_mock: 是否使用 mock 模式（快速返回，不调用 LLM）
            chat_fn: LLM 调用函数，签名为 (system_prompt: str, user_prompt: str) -> dict
            rules_provider: 规则配置加载函数

        Note:
            如果 use_mock=False，必须提供 chat_fn。
            rules_provider 是可选的，不提供时使用默认配置。
        """
        self.use_mock = use_mock
        self.chat_fn = chat_fn
        self.rules_provider = rules_provider

        if not use_mock and chat_fn is None:
            raise ValueError("chat_fn 参数在非 mock 模式下是必需的")

    def judge(
        self,
        *,
        title: str,
        request_text: str,
        domain: str,
        risk_level: RiskLevel,
        context: str = "",
        request_model_id: str | None = None,
    ) -> JudgmentResult:
        """执行判断请求。

        Args:
            title: 请求标题
            request_text: 请求文本
            domain: 领域
            risk_level: 风险等级
            context: 额外上下文
            request_model_id: 请求模型 ID（可选）

        Returns:
            判断结果，包含摘要和完整报告
        """
        from packages.engine.vinaya_engine.precept_enforcer import enforce_precepts

        request_id = f"vinaya-{uuid4().hex[:12]}"
        request: dict[str, Any] = {
            "requestId": request_id,
            "requestModelId": request_model_id or "local",
            "title": title,
            "requestText": request_text,
            "domain": domain,
            "riskLevel": risk_level,
            "context": context,
        }

        if self.use_mock:
            # 使用 mock pipeline
            from packages.engine.vinaya_engine import run_vinaya_pipeline

            report = run_vinaya_pipeline(request)
        else:
            # 使用真实 LLM
            from packages.engine.vinaya_engine.llm_pipeline import run_vinaya_llm_pipeline

            report = run_vinaya_llm_pipeline(
                request,
                chat_fn=self.chat_fn,  # type: ignore
                rules_provider=self.rules_provider,
            )

        # 应用戒律硬约束
        report = enforce_precepts(
            report,
            rules_provider=self.rules_provider,
        )

        return JudgmentResult.from_report(request_id, report)


def _mock_rules_config() -> Any:
    """Mock 规则配置（用于本地客户端的默认行为）。"""
    from dataclasses import dataclass

    @dataclass
    class MockPrecept:
        name: str
        enabled: bool
        description: str
        severity: str

    @dataclass
    class MockConfig:
        precepts: list[MockPrecept]
        risk_thresholds: dict[str, str]

    return MockConfig(
        precepts=[
            MockPrecept(
                name="无害性",
                enabled=True,
                description="不对任何有情众生造成伤害",
                severity="block",
            ),
            MockPrecept(
                name="真实性",
                enabled=True,
                description="不传播虚假或误导性信息",
                severity="block",
            ),
            MockPrecept(
                name="公正性",
                enabled=True,
                description="不偏袒特定群体或利益相关方",
                severity="warning",
            ),
            MockPrecept(
                name="合法性",
                enabled=True,
                description="遵守相关法律法规",
                severity="block",
            ),
            MockPrecept(
                name="隐私保护",
                enabled=True,
                description="保护个人隐私和数据安全",
                severity="warning",
            ),
        ],
        risk_thresholds={
            "auto_allow_max_risk": "low",
            "force_human_review_min_risk": "high",
        },
    )
