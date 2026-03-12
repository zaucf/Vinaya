from __future__ import annotations

import json
from typing import Any

from apps.api.vinaya_api.llm import chat_json

from .pipeline import rank_risk
from .types import JudgmentReport, VinayaRequest

SYSTEM_PROMPT = """你是 Vinaya 判断净化引擎。你必须基于输入请求，输出严格 JSON，不要输出 Markdown。
目标不是替用户拍板，而是完成六阶段净化分析，并给出 allow/defer/stop 三类建议之一。
你必须保持克制：高风险或信息不足时优先 defer，明显越界时 stop。
JSON 必须包含以下顶层字段：intention, causality, precepts, deliberation, gradualRelease, decision, reasoningSummary。
字段要求：
- intention: primaryIntent(string), mixedMotives(string[]), beneficiaries(string[]), costBearers(string[]), intentionRisk(low|medium|high)
- causality: proximateCauses(string[]), rootCauses(string[]), affectedParties(string[]), externalities(string[]), causalityRisk(low|medium|high)
- precepts: preceptFindings([{name,status,reason}]), hardBlock(boolean), humanReviewRequired(boolean), preceptRisk(low|medium|high)
- deliberation: options([{name,score}]), preferredOption(string), dissentNotes(string[]), deliberationRisk(low|medium|high)
- gradualRelease: mode(allow|defer|stop), trialPlan({action,scope,reviewAt,rollbackCondition,humanOwner}|null), releaseRisk(low|medium|high)
- decision: allow|defer|stop
- reasoningSummary: string
其中 preceptFindings[].status 只能是 pass|warning|block。options[].score 是 0 到 1 的浮点数。"""


def _build_user_prompt(request: VinayaRequest) -> str:
    return json.dumps(
        {
            "requestId": request.get("requestId"),
            "requestModelId": request.get("requestModelId"),
            "title": request.get("title"),
            "requestText": request.get("requestText"),
            "domain": request.get("domain"),
            "riskLevel": request.get("riskLevel"),
            "context": request.get("context", ""),
        },
        ensure_ascii=False,
        indent=2,
    )


def run_vinaya_llm_pipeline(request: VinayaRequest) -> JudgmentReport:
    result = chat_json(system_prompt=SYSTEM_PROMPT, user_prompt=_build_user_prompt(request))
    overall_risk = rank_risk(
        [
            result["intention"]["intentionRisk"],
            result["causality"]["causalityRisk"],
            result["precepts"]["preceptRisk"],
            result["deliberation"]["deliberationRisk"],
            result["gradualRelease"]["releaseRisk"],
        ]
    )

    reasoning_summary = result.get("reasoningSummary") or f"综合判断为 {overall_risk} 风险。"

    return {
        "request": request,
        "intention": result["intention"],
        "causality": result["causality"],
        "precepts": result["precepts"],
        "deliberation": result["deliberation"],
        "gradualRelease": result["gradualRelease"],
        "decision": result["decision"],
        "reasoningSummary": reasoning_summary,
    }
