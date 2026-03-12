from __future__ import annotations

from apps.api.vinaya_api.schemas import ReviewResponse


def map_review_result_label(review: ReviewResponse | None) -> str:
    if review is None:
        return "未复核"

    return {
        "maintain": "已维持",
        "revise": "已修改",
        "override": "已推翻",
    }.get(review.result, "已复核")
