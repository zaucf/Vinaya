"""SQLite-based repository implementation for Vinaya.

This module provides persistent storage using SQLite database.
It maintains backward compatibility with the JSON file format.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from apps.api.vinaya_api.schemas import (
    LLMProviderItem,
    RequestModelItem,
    RequestReportResponse,
    ReviewResponse,
)

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DB_FILE = DATA_DIR / "vinaya.db"


def _ensure_database() -> None:
    """Initialize database and create tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Request reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_reports (
            request_id TEXT PRIMARY KEY,
            report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Reviews table (supports multiple reviews per request)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            result TEXT NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES request_reports(request_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_request_id
        ON reviews(request_id)
    """)

    # Request models table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_models (
            model_id TEXT PRIMARY KEY,
            model_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # LLM providers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_providers (
            provider_id TEXT PRIMARY KEY,
            provider_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def _get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    _ensure_database()
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# Request Reports


def save_report(report: RequestReportResponse) -> RequestReportResponse:
    """Save a request report to the database."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO request_reports (request_id, report_json)
        VALUES (?, ?)
        """,
        (report.request_id, json.dumps(report.model_dump(), ensure_ascii=False)),
    )

    conn.commit()
    conn.close()
    return report


def get_report(request_id: str) -> RequestReportResponse | None:
    """Get a request report by ID."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT report_json FROM request_reports WHERE request_id = ?",
        (request_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return RequestReportResponse.model_validate(json.loads(row["report_json"]))


def list_reports() -> list[RequestReportResponse]:
    """List all request reports."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT report_json FROM request_reports ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [RequestReportResponse.model_validate(json.loads(row["report_json"])) for row in rows]


# Reviews


def save_review(review: ReviewResponse) -> ReviewResponse:
    """Save a review to the database."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reviews (review_id, request_id, reviewer, result, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            review.review_id,
            review.request_id,
            review.reviewer,
            review.result,
            review.comment,
            review.created_at,
        ),
    )

    conn.commit()
    conn.close()
    return review


def get_review(request_id: str) -> ReviewResponse | None:
    """Get the latest review for a request."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT review_id, request_id, reviewer, result, comment, created_at
        FROM reviews
        WHERE request_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (request_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return ReviewResponse(
        review_id=row["review_id"],
        request_id=row["request_id"],
        reviewer=row["reviewer"],
        result=row["result"],
        comment=row["comment"],
        created_at=row["created_at"],
    )


def list_reviews(request_id: str) -> list[ReviewResponse]:
    """List all reviews for a request."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT review_id, request_id, reviewer, result, comment, created_at
        FROM reviews
        WHERE request_id = ?
        ORDER BY created_at ASC
        """,
        (request_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        ReviewResponse(
            review_id=row["review_id"],
            request_id=row["request_id"],
            reviewer=row["reviewer"],
            result=row["result"],
            comment=row["comment"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


# Request Models


def list_request_models() -> list[RequestModelItem]:
    """List all request models."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT model_json FROM request_models ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [RequestModelItem.model_validate(json.loads(row["model_json"])) for row in rows]


def save_request_model(model: RequestModelItem) -> RequestModelItem:
    """Save a request model."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO request_models (model_id, model_json)
        VALUES (?, ?)
        """,
        (model.model_id, json.dumps(model.model_dump(), ensure_ascii=False)),
    )

    conn.commit()
    conn.close()
    return model


def get_request_model(model_id: str) -> RequestModelItem | None:
    """Get a request model by ID."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT model_json FROM request_models WHERE model_id = ?",
        (model_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return RequestModelItem.model_validate(json.loads(row["model_json"]))


def delete_request_model(model_id: str) -> bool:
    """Delete a request model."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM request_models WHERE model_id = ?", (model_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted


# LLM Providers


def list_llm_providers() -> list[LLMProviderItem]:
    """List all LLM providers."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT provider_json FROM llm_providers ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [LLMProviderItem.model_validate(json.loads(row["provider_json"])) for row in rows]


def save_llm_provider(provider: LLMProviderItem) -> LLMProviderItem:
    """Save an LLM provider."""
    conn = _get_connection()
    cursor = conn.cursor()

    # If this provider is set as default, unset all others
    if provider.is_default:
        cursor.execute("SELECT provider_json FROM llm_providers")
        rows = cursor.fetchall()
        for row in rows:
            existing = json.loads(row["provider_json"])
            if existing["provider_id"] != provider.provider_id:
                existing["is_default"] = False
                cursor.execute(
                    "UPDATE llm_providers SET provider_json = ? WHERE provider_id = ?",
                    (json.dumps(existing, ensure_ascii=False), existing["provider_id"]),
                )

    cursor.execute(
        """
        INSERT OR REPLACE INTO llm_providers (provider_id, provider_json)
        VALUES (?, ?)
        """,
        (provider.provider_id, json.dumps(provider.model_dump(), ensure_ascii=False)),
    )

    conn.commit()
    conn.close()
    return provider


def get_llm_provider(provider_id: str) -> LLMProviderItem | None:
    """Get an LLM provider by ID."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT provider_json FROM llm_providers WHERE provider_id = ?",
        (provider_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return LLMProviderItem.model_validate(json.loads(row["provider_json"]))


def get_default_llm_provider() -> LLMProviderItem | None:
    """Get the default LLM provider."""
    for provider in list_llm_providers():
        if provider.is_default and provider.enabled:
            return provider
    return None


def delete_llm_provider(provider_id: str) -> bool:
    """Delete an LLM provider."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM llm_providers WHERE provider_id = ?", (provider_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()
    return deleted
