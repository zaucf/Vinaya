from __future__ import annotations

import json
from typing import Any

from apps.api.vinaya_api.llm import chat_json
from apps.api.vinaya_api.services.rules import get_rules_config

from .pipeline import rank_risk
from .types import JudgmentReport, VinayaRequest

BASE_SYSTEM_PROMPT = """你是 Vinaya 判断净化引擎。你必须基于输入请求，输出严格 JSON，不要输出 Markdown。
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


def _build_system_prompt() -> str:
    """根据当前戒律配置动态生成 system prompt。"""
    config = get_rules_config()

    # 只告诉 LLM 当前启用的戒律
    enabled_precepts = [p for p in config.precepts if p.enabled]
    if not enabled_precepts:
        precept_section = "\n当前没有启用任何戒律，preceptFindings 返回空数组即可。"
    else:
        lines = []
        for p in enabled_precepts:
            lines.append(f"- {p.name}（{p.severity}级）：{p.description}")
        precept_section = (
            "\n你必须检查以下已启用的戒律，并在 preceptFindings 中逐条报告：\n"
            + "\n".join(lines)
            + "\n其中标注为 block 级的戒律一旦触发 warning 或 block，系统会强制止行。"
        )

    # 告诉 LLM 当前的风险阈值
    thresholds = config.risk_thresholds
    threshold_section = (
        f"\n当前风险阈值：自动放行上限={thresholds.get('auto_allow_max_risk', 'low')}，"
        f"强制人工复核下限={thresholds.get('force_human_review_min_risk', 'high')}。"
        f"超过自动放行上限的请求不应输出 allow。"
    )

    return BASE_SYSTEM_PROMPT + precept_section + threshold_section


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
    system_prompt = _build_system_prompt()
    result = chat_json(system_prompt=system_prompt, user_prompt=_build_user_prompt(request))
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
