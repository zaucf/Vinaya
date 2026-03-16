"""Migrate data from JSON files to SQLite database.

This script reads existing JSON files and imports the data into the new
SQLite database. It can be run multiple times safely (idempotent).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from apps.api.vinaya_api.schemas import (
    LLMProviderItem,
    RequestModelItem,
    RequestReportResponse,
    ReviewResponse,
)
from apps.api.vinaya_api import repository_sqlite as repo

DATA_DIR = project_root / "data"
REPORTS_FILE = DATA_DIR / "request-reports.json"
REVIEWS_FILE = DATA_DIR / "request-reviews.json"
REQUEST_MODELS_FILE = DATA_DIR / "request-models.json"
LLM_PROVIDERS_FILE = DATA_DIR / "llm-providers.json"


def _load_json(file_path: Path) -> dict:
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


def migrate():
    print("Starting migration from JSON to SQLite...")

    # Migrate reports
    reports_data = _load_json(REPORTS_FILE)
    report_count = 0
    for raw in reports_data.values():
        report = RequestReportResponse.model_validate(raw)
        repo.save_report(report)
        report_count += 1
    print(f"  Migrated {report_count} reports")

    # Migrate reviews (handle both old format and new list format)
    reviews_data = _load_json(REVIEWS_FILE)
    review_count = 0
    for value in reviews_data.values():
        review_list = value if isinstance(value, list) else [value]
        for raw in review_list:
            review = ReviewResponse.model_validate(raw)
            # Check if review already exists
            existing = repo.list_reviews(review.request_id)
            if not any(r.review_id == review.review_id for r in existing):
                repo.save_review(review)
                review_count += 1
    print(f"  Migrated {review_count} reviews")

    # Migrate request models
    models_data = _load_json(REQUEST_MODELS_FILE)
    model_count = 0
    for raw in models_data.values():
        model = RequestModelItem.model_validate(raw)
        repo.save_request_model(model)
        model_count += 1
    print(f"  Migrated {model_count} request models")

    # Migrate LLM providers
    providers_data = _load_json(LLM_PROVIDERS_FILE)
    provider_count = 0
    for raw in providers_data.values():
        provider = LLMProviderItem.model_validate(raw)
        repo.save_llm_provider(provider)
        provider_count += 1
    print(f"  Migrated {provider_count} LLM providers")

    print(f"Migration complete! Database: {repo.DB_FILE}")


if __name__ == "__main__":
    migrate()
