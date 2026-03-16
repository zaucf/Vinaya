"""JSON file-based repository implementation for Vinaya.

This is the original storage backend using JSON files in the data/ directory.
"""

from __future__ import annotations

import json
from pathlib import Path

from apps.api.vinaya_api.schemas import (
    LLMProviderItem,
    RequestModelItem,
    RequestReportResponse,
    ReviewResponse,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
REPORTS_FILE = DATA_DIR / "request-reports.json"
REVIEWS_FILE = DATA_DIR / "request-reviews.json"
REQUEST_MODELS_FILE = DATA_DIR / "request-models.json"
LLM_PROVIDERS_FILE = DATA_DIR / "llm-providers.json"


def _ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not REPORTS_FILE.exists():
        REPORTS_FILE.write_text("{}", encoding="utf-8")
    if not REVIEWS_FILE.exists():
        REVIEWS_FILE.write_text("{}", encoding="utf-8")
    if not REQUEST_MODELS_FILE.exists():
        REQUEST_MODELS_FILE.write_text("{}", encoding="utf-8")
    if not LLM_PROVIDERS_FILE.exists():
        LLM_PROVIDERS_FILE.write_text("{}", encoding="utf-8")


def _load_json(file_path: Path) -> dict[str, dict]:
    _ensure_storage()
    return json.loads(file_path.read_text(encoding="utf-8"))


def _save_json(file_path: Path, payload: dict[str, dict]) -> None:
    _ensure_storage()
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# Request Reports


def save_report(report: RequestReportResponse) -> RequestReportResponse:
    reports = _load_json(REPORTS_FILE)
    reports[report.request_id] = report.model_dump()
    _save_json(REPORTS_FILE, reports)
    return report


def get_report(request_id: str) -> RequestReportResponse | None:
    reports = _load_json(REPORTS_FILE)
    raw = reports.get(request_id)
    if raw is None:
        return None
    return RequestReportResponse.model_validate(raw)


def list_reports() -> list[RequestReportResponse]:
    reports = _load_json(REPORTS_FILE)
    return [RequestReportResponse.model_validate(raw) for raw in reports.values()]


# Reviews


def _load_reviews() -> dict[str, list[dict]]:
    """Load review data, auto-migrating old single-dict format to list format."""
    _ensure_storage()
    raw = json.loads(REVIEWS_FILE.read_text(encoding="utf-8"))
    migrated = False
    for key, value in raw.items():
        if isinstance(value, dict):
            raw[key] = [value]
            migrated = True
    if migrated:
        _save_json(REVIEWS_FILE, raw)
    return raw


def save_review(review: ReviewResponse) -> ReviewResponse:
    reviews = _load_reviews()
    if review.request_id not in reviews:
        reviews[review.request_id] = []
    reviews[review.request_id].append(review.model_dump())
    _save_json(REVIEWS_FILE, reviews)
    return review


def get_review(request_id: str) -> ReviewResponse | None:
    reviews = _load_reviews()
    raw_list = reviews.get(request_id)
    if raw_list is None or len(raw_list) == 0:
        return None
    return ReviewResponse.model_validate(raw_list[-1])


def list_reviews(request_id: str) -> list[ReviewResponse]:
    reviews = _load_reviews()
    raw_list = reviews.get(request_id)
    if raw_list is None:
        return []
    return [ReviewResponse.model_validate(raw) for raw in raw_list]


# Request Models


def list_request_models() -> list[RequestModelItem]:
    raw_models = _load_json(REQUEST_MODELS_FILE)
    return [RequestModelItem.model_validate(raw) for raw in raw_models.values()]


def save_request_model(model: RequestModelItem) -> RequestModelItem:
    models = _load_json(REQUEST_MODELS_FILE)
    models[model.model_id] = model.model_dump()
    _save_json(REQUEST_MODELS_FILE, models)
    return model


def get_request_model(model_id: str) -> RequestModelItem | None:
    models = _load_json(REQUEST_MODELS_FILE)
    raw = models.get(model_id)
    if raw is None:
        return None
    return RequestModelItem.model_validate(raw)


def delete_request_model(model_id: str) -> bool:
    models = _load_json(REQUEST_MODELS_FILE)
    if model_id not in models:
        return False
    del models[model_id]
    _save_json(REQUEST_MODELS_FILE, models)
    return True


# LLM Providers


def list_llm_providers() -> list[LLMProviderItem]:
    raw_providers = _load_json(LLM_PROVIDERS_FILE)
    return [LLMProviderItem.model_validate(raw) for raw in raw_providers.values()]


def save_llm_provider(provider: LLMProviderItem) -> LLMProviderItem:
    providers = _load_json(LLM_PROVIDERS_FILE)
    if provider.is_default:
        for item in providers.values():
            item["is_default"] = False
    providers[provider.provider_id] = provider.model_dump()
    _save_json(LLM_PROVIDERS_FILE, providers)
    return provider


def get_llm_provider(provider_id: str) -> LLMProviderItem | None:
    providers = _load_json(LLM_PROVIDERS_FILE)
    raw = providers.get(provider_id)
    if raw is None:
        return None
    return LLMProviderItem.model_validate(raw)


def get_default_llm_provider() -> LLMProviderItem | None:
    for provider in list_llm_providers():
        if provider.is_default and provider.enabled:
            return provider
    return None


def delete_llm_provider(provider_id: str) -> bool:
    providers = _load_json(LLM_PROVIDERS_FILE)
    if provider_id not in providers:
        return False
    del providers[provider_id]
    _save_json(LLM_PROVIDERS_FILE, providers)
    return True
