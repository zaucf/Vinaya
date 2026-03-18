"""Vinaya SDK 类型定义。

提供机器友好的数据结构，用于 AI 系统集成。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]
Decision = Literal["allow", "defer", "stop"]
PreceptStatus = Literal["pass", "warning", "block"]


@dataclass(frozen=True)
class PreceptViolation:
    """戒律违规记录。"""

    name: str
    """戒律名称"""

    status: PreceptStatus
    """状态：pass/warning/block"""

    reason: str
    """违规原因"""


@dataclass(frozen=True)
class JudgmentSummary:
    """判断摘要（机器友好）。

    这是给 AI 系统读取的结构化数据，包含：
    - 核心决策：decision
    - 风险等级：risk_level
    - 硬阻断标记：hard_block
    - 人工复核标记：human_review_required
    - 戒律违规列表：precept_violations
    - 简要推理：reasoning
    """

    request_id: str
    """请求 ID"""

    decision: Decision
    """决策：allow/defer/stop"""

    risk_level: RiskLevel
    """综合风险等级"""

    hard_block: bool
    """是否触发硬阻断（severity=block 的戒律被触发）"""

    human_review_required: bool
    """是否需要人工复核"""

    reasoning: str
    """推理摘要"""

    precept_violations: tuple[PreceptViolation, ...]
    """戒律违规列表"""

    @classmethod
    def from_report(cls, report: dict) -> "JudgmentSummary":
        """从 engine 返回的完整报告中提取摘要。"""
        precepts = report.get("precepts", {})
        findings = precepts.get("preceptFindings", [])

        violations = tuple(
            PreceptViolation(
                name=f.get("name", ""),
                status=f.get("status", "pass"),
                reason=f.get("reason", ""),
            )
            for f in findings
            if f.get("status") in ("warning", "block")
        )

        # 计算综合风险等级
        risks = [
            report.get("intention", {}).get("intentionRisk", "low"),
            report.get("causality", {}).get("causalityRisk", "low"),
            precepts.get("preceptRisk", "low"),
            report.get("deliberation", {}).get("deliberationRisk", "low"),
            report.get("gradualRelease", {}).get("releaseRisk", "low"),
        ]
        if "high" in risks:
            overall_risk: RiskLevel = "high"
        elif "medium" in risks:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return cls(
            request_id=report.get("request", {}).get("requestId", ""),
            decision=report.get("decision", "defer"),
            risk_level=overall_risk,
            hard_block=precepts.get("hardBlock", False),
            human_review_required=precepts.get("humanReviewRequired", False),
            reasoning=report.get("reasoningSummary", ""),
            precept_violations=violations,
        )


@dataclass(frozen=True)
class JudgmentResult:
    """判断结果（摘要 + 完整报告）。

    这是 SDK 返回的完整结果，包含：
    - summary: 机器友好的结构化摘要
    - report: 完整的判断报告（用于人工查看）
    """

    summary: JudgmentSummary
    """判断摘要（机器友好）"""

    report: dict
    """完整的判断报告"""

    @classmethod
    def from_report(cls, request_id: str, report: dict) -> "JudgmentResult":
        """从 engine 返回的完整报告构建结果。"""
        return cls(
            summary=JudgmentSummary.from_report(report),
            report=report,
        )
