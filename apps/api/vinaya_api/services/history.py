from __future__ import annotations

from apps.api.vinaya_api.repository import get_review, list_reports
from apps.api.vinaya_api.schemas import RequestListItem, RequestListResponse
from apps.api.vinaya_api.services.status import map_review_result_label


def get_request_history() -> RequestListResponse:
    reports = list_reports()
    items = []

    for report in reports:
        review = get_review(report.request_id)
        items.append(
            RequestListItem(
                request_id=report.request_id,
                title=report.report["request"]["title"],
                domain=report.report["request"]["domain"],
                risk_level=report.report["request"]["riskLevel"],
                decision=report.report["decision"],
                review_status=map_review_result_label(review),
            )
        )

    return RequestListResponse(items=items)
