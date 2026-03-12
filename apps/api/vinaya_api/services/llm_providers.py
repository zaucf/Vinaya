from __future__ import annotations

import os
from urllib import error, request

from apps.api.vinaya_api.repository import (
    delete_llm_provider,
    get_default_llm_provider,
    get_llm_provider,
    list_llm_providers,
    save_llm_provider,
)
from apps.api.vinaya_api.schemas import (
    CreateLLMProviderPayload,
    LLMProviderItem,
    LLMProvidersResponse,
    LLMProviderTestResponse,
    UpdateLLMProviderPayload,
)


def get_llm_provider_items() -> LLMProvidersResponse:
    return LLMProvidersResponse(items=list_llm_providers())


def create_llm_provider(payload: CreateLLMProviderPayload) -> LLMProviderItem:
    existing = get_llm_provider(payload.provider_id)
    if existing is not None:
        raise ValueError(f"LLM provider '{payload.provider_id}' already exists")

    provider = LLMProviderItem(**payload.model_dump())
    return save_llm_provider(provider)


def update_llm_provider(provider_id: str, payload: UpdateLLMProviderPayload) -> LLMProviderItem:
    existing = get_llm_provider(provider_id)
    if existing is None:
        raise LookupError(f"LLM provider '{provider_id}' not found")

    provider = LLMProviderItem(provider_id=provider_id, **payload.model_dump())
    return save_llm_provider(provider)


def remove_llm_provider(provider_id: str) -> None:
    provider = get_llm_provider(provider_id)
    if provider is None:
        raise LookupError(f"LLM provider '{provider_id}' not found")
    if provider.is_default:
        raise ValueError("Default LLM provider cannot be deleted")

    deleted = delete_llm_provider(provider_id)
    if not deleted:
        raise LookupError(f"LLM provider '{provider_id}' not found")


def get_active_llm_provider() -> LLMProviderItem:
    provider = get_default_llm_provider()
    if provider is None:
        raise LookupError("No enabled default LLM provider configured")
    return provider


def test_llm_provider_connection(provider_id: str) -> LLMProviderTestResponse:
    provider = get_llm_provider(provider_id)
    if provider is None:
        raise LookupError(f"LLM provider '{provider_id}' not found")

    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"Missing environment variable: {provider.api_key_env}",
        )

    http_request = request.Request(
        provider.base_url,
        data=b'{"model":"' + provider.model.encode("utf-8") + b'","messages":[{"role":"user","content":"ping"}],"max_tokens":1}',
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=provider.timeout_seconds):
            return LLMProviderTestResponse(
                ok=True,
                provider_id=provider_id,
                message="Connection test succeeded",
            )
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"HTTP {exc.code}: {detail}",
        )
    except error.URLError as exc:
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"Connection failed: {exc}",
        )
