from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from apps.api.vinaya_api.services.llm_providers import get_active_llm_provider


class LLMConfigurationError(RuntimeError):
    pass


class LLMRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model: str
    base_url: str
    temperature: float = 0.2
    timeout_seconds: int = 60


def load_llm_settings() -> LLMSettings:
    provider = get_active_llm_provider()
    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        raise LLMConfigurationError(
            f"Missing environment variable for active LLM provider: {provider.api_key_env}"
        )

    return LLMSettings(
        api_key=api_key,
        model=provider.model,
        base_url=provider.base_url,
        temperature=provider.temperature,
        timeout_seconds=provider.timeout_seconds,
    )


def chat_json(*, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    settings = load_llm_settings()
    payload = {
        "model": settings.model,
        "temperature": settings.temperature,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        settings.base_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=settings.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMRequestError(f"LLM HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise LLMRequestError(f"LLM connection failed: {exc}") from exc

    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMRequestError(f"Unexpected LLM response: {raw}") from exc

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMRequestError(f"LLM did not return valid JSON: {content}") from exc
