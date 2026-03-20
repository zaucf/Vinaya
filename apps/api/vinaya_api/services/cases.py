"""Cases service — 聚合推翻案例，组合 confessions + reports 数据。"""

from __future__ import annotations

from apps.api.vinaya_api.repository import get_report
from apps.api.vinaya_api.schemas import CaseItem, CaseListResponse
from apps.api.vinaya_api.services.confessions import get_confessions


def get_cases(
    *,
    domain: str | None = None,
    risk_level: str | None = None,
) -> CaseListResponse:
    """获取推翻案例列表，可按领域和风险等级筛选。"""
    confessions = get_confessions().items
    cases: list[CaseItem] = []

    for c in confessions:
        if domain and c.domain != domain:
            continue
        if risk_level and c.risk_level != risk_level:
            continue

        title = ""
        reasoning_summary = ""
        report = get_report(c.request_id)
        if report and report.report:
            req = report.report.get("request", {})
            title = req.get("title", "")
            reasoning_summary = report.report.get("reasoningSummary", "")

        cases.append(
            CaseItem(
                confession_id=c.confession_id,
                request_id=c.request_id,
                domain=c.domain,
                risk_level=c.risk_level,
                original_decision=c.original_decision,
                override_comment=c.override_comment,
                reviewer=c.reviewer,
                action_taken=c.action_taken,
                created_at=c.created_at,
                title=title,
                reasoning_summary=reasoning_summary,
            )
        )

    return CaseListResponse(items=cases)
