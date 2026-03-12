from __future__ import annotations

from typing import Literal, TypedDict

RiskLevel = Literal["low", "medium", "high"]
Decision = Literal["allow", "defer", "stop"]
PreceptStatus = Literal["pass", "warning", "block"]


class VinayaRequest(TypedDict, total=False):
    requestId: str
    requestModelId: str
    title: str
    requestText: str
    domain: str
    riskLevel: RiskLevel
    context: str


class IntentionResult(TypedDict):
    primaryIntent: str
    mixedMotives: list[str]
    beneficiaries: list[str]
    costBearers: list[str]
    intentionRisk: RiskLevel


class CausalityResult(TypedDict):
    proximateCauses: list[str]
    rootCauses: list[str]
    affectedParties: list[str]
    externalities: list[str]
    causalityRisk: RiskLevel


class PreceptFinding(TypedDict):
    name: str
    status: PreceptStatus
    reason: str


class PreceptResult(TypedDict):
    preceptFindings: list[PreceptFinding]
    hardBlock: bool
    humanReviewRequired: bool
    preceptRisk: RiskLevel


class DeliberationOption(TypedDict):
    name: str
    score: float


class DeliberationResult(TypedDict):
    options: list[DeliberationOption]
    preferredOption: str
    dissentNotes: list[str]
    deliberationRisk: RiskLevel


class TrialPlan(TypedDict):
    action: str
    scope: str
    reviewAt: str
    rollbackCondition: str
    humanOwner: str


class GradualReleaseResult(TypedDict):
    mode: Decision
    trialPlan: TrialPlan | None
    releaseRisk: RiskLevel


class JudgmentReport(TypedDict):
    request: VinayaRequest
    intention: IntentionResult
    causality: CausalityResult
    precepts: PreceptResult
    deliberation: DeliberationResult
    gradualRelease: GradualReleaseResult
    decision: Decision
    reasoningSummary: str
