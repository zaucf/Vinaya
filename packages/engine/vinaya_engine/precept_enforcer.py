"""Precept Enforcer — 独立于 LLM 的戒律硬约束层。

这是"戒"的真正执行者。不管 LLM 输出什么，这一层都会：
1. 读取当前五戒配置（哪些启用、severity 是 warning 还是 block）
2. 检查 LLM 输出的 preceptFindings，对 severity=block 的越戒强制止行
3. 根据风险阈值强制调整 decision（"定"的硬约束）
4. 标记是否需要人工复核

这一层的逻辑不依赖 LLM，是纯规则校验。
"""

from __future__ import annotations

from typing import Any

from apps.api.vinaya_api.services.rules import get_rules_config

# 风险等级排序
RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def _risk_ge(a: str, b: str) -> bool:
    """判断风险等级 a 是否 >= b。"""
    return RISK_ORDER.get(a, 0) >= RISK_ORDER.get(b, 0)


def enforce_precepts(report: dict[str, Any]) -> dict[str, Any]:
    """对 LLM/规则引擎的输出做戒律硬约束校验。

    这是判断链的最后一关。LLM 可以建议 allow，但如果触犯了
    severity=block 的戒律，这里会强制覆盖为 stop。

    返回修改后的 report（原地修改并返回）。
    """
    config = get_rules_config()

    # ── 戒：五戒硬约束 ──────────────────────────────

    # 构建启用的戒律配置索引
    precept_config_map = {
        p.name: p for p in config.precepts if p.enabled
    }

    precept_findings = report.get("precepts", {}).get("preceptFindings", [])
    enforced_block = False
    enforcement_reasons: list[str] = []

    for finding in precept_findings:
        name = finding.get("name", "")
        status = finding.get("status", "pass")
        precept_cfg = precept_config_map.get(name)

        if precept_cfg is None:
            # 该戒律未启用，降级为 pass
            finding["status"] = "pass"
            finding["reason"] = f"[系统] {name} 当前未启用，跳过检查。"
            continue

        if status in ("warning", "block") and precept_cfg.severity == "block":
            # severity=block 的戒律被触发 → 强制止行
            finding["status"] = "block"
            enforced_block = True
            enforcement_reasons.append(f"{name}（{finding.get('reason', '')}）")

    # 如果有 severity=block 的戒律被触发，强制覆盖 decision
    if enforced_block:
        report["precepts"]["hardBlock"] = True
        report["precepts"]["humanReviewRequired"] = True
        if report["decision"] != "stop":
            original_decision = report["decision"]
            report["decision"] = "stop"
            block_detail = "；".join(enforcement_reasons)
            report["reasoningSummary"] = (
                f"[戒律强制止行] LLM 原始建议为 {original_decision}，"
                f"但触犯了以下 block 级戒律：{block_detail}。"
                f"系统强制覆盖为 stop。原始分析：{report.get('reasoningSummary', '')}"
            )

    # ── 定：风险阈值硬约束 ──────────────────────────

    thresholds = config.risk_thresholds
    overall_risk = _compute_overall_risk(report)

    # 约束 1：超过 auto_allow_max_risk 的请求不能 allow
    auto_allow_max = thresholds.get("auto_allow_max_risk", "low")
    if report["decision"] == "allow" and _risk_ge(overall_risk, auto_allow_max) and overall_risk != auto_allow_max:
        report["decision"] = "defer"
        report["reasoningSummary"] = (
            f"[风险阈值约束] 综合风险为 {overall_risk}，超过自动放行上限 {auto_allow_max}，"
            f"系统强制从 allow 降级为 defer。{report.get('reasoningSummary', '')}"
        )

    # 约束 2：达到 force_human_review_min_risk 的请求强制人工复核
    force_review_min = thresholds.get("force_human_review_min_risk", "high")
    if _risk_ge(overall_risk, force_review_min):
        report["precepts"]["humanReviewRequired"] = True

    return report


def _compute_overall_risk(report: dict[str, Any]) -> str:
    """从各阶段风险中取最高值。"""
    risks = [
        report.get("intention", {}).get("intentionRisk", "low"),
        report.get("causality", {}).get("causalityRisk", "low"),
        report.get("precepts", {}).get("preceptRisk", "low"),
        report.get("deliberation", {}).get("deliberationRisk", "low"),
        report.get("gradualRelease", {}).get("releaseRisk", "low"),
    ]
    if "high" in risks:
        return "high"
    if "medium" in risks:
        return "medium"
    return "low"
