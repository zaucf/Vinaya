from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    ok: bool
    service: str


class RequestModelItem(BaseModel):
    model_id: str
    name: str
    description: str
    domain: str
    default_risk_level: Literal["low", "medium", "high"]
    default_title: str
    placeholder_request_text: str
    placeholder_context: str
    human_review_required: bool
    llm_provider_id: str | None = None  # 指定使用的 LLM 供应商，空则使用默认


class RequestModelsResponse(BaseModel):
    items: list[RequestModelItem]

class LLMProviderItem(BaseModel):
    provider_id: str
    name: str
    provider_type: Literal["openai-compatible"]
    base_url: str
    model: str
    api_key: str
    temperature: float = Field(ge=0, le=2)
    timeout_seconds: int = Field(ge=1, le=600)
    enabled: bool
    is_default: bool
    system_prompt: str


class LLMProvidersResponse(BaseModel):
    items: list[LLMProviderItem]


class CreateLLMProviderPayload(BaseModel):
    provider_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=80)
    provider_type: Literal["openai-compatible"]
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1, max_length=500)
    temperature: float = Field(ge=0, le=2)
    timeout_seconds: int = Field(ge=1, le=600)
    enabled: bool
    is_default: bool
    system_prompt: str = Field(min_length=1, max_length=12000)


class UpdateLLMProviderPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    provider_type: Literal["openai-compatible"]
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1, max_length=500)
    temperature: float = Field(ge=0, le=2)
    timeout_seconds: int = Field(ge=1, le=600)
    enabled: bool
    is_default: bool
    system_prompt: str = Field(min_length=1, max_length=12000)

class CreateRequestModelPayload(BaseModel):
    model_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_\-]+$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    domain: str = Field(min_length=1, max_length=80)
    default_risk_level: Literal["low", "medium", "high"]
    default_title: str = Field(min_length=1, max_length=120)
    placeholder_request_text: str = Field(min_length=1, max_length=4000)
    placeholder_context: str = Field(default="", max_length=4000)
    human_review_required: bool
    llm_provider_id: str | None = Field(default=None, max_length=80)  # 指定使用的 LLM 供应商


class UpdateRequestModelPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    domain: str = Field(min_length=1, max_length=80)
    default_risk_level: Literal["low", "medium", "high"]
    default_title: str = Field(min_length=1, max_length=120)
    placeholder_request_text: str = Field(min_length=1, max_length=4000)
    placeholder_context: str = Field(default="", max_length=4000)
    human_review_required: bool
    llm_provider_id: str | None = Field(default=None, max_length=80)  # 指定使用的 LLM 供应商


class CreateRequestPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    request_text: str = Field(min_length=1, max_length=4000)
    domain: str = Field(min_length=1, max_length=80)
    risk_level: Literal["auto", "low", "medium", "high"]
    context: str = Field(default="", max_length=4000)
    request_model_id: str | None = Field(default=None, max_length=80)


# ────────────────────────────────────────────────────────────────────────────
# 机器友好的判断摘要（新增）
# ────────────────────────────────────────────────────────────────────────────


class PreceptViolationItem(BaseModel):
    """戒律违规项。"""

    name: str
    status: Literal["pass", "warning", "block"]
    reason: str


class JudgmentSummaryResponse(BaseModel):
    """判断摘要（机器友好）。

    这是给 AI 系统读取的结构化数据。
    """

    request_id: str
    decision: Literal["allow", "defer", "stop"]
    risk_level: Literal["low", "medium", "high"]
    hard_block: bool
    human_review_required: bool
    reasoning: str
    precept_violations: list[PreceptViolationItem]


class RequestReportResponse(BaseModel):
    request_id: str
    report: dict[str, Any]
    # 新增：机器友好的摘要
    summary: JudgmentSummaryResponse | None = None


class RequestListItem(BaseModel):
    request_id: str
    title: str
    domain: str
    risk_level: Literal["low", "medium", "high"]
    decision: Literal["allow", "defer", "stop"]
    review_status: str


class RequestListResponse(BaseModel):
    items: list[RequestListItem]


class ReviewPayload(BaseModel):
    reviewer: str = Field(min_length=1, max_length=80)
    result: Literal["maintain", "revise", "override"]
    comment: str = Field(min_length=1, max_length=2000)


class ReviewResponse(BaseModel):
    review_id: str
    request_id: str
    reviewer: str
    result: Literal["maintain", "revise", "override"]
    comment: str
    created_at: str


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]


class PreceptConfig(BaseModel):
    name: str
    enabled: bool
    description: str
    severity: Literal["warning", "block"]


class DeferStrategyConfig(BaseModel):
    strategy_id: str
    name: str
    description: str
    enabled: bool
    default_duration_hours: int = Field(ge=1, le=720)
    require_human_review: bool
    auto_rollback: bool


class RulesConfigResponse(BaseModel):
    precepts: list[PreceptConfig]
    defer_strategies: list[DeferStrategyConfig]
    risk_thresholds: dict[str, Any]


class ConfessionItem(BaseModel):
    confession_id: str
    request_id: str
    domain: str
    risk_level: str
    original_decision: str
    override_comment: str
    reviewer: str
    action_taken: str
    created_at: str


class ConfessionListResponse(BaseModel):
    items: list[ConfessionItem]


class LLMProviderTestResponse(BaseModel):
    ok: bool
    provider_id: str
    message: str
    models: list[str] | None = None  # 可用模型列表


class CaseItem(BaseModel):
    confession_id: str
    request_id: str
    domain: str
    risk_level: str
    original_decision: str
    override_comment: str
    reviewer: str
    action_taken: str
    created_at: str
    title: str = ""
    reasoning_summary: str = ""


class CaseListResponse(BaseModel):
    items: list[CaseItem]
