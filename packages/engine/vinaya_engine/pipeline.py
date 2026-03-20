from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .types import (
    CausalityResult,
    Decision,
    DedicationResult,
    DeliberationResult,
    GradualReleaseResult,
    IntentionResult,
    JudgmentReport,
    PreceptResult,
    RiskLevel,
    VinayaRequest,
)


def next_review_date(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def rank_risk(levels: list[RiskLevel]) -> RiskLevel:
    if "high" in levels:
        return "high"
    if "medium" in levels:
        return "medium"
    return "low"


# ── 风险自动分类（Mock 模式）──

_HIGH_KEYWORDS = ["删除", "批量", "高风险", "永久", "不可逆", "资金", "转账", "裁员", "解雇", "终止"]
_LOW_KEYWORDS = ["查看", "查询", "报告", "统计", "预览", "测试"]


def mock_classify_risk(title: str, request_text: str, domain: str) -> str:
    """Mock 模式下根据关键词简单分类风险等级。"""
    combined = f"{title} {request_text}".lower()
    for kw in _HIGH_KEYWORDS:
        if kw in combined:
            return "high"
    for kw in _LOW_KEYWORDS:
        if kw in combined:
            return "low"
    return "medium"


def run_intention(request: VinayaRequest) -> IntentionResult:
    return {
        "primaryIntent": request.get("title") or "澄清该请求的真实目标",
        "mixedMotives": ["快速降低风险暴露", "缩短人工处理时间"]
        if request["riskLevel"] == "high"
        else ["提升处理效率"],
        "beneficiaries": ["系统使用者", "受影响的业务流程"],
        "costBearers": ["被决策对象", "人工复核人员"],
        "intentionRisk": "high" if request["riskLevel"] == "high" else "medium",
    }


def run_causality(request: VinayaRequest) -> CausalityResult:
    return {
        "proximateCauses": ["收到新的高影响判断请求", "需要在执行前做净化审查"],
        "rootCauses": ["自动化决策风险较高", "需要明确执行边界与回退机制"],
        "affectedParties": ["请求提交者", "被影响对象", "后续审核人员"],
        "externalities": ["误判会扩大影响面", "可能带来不可回退后果"]
        if request["riskLevel"] == "high"
        else ["若解释不足，会影响系统信任感"],
        "causalityRisk": request["riskLevel"],
    }


def run_precepts(request: VinayaRequest) -> PreceptResult:
    findings = [
        {
            "name": "不妄语",
            "status": "warning",
            "reason": "当前为原型阶段，结论必须明确标注不确定性。",
        },
        {
            "name": "不越界",
            "status": "warning" if request["riskLevel"] == "high" else "pass",
            "reason": "高风险请求必须保留人工主权。"
            if request["riskLevel"] == "high"
            else "当前请求可在原型边界内分析。",
        },
    ]

    return {
        "preceptFindings": findings,
        "hardBlock": False,
        "humanReviewRequired": request["riskLevel"] != "low",
        "preceptRisk": request["riskLevel"],
    }


def run_deliberation(request: VinayaRequest) -> DeliberationResult:
    return {
        "options": [
            {"name": "直接执行原请求", "score": 0.72 if request["riskLevel"] == "low" else 0.28},
            {"name": "先小范围试行并设置回退条件", "score": 0.91},
            {"name": "转人工复核后再决定", "score": 0.95 if request["riskLevel"] == "high" else 0.76},
        ],
        "preferredOption": "先小范围试行并设置回退条件"
        if request["riskLevel"] == "low"
        else "转人工复核后再决定",
        "dissentNotes": ["当前信息量有限，不宜把自动结论包装成最终裁定。"],
        "deliberationRisk": "medium" if request["riskLevel"] == "low" else request["riskLevel"],
        "roleDebates": [
            {
                "role": "advocate",
                "stance": "请求目标明确，执行收益大于风险",
                "reasoning": "从请求方立场看，该请求有清晰的业务目标，"
                "在受控条件下执行可带来显著效率提升，风险可通过回退机制管控。",
                "suggestedOption": "先小范围试行并设置回退条件",
            },
            {
                "role": "critic",
                "stance": "信息不充分，盲目执行可能造成不可逆后果",
                "reasoning": "当前对受影响方的评估仍有盲点，"
                "一旦出现误判可能扩大影响面，建议优先补充信息后再决策。",
                "suggestedOption": "转人工复核后再决定",
            },
            {
                "role": "moderator",
                "stance": "综合两方意见，建议在有限范围内审慎推进",
                "reasoning": "倡导者指出的收益合理，批评者的风险担忧也有依据。"
                "折中方案是小范围试行，同时保留人工复核通道。",
                "suggestedOption": "先小范围试行并设置回退条件"
                if request["riskLevel"] == "low"
                else "转人工复核后再决定",
            },
        ],
        "consensusLevel": 0.82 if request["riskLevel"] == "low" else 0.61,
    }


def run_gradual_release(request: VinayaRequest) -> GradualReleaseResult:
    if request["riskLevel"] == "high":
        return {
            "mode": "defer",
            "trialPlan": {
                "action": "进入人工复核队列并冻结自动执行",
                "scope": "仅生成建议，不触发真实动作",
                "reviewAt": next_review_date(1),
                "rollbackCondition": "人工认定风险过高或信息不足时停止推进",
                "humanOwner": "human-review-owner",
            },
            "releaseRisk": "high",
        }

    if request["riskLevel"] == "medium":
        return {
            "mode": "defer",
            "trialPlan": {
                "action": "小范围试行并记录反馈",
                "scope": "限制在单一场景或沙盒环境",
                "reviewAt": next_review_date(3),
                "rollbackCondition": "出现误伤、投诉或关键指标下降时立即回退",
                "humanOwner": "ops-review-owner",
            },
            "releaseRisk": "medium",
        }

    return {
        "mode": "allow",
        "trialPlan": {
            "action": "允许在受控环境执行",
            "scope": "低风险范围",
            "reviewAt": next_review_date(7),
            "rollbackCondition": "若产生异常结果则回退",
            "humanOwner": "system-owner",
        },
        "releaseRisk": "low",
    }


def run_dedication(request: VinayaRequest) -> DedicationResult:
    if request["riskLevel"] == "high":
        return {
            "lessonsLearned": [
                "高风险请求不应绕过人工复核",
                "系统克制优先于效率提升",
            ],
            "followUpActions": [
                "48 小时内由人工负责人确认最终处置",
                "将本次判断纳入高风险案例库以供后续参考",
            ],
            "meritDedication": "本次审慎决策保护了被决策对象免受不可回退伤害，功德回向所有受影响方。",
            "dedicationRisk": "high",
        }

    if request["riskLevel"] == "medium":
        return {
            "lessonsLearned": [
                "中等风险下仍需保持克制",
                "试行方案需设置明确的回退条件",
            ],
            "followUpActions": [
                "在试行期结束后复盘执行效果",
                "记录本次判断路径供后续类似请求参考",
            ],
            "meritDedication": "本次判断在效率与审慎之间取得平衡，功德回向请求提交者与受影响的业务流程。",
            "dedicationRisk": "medium",
        }

    return {
        "lessonsLearned": [
            "低风险请求同样经过了完整净化流程",
        ],
        "followUpActions": [
            "定期回顾低风险判断是否出现漏判",
        ],
        "meritDedication": "本次判断虽风险可控，仍以完整流程确保无遗漏，功德回向所有参与方。",
        "dedicationRisk": "low",
    }


def resolve_decision(
    request: VinayaRequest,
    precepts: PreceptResult,
    release: GradualReleaseResult,
) -> Decision:
    if precepts["hardBlock"]:
        return "stop"
    if request["riskLevel"] == "high":
        return "defer"
    return release["mode"]


def run_vinaya_pipeline(request: VinayaRequest) -> JudgmentReport:
    intention = run_intention(request)
    causality = run_causality(request)
    precepts = run_precepts(request)
    deliberation = run_deliberation(request)
    gradual_release = run_gradual_release(request)
    dedication = run_dedication(request)
    decision = resolve_decision(request, precepts, gradual_release)
    overall_risk = rank_risk(
        [
            intention["intentionRisk"],
            causality["causalityRisk"],
            precepts["preceptRisk"],
            deliberation["deliberationRisk"],
            gradual_release["releaseRisk"],
            dedication["dedicationRisk"],
        ]
    )

    return {
        "request": request,
        "intention": intention,
        "causality": causality,
        "precepts": precepts,
        "deliberation": deliberation,
        "gradualRelease": gradual_release,
        "dedication": dedication,
        "decision": decision,
        "reasoningSummary": f"综合判断为 {overall_risk} 风险，但当前可在受控范围内推进。"
        if decision == "allow"
        else f"综合判断为 {overall_risk} 风险，建议缓行并保留人工复核。"
        if decision == "defer"
        else "综合判断触发止行条件，不建议继续推进。",
    }
