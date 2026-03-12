export type RiskLevel = "low" | "medium" | "high";
export type Decision = "allow" | "defer" | "stop";

export interface VinayaRequest {
  requestId: string;
  title: string;
  requestText: string;
  domain: string;
  riskLevel: RiskLevel;
  context?: string;
}

export interface IntentionResult {
  primaryIntent: string;
  mixedMotives: string[];
  beneficiaries: string[];
  costBearers: string[];
  intentionRisk: RiskLevel;
}

export interface CausalityResult {
  proximateCauses: string[];
  rootCauses: string[];
  affectedParties: string[];
  externalities: string[];
  causalityRisk: RiskLevel;
}

export interface PreceptFinding {
  name: string;
  status: "pass" | "warning" | "block";
  reason: string;
}

export interface PreceptResult {
  preceptFindings: PreceptFinding[];
  hardBlock: boolean;
  humanReviewRequired: boolean;
  preceptRisk: RiskLevel;
}

export interface DeliberationOption {
  name: string;
  score: number;
}

export interface DeliberationResult {
  options: DeliberationOption[];
  preferredOption: string;
  dissentNotes: string[];
  deliberationRisk: RiskLevel;
}

export interface TrialPlan {
  action: string;
  scope: string;
  reviewAt: string;
  rollbackCondition: string;
  humanOwner: string;
}

export interface GradualReleaseResult {
  mode: Decision;
  trialPlan?: TrialPlan;
  releaseRisk: RiskLevel;
}

export interface JudgmentReport {
  request: VinayaRequest;
  intention: IntentionResult;
  causality: CausalityResult;
  precepts: PreceptResult;
  deliberation: DeliberationResult;
  gradualRelease: GradualReleaseResult;
  decision: Decision;
  reasoningSummary: string;
}
