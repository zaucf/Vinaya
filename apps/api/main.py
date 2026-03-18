from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from apps.api.vinaya_api.llm import LLMConfigurationError, LLMRequestError
from apps.api.vinaya_api.schemas import (
    ConfessionListResponse,
    CreateLLMProviderPayload,
    CreateRequestModelPayload,
    CreateRequestPayload,
    HealthResponse,
    LLMProviderItem,
    LLMProvidersResponse,
    LLMProviderTestResponse,
    RequestListResponse,
    RequestModelItem,
    RequestModelsResponse,
    RequestReportResponse,
    ReviewListResponse,
    ReviewPayload,
    ReviewResponse,
    RulesConfigResponse,
    UpdateLLMProviderPayload,
    UpdateRequestModelPayload,
)

from apps.api.vinaya_api.services.demo import get_demo_report
from apps.api.vinaya_api.services.history import get_request_history
from apps.api.vinaya_api.services.llm_providers import (
    create_llm_provider,
    get_llm_provider_items,
    remove_llm_provider,
    test_llm_provider_connection,
    update_llm_provider,
)

from apps.api.vinaya_api.services.request_models import (
    create_request_model,
    get_request_models,
    remove_request_model,
    update_request_model,
)
from apps.api.vinaya_api.services.requests import create_request, fetch_request
from apps.api.vinaya_api.services.requests_stream import stream_judgment_process
from apps.api.vinaya_api.services.reviews import fetch_review, fetch_review_list, submit_review
from apps.api.vinaya_api.services.rules import get_rules_config, save_rules_config
from apps.api.vinaya_api.services.confessions import get_confessions

app = FastAPI(title="Vinaya API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True, service="vinaya-api")


@app.get("/api/demo")
def demo_report() -> dict:
    return get_demo_report()


@app.get("/api/request-models", response_model=RequestModelsResponse)
def list_request_models() -> RequestModelsResponse:
    return get_request_models()


@app.post("/api/request-models", response_model=RequestModelItem, status_code=201)
def create_request_model_item(payload: CreateRequestModelPayload) -> RequestModelItem:
    try:
        return create_request_model(payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.put("/api/request-models/{model_id}", response_model=RequestModelItem)
def update_request_model_item(
    model_id: str,
    payload: UpdateRequestModelPayload,
) -> RequestModelItem:
    try:
        return update_request_model(model_id, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/request-models/{model_id}", status_code=204)
def delete_request_model_item(model_id: str) -> None:
    try:
        remove_request_model(model_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/llm-providers", response_model=LLMProvidersResponse)
def list_llm_provider_items() -> LLMProvidersResponse:
    return get_llm_provider_items()


@app.post("/api/llm-providers", response_model=LLMProviderItem, status_code=201)
def create_llm_provider_item(payload: CreateLLMProviderPayload) -> LLMProviderItem:
    try:
        return create_llm_provider(payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.put("/api/llm-providers/{provider_id}", response_model=LLMProviderItem)
def update_llm_provider_item(
    provider_id: str,
    payload: UpdateLLMProviderPayload,
) -> LLMProviderItem:
    try:
        return update_llm_provider(provider_id, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/llm-providers/{provider_id}", status_code=204)
def delete_llm_provider_item(provider_id: str) -> None:
    try:
        remove_llm_provider(provider_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/llm-providers/{provider_id}/test", response_model=LLMProviderTestResponse)
def test_llm_provider_item(provider_id: str) -> LLMProviderTestResponse:
    try:
        return test_llm_provider_connection(provider_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/requests", response_model=RequestListResponse)
def list_request_reports() -> RequestListResponse:
    return get_request_history()

@app.post("/api/requests", response_model=RequestReportResponse)
def create_request_report(payload: CreateRequestPayload) -> RequestReportResponse:
    try:
        return create_request(payload)
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMRequestError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/requests/stream")
async def create_request_stream(payload: CreateRequestPayload) -> StreamingResponse:
    return StreamingResponse(
        stream_judgment_process(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )



@app.get("/api/requests/{request_id}", response_model=RequestReportResponse)
def get_request_report(request_id: str) -> RequestReportResponse:
    report = fetch_request(request_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Request report not found")
    return report


@app.get("/api/requests/{request_id}/review", response_model=ReviewResponse)
def get_request_review(request_id: str) -> ReviewResponse:
    review = fetch_review(request_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.get("/api/requests/{request_id}/reviews", response_model=ReviewListResponse)
def get_request_review_list(request_id: str) -> ReviewListResponse:
    return fetch_review_list(request_id)


@app.post("/api/requests/{request_id}/review", response_model=ReviewResponse)
def create_request_review(request_id: str, payload: ReviewPayload) -> ReviewResponse:
    report = fetch_request(request_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Request report not found")
    return submit_review(request_id, payload)


@app.get("/api/rules", response_model=RulesConfigResponse)
def get_rules() -> RulesConfigResponse:
    return get_rules_config()


@app.put("/api/rules", response_model=RulesConfigResponse)
def update_rules(payload: RulesConfigResponse) -> RulesConfigResponse:
    return save_rules_config(payload)


@app.get("/api/confessions", response_model=ConfessionListResponse)
def list_confessions() -> ConfessionListResponse:
    return get_confessions()
