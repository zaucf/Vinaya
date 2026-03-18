"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const riskLevels = [
  { value: "low", label: "低风险" },
  { value: "medium", label: "中风险" },
  { value: "high", label: "高风险" },
] as const;

const PRESET_DOMAINS = [
  { value: "content-moderation", label: "内容审核" },
  { value: "risk-review", label: "风险复核" },
  { value: "operations-trial", label: "运营试行" },
  { value: "hr-decision", label: "人事决策" },
  { value: "finance-approval", label: "财务审批" },
  { value: "legal-compliance", label: "法律合规" },
  { value: "customer-escalation", label: "客诉升级" },
] as const;

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

type RiskLevel = (typeof riskLevels)[number]["value"];

type RequestModel = {
  model_id: string;
  name: string;
  description: string;
  domain: string;
  default_risk_level: RiskLevel;
  default_title: string;
  placeholder_request_text: string;
  placeholder_context: string;
  human_review_required: boolean;
};

export function RequestForm() {
  const router = useRouter();
  const [models, setModels] = useState<RequestModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState("");
  const [title, setTitle] = useState("");
  const [domain, setDomain] = useState("content-moderation");
  const [riskLevel, setRiskLevel] = useState<RiskLevel>("medium");
  const [requestText, setRequestText] = useState("");
  const [context, setContext] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loadingModels, setLoadingModels] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedModel = useMemo(
    () => models.find((item) => item.model_id === selectedModelId) ?? null,
    [models, selectedModelId]
  );

  useEffect(() => {
    let cancelled = false;

    async function loadModels() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/request-models`, {
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error("请求模型加载失败，请确认 FastAPI 已启动。");
        }

        const data = (await response.json()) as { items: RequestModel[] };
        if (cancelled) {
          return;
        }

        setModels(data.items);
        const firstModel = data.items[0];
        if (!firstModel) {
          return;
        }

        setSelectedModelId(firstModel.model_id);
        setTitle(firstModel.default_title);
        setDomain(firstModel.domain);
        setRiskLevel(firstModel.default_risk_level);
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error ? loadError.message : "请求模型加载失败"
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingModels(false);
        }
      }
    }

    loadModels();

    return () => {
      cancelled = true;
    };
  }, []);

  function handleModelChange(nextModelId: string) {
    setSelectedModelId(nextModelId);
    const nextModel = models.find((item) => item.model_id === nextModelId);

    if (!nextModel) {
      return;
    }

    setTitle(nextModel.default_title);
    setDomain(nextModel.domain);
    setRiskLevel(nextModel.default_risk_level);
    setRequestText("");
    setContext("");
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/requests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title,
          domain,
          risk_level: riskLevel,
          request_text: requestText,
          context,
          request_model_id: selectedModelId || null,
        }),
      });
      if (!response.ok) {
        throw new Error("Python API 请求失败，请确认 FastAPI 已启动。");
      }

      const data = await response.json();
      router.push(`/requests/${data.request_id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2 className="section-title">提交判断请求</h2>
      <label className="field">
        <span>请求模型</span>
        <select
          value={selectedModelId}
          onChange={(event) => handleModelChange(event.target.value)}
          disabled={loadingModels || models.length === 0}
        >
          {models.map((item) => (
            <option key={item.model_id} value={item.model_id}>
              {item.name}
            </option>
          ))}
        </select>
      </label>

      {selectedModel ? (
        <div className="card inset-card">
          <strong>{selectedModel.name}</strong>
          <p className="muted" style={{ marginTop: 8 }}>
            {selectedModel.description}
          </p>
          <p className="muted" style={{ marginBottom: 0 }}>
            默认领域：{selectedModel.domain} · 默认风险：
            {selectedModel.default_risk_level} ·
            {selectedModel.human_review_required
              ? " 需要人工复核"
              : " 可先受控试行"}
          </p>
        </div>
      ) : null}

      <label className="field">
        <span>标题</span>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
        />
      </label>
      <label className="field">
        <span>领域</span>
        <select
          value={PRESET_DOMAINS.some((d) => d.value === domain) ? domain : "__custom__"}
          onChange={(event) => {
            if (event.target.value === "__custom__") {
              setDomain("");
            } else {
              setDomain(event.target.value);
            }
          }}
        >
          {PRESET_DOMAINS.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
          <option value="__custom__">自定义...</option>
        </select>
        {!PRESET_DOMAINS.some((d) => d.value === domain) && (
          <input
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
            placeholder="输入自定义领域"
            required
            style={{ marginTop: 8 }}
          />
        )}
      </label>
      <label className="field">
        <span>风险等级</span>
        <select
          value={riskLevel}
          onChange={(event) => setRiskLevel(event.target.value as RiskLevel)}
        >
          {riskLevels.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>请求内容</span>
        <textarea
          value={requestText}
          onChange={(event) => setRequestText(event.target.value)}
          rows={6}
          placeholder={
            selectedModel?.placeholder_request_text ?? "请描述请求内容"
          }
          required
        />
      </label>
      <label className="field">
        <span>补充上下文</span>
        <textarea
          value={context}
          onChange={(event) => setContext(event.target.value)}
          rows={4}
          placeholder={selectedModel?.placeholder_context ?? "补充上下文信息"}
        />
      </label>
      {error ? <p className="error-text">{error}</p> : null}
      <button
        className="button"
        type="submit"
        disabled={submitting || loadingModels}
      >
        {submitting ? "提交中..." : "生成判断报告"}
      </button>
    </form>
  );
}
