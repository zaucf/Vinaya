from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from functools import partial
from uuid import uuid4

from apps.api.vinaya_api.llm import chat_json, classify_risk
from apps.api.vinaya_api.repository import get_request_model, save_report
from apps.api.vinaya_api.schemas import (
    CreateRequestPayload,
    JudgmentSummaryResponse,
    PreceptViolationItem,
    RequestReportResponse,
)
from apps.api.vinaya_api.services.rules import get_rules_config
from packages.engine.vinaya_engine.llm_pipeline import run_vinaya_llm_pipeline
from packages.engine.vinaya_engine.pipeline import (
    mock_classify_risk,
    rank_risk,
    resolve_decision,
    run_causality,
    run_dedication,
    run_deliberation,
    run_gradual_release,
    run_intention,
    run_precepts,
)
from packages.engine.vinaya_engine.precept_enforcer import enforce_precepts

# SSE 阶段定义（10 个阶段）
STAGES = [
    {"key": "classify", "label": "风险预判", "message": "正在自动评估风险等级..."},
    {"key": "intention", "label": "发心", "message": "正在分析请求的真实意图和动机..."},
    {"key": "causality", "label": "观缘", "message": "正在追溯因果链和外部影响..."},
    {"key": "precepts", "label": "持戒", "message": "正在逐条校验五戒约束..."},
    {"key": "deliberation", "label": "辩义", "message": "正在权衡备选方案..."},
    {"key": "gradualRelease", "label": "缓行", "message": "正在制定渐进释放策略..."},
    {"key": "dedication", "label": "回向", "message": "正在总结经验教训与功德回向..."},
    {"key": "decision", "label": "决策", "message": "正在综合各阶段结果做出决策..."},
    {"key": "enforce", "label": "戒律校验", "message": "正在执行硬约束校验..."},
    {"key": "summary", "label": "生成摘要", "message": "正在生成判断摘要..."},
]

# Mock 模式下各阶段对应的运行函数
MOCK_STAGE_RUNNERS = {
    "intention": run_intention,
    "causality": run_causality,
    "precepts": run_precepts,
    "deliberation": run_deliberation,
    "gradualRelease": run_gradual_release,
    "dedication": run_dedication,
}


def _sse_event(event: str, data: dict) -> str:
    """构造 SSE 事件字符串。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _get_llm_provider_id(request_model_id: str | None) -> str | None:
    if not request_model_id or request_model_id == "manual":
        return None
    model = get_request_model(request_model_id)
    if model is None:
        return None
    return model.llm_provider_id


def _build_summary(report: dict, request_id: str) -> JudgmentSummaryResponse:
    precepts = report.get("precepts", {})
    findings = precepts.get("preceptFindings", [])
    violations = [
        PreceptViolationItem(
            name=f.get("name", ""),
            status=f.get("status", "pass"),
            reason=f.get("reason", ""),
        )
        for f in findings
        if f.get("status") in ("warning", "block")
    ]
    risks = [
        report.get("intention", {}).get("intentionRisk", "low"),
        report.get("causality", {}).get("causalityRisk", "low"),
        precepts.get("preceptRisk", "low"),
        report.get("deliberation", {}).get("deliberationRisk", "low"),
        report.get("gradualRelease", {}).get("releaseRisk", "low"),
        report.get("dedication", {}).get("dedicationRisk", "low"),
    ]
    if "high" in risks:
        overall_risk = "high"
    elif "medium" in risks:
        overall_risk = "medium"
    else:
        overall_risk = "low"
    return JudgmentSummaryResponse(
        request_id=request_id,
        decision=report.get("decision", "defer"),
        risk_level=overall_risk,  # type: ignore[arg-type]
        hard_block=precepts.get("hardBlock", False),
        human_review_required=precepts.get("humanReviewRequired", False),
        reasoning=report.get("reasoningSummary", ""),
        precept_violations=violations,
    )


async def stream_judgment_process(payload: CreateRequestPayload) -> AsyncGenerator[str, None]:
    """SSE 流式推送判断过程。

    Mock 模式：逐阶段运行，每步推送 stage_start / stage_complete。
    LLM 模式：先推送 llm_call_start，等 LLM 返回后逐阶段推送结果。

    若 risk_level == "auto"，在正式阶段之前插入 classify 阶段做风险预判。
    """
    request_id = f"vinaya-{uuid4().hex[:12]}"
    request = {
        "requestId": request_id,
        "requestModelId": payload.request_model_id or "manual",
        "title": payload.title,
        "requestText": payload.request_text,
        "domain": payload.domain,
        "riskLevel": payload.risk_level,
        "context": payload.context or "",
    }
    total = len(STAGES)
    use_mock = os.getenv("VINAYA_USE_MOCK_ENGINE", "false").lower() == "true"
    need_classify = payload.risk_level == "auto"

    # 计算阶段索引偏移：classify 是 STAGES[0]，六阶段从 STAGES[1] 开始
    SIX_START = 1  # intention 在 STAGES 中的索引

    try:
        # ── 阶段 0：风险预判（仅 auto 模式）──
        if need_classify:
            stage = STAGES[0]
            yield _sse_event("stage_start", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": 0,
                "total": total,
                "message": stage["message"],
            })

            if use_mock:
                classified = await asyncio.to_thread(
                    mock_classify_risk,
                    payload.title,
                    payload.request_text,
                    payload.domain,
                )
            else:
                llm_provider_id = _get_llm_provider_id(payload.request_model_id)
                classified = await asyncio.to_thread(
                    classify_risk,
                    payload.title,
                    payload.request_text,
                    payload.domain,
                    llm_provider_id=llm_provider_id,
                )

            request["riskLevel"] = classified
            await asyncio.sleep(0.2)
            yield _sse_event("stage_complete", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": 0,
                "result": {"risk_level": classified},
            })
        else:
            # 手动选择风险等级时，跳过 classify 阶段，直接标记完成
            stage = STAGES[0]
            yield _sse_event("stage_start", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": 0,
                "total": total,
                "message": "使用手动指定的风险等级",
            })
            yield _sse_event("stage_complete", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": 0,
                "result": {"risk_level": payload.risk_level, "skipped": True},
            })

        if use_mock:
            report = {"request": request}

            # ── 阶段 1-6：逐步运行 Mock 引擎 ──
            for i, stage in enumerate(STAGES[SIX_START:SIX_START + 6]):
                idx = SIX_START + i
                yield _sse_event("stage_start", {
                    "stage": stage["key"],
                    "label": stage["label"],
                    "index": idx,
                    "total": total,
                    "message": stage["message"],
                })
                runner = MOCK_STAGE_RUNNERS[stage["key"]]
                result = await asyncio.to_thread(runner, request)
                report[stage["key"]] = result
                await asyncio.sleep(0.3)
                yield _sse_event("stage_complete", {
                    "stage": stage["key"],
                    "label": stage["label"],
                    "index": idx,
                    "result": result,
                })

            # ── 阶段 7：决策 ──
            stage = STAGES[SIX_START + 6]
            yield _sse_event("stage_start", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": SIX_START + 6,
                "total": total,
                "message": stage["message"],
            })
            decision = resolve_decision(request, report["precepts"], report["gradualRelease"])
            overall_risk = rank_risk([
                report["intention"]["intentionRisk"],
                report["causality"]["causalityRisk"],
                report["precepts"]["preceptRisk"],
                report["deliberation"]["deliberationRisk"],
                report["gradualRelease"]["releaseRisk"],
                report["dedication"]["dedicationRisk"],
            ])
            report["decision"] = decision
            report["reasoningSummary"] = (
                f"综合判断为 {overall_risk} 风险，但当前可在受控范围内推进。"
                if decision == "allow"
                else f"综合判断为 {overall_risk} 风险，建议缓行并保留人工复核。"
                if decision == "defer"
                else "综合判断触发止行条件，不建议继续推进。"
            )
            await asyncio.sleep(0.2)
            yield _sse_event("stage_complete", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": SIX_START + 6,
                "result": {"decision": decision, "reasoningSummary": report["reasoningSummary"]},
            })

        else:
            # ── LLM 模式：先推送六阶段的 start，然后调用 LLM ──
            for i, stage in enumerate(STAGES[SIX_START:SIX_START + 6]):
                idx = SIX_START + i
                yield _sse_event("stage_start", {
                    "stage": stage["key"],
                    "label": stage["label"],
                    "index": idx,
                    "total": total,
                    "message": stage["message"],
                })

            yield _sse_event("llm_call_start", {"message": "正在调用 LLM 进行六阶段分析..."})

            llm_provider_id = _get_llm_provider_id(payload.request_model_id)
            chat_fn_with_provider = partial(chat_json, llm_provider_id=llm_provider_id)
            report = await asyncio.to_thread(
                run_vinaya_llm_pipeline,
                request,
                chat_fn=chat_fn_with_provider,
                rules_provider=get_rules_config,
            )

            # LLM 返回后逐阶段推送结果（150ms 间隔）
            stage_keys_with_results = [
                ("intention", report.get("intention")),
                ("causality", report.get("causality")),
                ("precepts", report.get("precepts")),
                ("deliberation", report.get("deliberation")),
                ("gradualRelease", report.get("gradualRelease")),
                ("dedication", report.get("dedication")),
            ]
            for i, (key, result) in enumerate(stage_keys_with_results):
                idx = SIX_START + i
                stage = STAGES[idx]
                await asyncio.sleep(0.15)
                yield _sse_event("stage_complete", {
                    "stage": key,
                    "label": stage["label"],
                    "index": idx,
                    "result": result,
                })

            # 阶段 7：决策
            stage = STAGES[SIX_START + 6]
            yield _sse_event("stage_start", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": SIX_START + 6,
                "total": total,
                "message": stage["message"],
            })
            await asyncio.sleep(0.15)
            yield _sse_event("stage_complete", {
                "stage": stage["key"],
                "label": stage["label"],
                "index": SIX_START + 6,
                "result": {
                    "decision": report.get("decision"),
                    "reasoningSummary": report.get("reasoningSummary"),
                },
            })

        # ── 阶段 8：戒律校验（enforce_precepts）──
        enforce_idx = SIX_START + 7
        stage = STAGES[enforce_idx]
        yield _sse_event("stage_start", {
            "stage": stage["key"],
            "label": stage["label"],
            "index": enforce_idx,
            "total": total,
            "message": stage["message"],
        })
        report = await asyncio.to_thread(enforce_precepts, report, rules_provider=get_rules_config)
        await asyncio.sleep(0.2)
        yield _sse_event("stage_complete", {
            "stage": stage["key"],
            "label": stage["label"],
            "index": enforce_idx,
            "result": {
                "hardBlock": report.get("precepts", {}).get("hardBlock", False),
                "decision": report.get("decision"),
                "reasoningSummary": report.get("reasoningSummary"),
            },
        })

        # ── 阶段 9：生成摘要 ──
        summary_idx = SIX_START + 8
        stage = STAGES[summary_idx]
        yield _sse_event("stage_start", {
            "stage": stage["key"],
            "label": stage["label"],
            "index": summary_idx,
            "total": total,
            "message": stage["message"],
        })
        summary = _build_summary(report, request_id)
        response = RequestReportResponse(request_id=request_id, report=report, summary=summary)
        saved = await asyncio.to_thread(save_report, response)
        await asyncio.sleep(0.15)
        yield _sse_event("stage_complete", {
            "stage": stage["key"],
            "label": stage["label"],
            "index": summary_idx,
            "result": summary.model_dump(),
        })

        # ── 完成 ──
        yield _sse_event("done", {
            "request_id": saved.request_id,
            "report": saved.report,
            "summary": saved.summary.model_dump() if saved.summary else None,
        })

    except Exception as exc:
        yield _sse_event("error", {"message": str(exc)})
