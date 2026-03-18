from __future__ import annotations

import json
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
    """测试 LLM 提供商连接。

    策略：
    1. 先尝试 GET /models（不消耗 token）
    2. 如果返回 404/405，回退到 POST /chat/completions
    """
    provider = get_llm_provider(provider_id)
    if provider is None:
        raise LookupError(f"LLM provider '{provider_id}' not found")

    api_key = provider.api_key
    if not api_key:
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message="缺少 API Key",
        )

    # 构建基础 URL
    base_url = provider.base_url.rstrip("/")

    # 如果用户配置的是完整 URL（包含 /chat/completions），则去掉
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]

    # 方法 1：尝试 GET /models（不消耗 token）
    models_url = f"{base_url}/models"

    try:
        models_request = request.Request(
            models_url,
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )
        with request.urlopen(models_request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "object" in data and data["object"] == "list":
                model_list = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
                model_count = len(model_list)
                return LLMProviderTestResponse(
                    ok=True,
                    provider_id=provider_id,
                    message=f"连接成功，可用模型 {model_count} 个",
                    models=model_list,
                )
            return LLMProviderTestResponse(
                ok=True,
                provider_id=provider_id,
                message="连接成功",
            )
    except error.HTTPError as exc:
        if exc.code not in (404, 405):
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                error_data = json.loads(detail)
                error_msg = error_data.get("error", {}).get("message", detail[:150])
            except:
                error_msg = detail[:150]
            return LLMProviderTestResponse(
                ok=False,
                provider_id=provider_id,
                message=f"HTTP {exc.code}: {error_msg}",
            )
        # 404/405: /models 不支持，继续尝试 chat 请求
    except error.URLError as exc:
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"连接失败: {exc.reason}",
        )

    # 方法 2：回退到 POST /chat/completions
    chat_url = f"{base_url}/chat/completions"

    try:
        payload = {
            "model": provider.model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }
        chat_request = request.Request(
            chat_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with request.urlopen(chat_request, timeout=provider.timeout_seconds) as response:
            return LLMProviderTestResponse(
                ok=True,
                provider_id=provider_id,
                message="连接成功",
            )
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(detail)
            error_msg = error_data.get("error", {}).get("message", detail[:200])
        except:
            error_msg = detail[:200]
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"HTTP {exc.code}: {error_msg}",
        )
    except error.URLError as exc:
        return LLMProviderTestResponse(
            ok=False,
            provider_id=provider_id,
            message=f"连接失败: {exc.reason}",
        )
