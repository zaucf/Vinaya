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


class RequestModelsResponse(BaseModel):
    items: list[RequestModelItem]

class LLMProviderItem(BaseModel):
    provider_id: str
    name: str
    provider_type: Literal["openai-compatible"]
    base_url: str
    model: str
    api_key_env: str
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
    api_key_env: str = Field(min_length=1, max_length=120)
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
    api_key_env: str = Field(min_length=1, max_length=120)
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


class UpdateRequestModelPayload(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=240)
    domain: str = Field(min_length=1, max_length=80)
    default_risk_level: Literal["low", "medium", "high"]
    default_title: str = Field(min_length=1, max_length=120)
    placeholder_request_text: str = Field(min_length=1, max_length=4000)
    placeholder_context: str = Field(default="", max_length=4000)
    human_review_required: bool


class CreateRequestPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    request_text: str = Field(min_length=1, max_length=4000)
    domain: str = Field(min_length=1, max_length=80)
    risk_level: Literal["low", "medium", "high"]
    context: str = Field(default="", max_length=4000)
    request_model_id: str | None = Field(default=None, max_length=80)



class RequestReportResponse(BaseModel):
    request_id: str
    report: dict[str, Any]


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


class LLMProviderTestResponse(BaseModel):
    ok: bool
    provider_id: str
    message: str
