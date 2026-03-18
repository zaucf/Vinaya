from __future__ import annotations

import os
from functools import partial
from uuid import uuid4

from apps.api.vinaya_api.llm import chat_json
from apps.api.vinaya_api.repository import get_report, get_request_model, save_report
from apps.api.vinaya_api.schemas import (
    CreateRequestPayload,
    JudgmentSummaryResponse,
    PreceptViolationItem,
    RequestReportResponse,
)
from apps.api.vinaya_api.services.rules import get_rules_config
from packages.engine.vinaya_engine import run_vinaya_llm_pipeline, run_vinaya_pipeline
from packages.engine.vinaya_engine.precept_enforcer import enforce_precepts


def _get_llm_provider_id(request_model_id: str | None) -> str | None:
    """根据请求模型 ID 获取对应的 LLM 供应商 ID。

    Args:
        request_model_id: 请求模型 ID，如果为 "manual" 或 None 则返回 None（使用默认供应商）

    Returns:
        LLM 供应商 ID，如果不需要指定则返回 None
    """
    if not request_model_id or request_model_id == "manual":
        return None

    model = get_request_model(request_model_id)
    if model is None:
        # 请求模型不存在，使用默认供应商
        return None

    return model.llm_provider_id


def _build_summary(report: dict, request_id: str) -> JudgmentSummaryResponse:
    """从完整报告中提取机器友好的摘要。"""
    precepts = report.get("precepts", {})
    findings = precepts.get("preceptFindings", [])

    violations = [
        PreceptViolationItem(
            name=f.get("name", ""),
            status=f.get("status", "pass"),
            reason=f.get("reason", ""),
        )
        for f in findings
        if f.get("status") in ("warning", "block")
    ]

    # 计算综合风险等级
    risks = [
        report.get("intention", {}).get("intentionRisk", "low"),
        report.get("causality", {}).get("causalityRisk", "low"),
        precepts.get("preceptRisk", "low"),
        report.get("deliberation", {}).get("deliberationRisk", "low"),
        report.get("gradualRelease", {}).get("releaseRisk", "low"),
    ]
    if "high" in risks:
        overall_risk = "high"
    elif "medium" in risks:
        overall_risk = "medium"
    else:
        overall_risk = "low"

    return JudgmentSummaryResponse(
        request_id=request_id,
        decision=report.get("decision", "defer"),
        risk_level=overall_risk,  # type: ignore
        hard_block=precepts.get("hardBlock", False),
        human_review_required=precepts.get("humanReviewRequired", False),
        reasoning=report.get("reasoningSummary", ""),
        precept_violations=violations,
    )


def create_request(payload: CreateRequestPayload) -> RequestReportResponse:
    request_id = f"vinaya-{uuid4().hex[:12]}"
    request = {
        "requestId": request_id,
        "requestModelId": payload.request_model_id or "manual",
        "title": payload.title,
        "requestText": payload.request_text,
        "domain": payload.domain,
        "riskLevel": payload.risk_level,
        "context": payload.context or "",
    }

    use_mock_engine = os.getenv("VINAYA_USE_MOCK_ENGINE", "false").lower() == "true"

    if use_mock_engine:
        report = run_vinaya_pipeline(request)
    else:
        # 根据请求模型获取对应的 LLM 供应商 ID
        llm_provider_id = _get_llm_provider_id(payload.request_model_id)

        # 创建绑定了供应商 ID 的 LLM 调用函数
        chat_fn_with_provider = partial(chat_json, llm_provider_id=llm_provider_id)

        # 通过依赖注入传入具体的 LLM 调用函数和规则配置加载函数
        report = run_vinaya_llm_pipeline(
            request,
            chat_fn=chat_fn_with_provider,
            rules_provider=get_rules_config,
        )

    # 戒律硬约束 + 风险阈值硬约束：独立于 LLM 的系统级校验
    report = enforce_precepts(report, rules_provider=get_rules_config)

    # 生成机器友好的摘要
    summary = _build_summary(report, request_id)

    response = RequestReportResponse(request_id=request_id, report=report, summary=summary)
    return save_report(response)


def fetch_request(request_id: str) -> RequestReportResponse | None:
    return get_report(request_id)
