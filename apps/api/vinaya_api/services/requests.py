from __future__ import annotations

import os
from uuid import uuid4

from apps.api.vinaya_api.repository import get_report, save_report
from apps.api.vinaya_api.schemas import CreateRequestPayload, RequestReportResponse
from packages.engine.vinaya_engine import run_vinaya_llm_pipeline, run_vinaya_pipeline


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
    report = run_vinaya_pipeline(request) if use_mock_engine else run_vinaya_llm_pipeline(request)
    response = RequestReportResponse(request_id=request_id, report=report)
    return save_report(response)


def fetch_request(request_id: str) -> RequestReportResponse | None:
    return get_report(request_id)
