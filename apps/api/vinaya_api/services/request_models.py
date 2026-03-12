from __future__ import annotations

from apps.api.vinaya_api.repository import (
    delete_request_model,
    get_request_model,
    list_request_models,
    save_request_model,
)
from apps.api.vinaya_api.schemas import (
    CreateRequestModelPayload,
    RequestModelItem,
    RequestModelsResponse,
    UpdateRequestModelPayload,
)


def get_request_models() -> RequestModelsResponse:
    return RequestModelsResponse(items=list_request_models())


def create_request_model(payload: CreateRequestModelPayload) -> RequestModelItem:
    existing = get_request_model(payload.model_id)
    if existing is not None:
        raise ValueError(f"Request model '{payload.model_id}' already exists")

    model = RequestModelItem(**payload.model_dump())
    return save_request_model(model)


def update_request_model(model_id: str, payload: UpdateRequestModelPayload) -> RequestModelItem:
    existing = get_request_model(model_id)
    if existing is None:
        raise LookupError(f"Request model '{model_id}' not found")

    model = RequestModelItem(model_id=model_id, **payload.model_dump())
    return save_request_model(model)


def remove_request_model(model_id: str) -> None:
    deleted = delete_request_model(model_id)
    if not deleted:
        raise LookupError(f"Request model '{model_id}' not found")
