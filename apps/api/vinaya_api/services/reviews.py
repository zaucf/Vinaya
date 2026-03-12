from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from apps.api.vinaya_api.repository import get_review, save_review
from apps.api.vinaya_api.schemas import ReviewPayload, ReviewResponse


def submit_review(request_id: str, payload: ReviewPayload) -> ReviewResponse:
    review = ReviewResponse(
        review_id=f"review-{uuid4().hex[:12]}",
        request_id=request_id,
        reviewer=payload.reviewer,
        result=payload.result,
        comment=payload.comment,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return save_review(review)


def fetch_review(request_id: str) -> ReviewResponse | None:
    return get_review(request_id)
