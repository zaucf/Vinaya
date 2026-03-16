from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from apps.api.vinaya_api.repository import get_report, get_review, list_reviews, save_review
from apps.api.vinaya_api.schemas import ReviewListResponse, ReviewPayload, ReviewResponse
from apps.api.vinaya_api.services.confessions import create_confession


def submit_review(request_id: str, payload: ReviewPayload) -> ReviewResponse:
    review = ReviewResponse(
        review_id=f"review-{uuid4().hex[:12]}",
        request_id=request_id,
        reviewer=payload.reviewer,
        result=payload.result,
        comment=payload.comment,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    saved = save_review(review)

    # 慧：推翻时自动触发补赎
    if payload.result == "override":
        report = get_report(request_id)
        if report is not None:
            report_data = report.report
            create_confession(
                request_id=request_id,
                domain=report_data.get("request", {}).get("domain", "unknown"),
                risk_level=report_data.get("request", {}).get("riskLevel", "medium"),
                original_decision=report_data.get("decision", "unknown"),
                override_comment=payload.comment,
                reviewer=payload.reviewer,
            )

    return saved


def fetch_review(request_id: str) -> ReviewResponse | None:
    return get_review(request_id)


def fetch_review_list(request_id: str) -> ReviewListResponse:
    return ReviewListResponse(items=list_reviews(request_id))
