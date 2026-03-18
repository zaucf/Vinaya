"use client";

import { useEffect, useRef, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

/** 8 个阶段定义 */
const STAGE_DEFS = [
  { key: "intention", label: "发心" },
  { key: "causality", label: "观缘" },
  { key: "precepts", label: "持戒" },
  { key: "deliberation", label: "辩义" },
  { key: "gradualRelease", label: "缓行" },
  { key: "decision", label: "决策" },
  { key: "enforce", label: "戒律校验" },
  { key: "summary", label: "生成摘要" },
] as const;

type StageStatus = "pending" | "running" | "complete";

interface StageState {
  key: string;
  label: string;
  status: StageStatus;
  message?: string;
  result?: Record<string, unknown>;
}

interface DonePayload {
  request_id: string;
  report: Record<string, unknown>;
  summary: Record<string, unknown> | null;
}

interface JudgmentProgressProps {
  payload: {
    title: string;
    domain: string;
    risk_level: string;
    request_text: string;
    context: string;
    request_model_id: string | null;
  };
  onComplete: (data: DonePayload) => void;
  onError: (message: string) => void;
}

/** 解析 SSE 文本流为 {event, data} 对 */
function parseSSE(chunk: string): Array<{ event: string; data: string }> {
  const results: Array<{ event: string; data: string }> = [];
  const blocks = chunk.split("\n\n");
  for (const block of blocks) {
    if (!block.trim()) continue;
    let event = "message";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event: ")) {
        event = line.slice(7);
      } else if (line.startsWith("data: ")) {
        data = line.slice(6);
      }
    }
    if (data) {
      results.push({ event, data });
    }
  }
  return results;
}

/** 渲染阶段详情 */
function StageDetail({ stageKey, result }: { stageKey: string; result: Record<string, unknown> }) {
  switch (stageKey) {
    case "intention": {
      const r = result as {
        primaryIntent?: string;
        mixedMotives?: string[];
        beneficiaries?: string[];
        costBearers?: string[];
        intentionRisk?: string;
      };
      return (
        <div className="stage-result">
          <p><strong>主要意图：</strong>{r.primaryIntent}</p>
          {r.mixedMotives && r.mixedMotives.length > 0 && (
            <p><strong>混杂动机：</strong>{r.mixedMotives.join("、")}</p>
          )}
          {r.beneficiaries && r.beneficiaries.length > 0 && (
            <p><strong>受益者：</strong>{r.beneficiaries.join("、")}</p>
          )}
          {r.costBearers && r.costBearers.length > 0 && (
            <p><strong>代价承担者：</strong>{r.costBearers.join("、")}</p>
          )}
          {r.intentionRisk && <span className={`pill ${r.intentionRisk}`}>{r.intentionRisk} 风险</span>}
        </div>
      );
    }
    case "causality": {
      const r = result as {
        externalities?: string[];
        affectedParties?: string[];
        causalityRisk?: string;
      };
      return (
        <div className="stage-result">
          {r.affectedParties && r.affectedParties.length > 0 && (
            <p><strong>受影响方：</strong>{r.affectedParties.join("、")}</p>
          )}
          {r.externalities && r.externalities.length > 0 && (
            <p><strong>外部性：</strong>{r.externalities.join("、")}</p>
          )}
          {r.causalityRisk && <span className={`pill ${r.causalityRisk}`}>{r.causalityRisk} 风险</span>}
        </div>
      );
    }
    case "precepts": {
      const r = result as {
        preceptFindings?: Array<{ name: string; status: string; reason: string }>;
        hardBlock?: boolean;
        preceptRisk?: string;
      };
      return (
        <div className="stage-result">
          {r.preceptFindings?.map((f) => (
            <p key={f.name}>
              <span className={`pill ${f.status}`}>{f.status}</span>
              <strong>{f.name}：</strong>{f.reason}
            </p>
          ))}
          {r.hardBlock && <p style={{ color: "var(--stop)" }}>触发硬约束阻止</p>}
        </div>
      );
    }
    case "deliberation": {
      const r = result as {
        options?: Array<{ name: string; score: number }>;
        preferredOption?: string;
        deliberationRisk?: string;
      };
      return (
        <div className="stage-result">
          {r.options?.map((opt) => (
            <p key={opt.name}>
              {opt.name === r.preferredOption ? <strong>{opt.name}</strong> : opt.name}
              {" "}— 得分 {opt.score.toFixed(2)}
            </p>
          ))}
        </div>
      );
    }
    case "gradualRelease": {
      const r = result as {
        mode?: string;
        trialPlan?: { action?: string; scope?: string; rollbackCondition?: string };
        releaseRisk?: string;
      };
      return (
        <div className="stage-result">
          {r.mode && <span className={`pill ${r.mode}`}>{r.mode}</span>}
          {r.trialPlan && (
            <>
              <p><strong>动作：</strong>{r.trialPlan.action}</p>
              <p><strong>范围：</strong>{r.trialPlan.scope}</p>
              <p><strong>回退条件：</strong>{r.trialPlan.rollbackCondition}</p>
            </>
          )}
        </div>
      );
    }
    case "decision": {
      const r = result as { decision?: string; reasoningSummary?: string };
      return (
        <div className="stage-result">
          {r.decision && <span className={`pill ${r.decision}`}>{r.decision}</span>}
          {r.reasoningSummary && <p className="muted">{r.reasoningSummary}</p>}
        </div>
      );
    }
    case "enforce": {
      const r = result as { hardBlock?: boolean; decision?: string; reasoningSummary?: string };
      return (
        <div className="stage-result">
          <p><strong>硬约束：</strong>{r.hardBlock ? "已触发" : "未触发"}</p>
          {r.decision && <span className={`pill ${r.decision}`}>最终决策：{r.decision}</span>}
        </div>
      );
    }
    case "summary": {
      const r = result as {
        decision?: string;
        risk_level?: string;
        reasoning?: string;
        hard_block?: boolean;
        human_review_required?: boolean;
      };
      return (
        <div className="stage-result">
          {r.decision && <span className={`pill ${r.decision}`}>{r.decision}</span>}
          {r.risk_level && <span className={`pill ${r.risk_level}`}>{r.risk_level} 风险</span>}
          {r.human_review_required && <span className="pill defer">需人工复核</span>}
          {r.reasoning && <p className="muted">{r.reasoning}</p>}
        </div>
      );
    }
    default:
      return <pre className="stage-result">{JSON.stringify(result, null, 2)}</pre>;
  }
}

export function JudgmentProgress({ payload, onComplete, onError }: JudgmentProgressProps) {
  const [stages, setStages] = useState<StageState[]>(
    STAGE_DEFS.map((s) => ({ key: s.key, label: s.label, status: "pending" }))
  );
  const [llmCalling, setLlmCalling] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    abortRef.current = controller;

    async function run() {
      let buffer = "";
      try {
        const resp = await fetch(`${apiBaseUrl}/api/requests/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        if (!resp.ok || !resp.body) {
          onError("SSE 连接失败，请确认后端已启动。");
          return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = parseSSE(buffer);

          // 保留未完成的最后一个块
          const lastDoubleNewline = buffer.lastIndexOf("\n\n");
          if (lastDoubleNewline >= 0) {
            buffer = buffer.slice(lastDoubleNewline + 2);
          }

          for (const evt of events) {
            const data = JSON.parse(evt.data);

            switch (evt.event) {
              case "stage_start":
                setStages((prev) =>
                  prev.map((s) =>
                    s.key === data.stage
                      ? { ...s, status: "running", message: data.message }
                      : s
                  )
                );
                break;

              case "stage_complete":
                setStages((prev) =>
                  prev.map((s) =>
                    s.key === data.stage
                      ? { ...s, status: "complete", result: data.result }
                      : s
                  )
                );
                break;

              case "llm_call_start":
                setLlmCalling(true);
                break;

              case "done":
                setLlmCalling(false);
                onComplete(data as DonePayload);
                return;

              case "error":
                onError(data.message || "判断过程出错");
                return;
            }
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          onError(err instanceof Error ? err.message : "连接中断");
        }
      }
    }

    run();

    return () => {
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="stage-timeline">
      <h2 className="section-title">判断过程</h2>
      {llmCalling && (
        <div className="card inset-card" style={{ marginBottom: 16 }}>
          <span className="stage-spinner" /> 正在调用 LLM 进行六阶段分析...
        </div>
      )}
      {stages.map((stage) => (
        <div
          key={stage.key}
          className={`stage-item ${stage.status}`}
        >
          <div className="stage-header">
            <div className="stage-indicator">
              {stage.status === "pending" && <span className="stage-dot" />}
              {stage.status === "running" && <span className="stage-spinner" />}
              {stage.status === "complete" && <span className="stage-check" />}
            </div>
            <div className="stage-label">
              <strong>{stage.label}</strong>
              {stage.status === "running" && stage.message && (
                <span className="muted" style={{ marginLeft: 8, fontSize: 13 }}>
                  {stage.message}
                </span>
              )}
            </div>
          </div>
          {stage.status === "complete" && stage.result && (
            <StageDetail stageKey={stage.key} result={stage.result} />
          )}
        </div>
      ))}
    </div>
  );
}
