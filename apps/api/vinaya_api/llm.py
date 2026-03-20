from __future__ import annotations

import json
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


def load_llm_settings(llm_provider_id: str | None = None) -> LLMSettings:
    """加载 LLM 设置。

    Args:
        llm_provider_id: 指定使用的 LLM 供应商 ID，如果为 None 则使用默认供应商

    Raises:
        LLMConfigurationError: 供应商不存在或 API key 为空
    """
    from apps.api.vinaya_api.services.llm_providers import get_active_llm_provider

    if llm_provider_id:
        from apps.api.vinaya_api.repository import get_llm_provider

        provider = get_llm_provider(llm_provider_id)
        if provider is None:
            raise LLMConfigurationError(
                f"Specified LLM provider '{llm_provider_id}' not found"
            )
        if not provider.enabled:
            raise LLMConfigurationError(
                f"Specified LLM provider '{llm_provider_id}' is not enabled"
            )
    else:
        provider = get_active_llm_provider()

    api_key = provider.api_key
    if not api_key:
        raise LLMConfigurationError(
            f"Missing API key for LLM provider: {provider.provider_id}"
        )

    return LLMSettings(
        api_key=api_key,
        model=provider.model,
        base_url=provider.base_url,
        temperature=provider.temperature,
        timeout_seconds=provider.timeout_seconds,
    )


def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    llm_provider_id: str | None = None,
) -> dict[str, Any]:
    """调用 LLM 并返回 JSON 格式响应。

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        llm_provider_id: 指定使用的 LLM 供应商 ID，如果为 None 则使用默认供应商
    """
    settings = load_llm_settings(llm_provider_id)

    # 构建完整的端点 URL：base_url 可能是基础 URL 或完整 URL
    base_url = settings.base_url.rstrip("/")
    if not base_url.endswith("/chat/completions"):
        endpoint_url = f"{base_url}/chat/completions"
    else:
        endpoint_url = base_url

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
        endpoint_url,
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


# ── 风险自动分类 ──

CLASSIFY_PROMPT = (
    "你是一个风险评估助手。根据以下请求内容，判断风险等级。\n"
    "只输出 JSON：{\"risk_level\": \"low\"|\"medium\"|\"high\"}\n\n"
    "考虑因素：\n"
    "- 是否涉及不可逆操作（删除、永久修改、资金转移等）\n"
    "- 影响面大小（单人/团队/全公司/公众）\n"
    "- 是否需要人工确认才能安全执行\n"
    "- 是否涉及敏感领域（法律、财务、人事、安全）\n\n"
    "低风险：影响面小、可回退、不涉及敏感操作\n"
    "中风险：有一定影响面、需要关注但可控\n"
    "高风险：不可逆、影响面大、涉及敏感领域"
)


def classify_risk(
    title: str,
    request_text: str,
    domain: str,
    *,
    llm_provider_id: str | None = None,
) -> str:
    """使用 LLM 自动分类风险等级。

    Returns:
        "low" | "medium" | "high"
    """
    user_prompt = (
        f"请求标题：{title}\n"
        f"领域：{domain}\n"
        f"请求内容：{request_text}"
    )
    try:
        result = chat_json(
            system_prompt=CLASSIFY_PROMPT,
            user_prompt=user_prompt,
            llm_provider_id=llm_provider_id,
        )
        level = result.get("risk_level", "medium")
        if level in ("low", "medium", "high"):
            return level
        return "medium"
    except (LLMConfigurationError, LLMRequestError):
        return "medium"
