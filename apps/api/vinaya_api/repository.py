"""Repository layer for Vinaya data persistence.

This module acts as a router that delegates to either JSON file storage
or SQLite database storage based on the VINAYA_USE_SQLITE environment variable.

Set VINAYA_USE_SQLITE=true to use SQLite, otherwise defaults to JSON files.
"""

from __future__ import annotations

import os

from apps.api.vinaya_api.schemas import (
    LLMProviderItem,
    RequestModelItem,
    RequestReportResponse,
    ReviewResponse,
)

# Determine which backend to use
USE_SQLITE = os.getenv("VINAYA_USE_SQLITE", "false").lower() == "true"

if USE_SQLITE:
    from apps.api.vinaya_api import repository_sqlite as backend
else:
    from apps.api.vinaya_api import repository_json as backend


# Re-export all functions from the selected backend
save_report = backend.save_report
get_report = backend.get_report
list_reports = backend.list_reports

save_review = backend.save_review
get_review = backend.get_review
list_reviews = backend.list_reviews

list_request_models = backend.list_request_models
save_request_model = backend.save_request_model
get_request_model = backend.get_request_model
delete_request_model = backend.delete_request_model

list_llm_providers = backend.list_llm_providers
save_llm_provider = backend.save_llm_provider
get_llm_provider = backend.get_llm_provider
get_default_llm_provider = backend.get_default_llm_provider
delete_llm_provider = backend.delete_llm_provider
