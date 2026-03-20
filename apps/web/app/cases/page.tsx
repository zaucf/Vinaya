"use client";

import { useEffect, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

interface CaseItem {
  confession_id: string;
  request_id: string;
  domain: string;
  risk_level: string;
  original_decision: string;
  override_comment: string;
  reviewer: string;
  action_taken: string;
  created_at: string;
  title: string;
  reasoning_summary: string;
}

const DECISION_LABELS: Record<string, string> = {
  allow: "允许",
  defer: "缓行",
  stop: "止行",
};

const RISK_LABELS: Record<string, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [domainFilter, setDomainFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const params = new URLSearchParams();
        if (domainFilter) params.set("domain", domainFilter);
        if (riskFilter) params.set("risk_level", riskFilter);
        const qs = params.toString();
        const url = `${apiBaseUrl}/api/cases${qs ? `?${qs}` : ""}`;
        const resp = await fetch(url, { cache: "no-store" });
        if (!resp.ok) throw new Error("加载案例库失败");
        const data = await resp.json();
        setCases(data.items);
      } catch (e) {
        setError(e instanceof Error ? e.message : "加载失败");
      } finally {
        setLoading(false);
      }
    }
    setLoading(true);
    load();
  }, [domainFilter, riskFilter]);

  const domains = [...new Set(cases.map((c) => c.domain))];

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Cases</div>
          <h1>案例库</h1>
          <p className="muted">
            人工推翻系统判断的历史记录，每一次纠正都让系统变得更好。
          </p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <div className="filters" style={{ marginBottom: 20 }}>
        <label className="field compact">
          <span>领域</span>
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
          >
            <option value="">全部领域</option>
            {domains.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label className="field compact">
          <span>风险等级</span>
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
          >
            <option value="">全部等级</option>
            <option value="low">低风险</option>
            <option value="medium">中风险</option>
            <option value="high">高风险</option>
          </select>
        </label>
      </div>

      {loading && <p className="muted">加载中...</p>}
      {error && <p className="error-text">{error}</p>}

      {!loading && !error && cases.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p style={{ fontSize: 18, marginBottom: 8 }}>
            暂无推翻案例，系统运行良好
          </p>
          <p className="muted">
            当人工复核推翻系统判断时，案例会自动记录在这里。
          </p>
        </div>
      )}

      {!loading && !error && cases.length > 0 && (
        <div className="table-like">
          {cases.map((c) => (
            <div key={c.confession_id} className="card" style={{ padding: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: 12,
                  marginBottom: 10,
                }}
              >
                <div>
                  <strong>{c.title || c.request_id}</strong>
                  <div style={{ marginTop: 6 }}>
                    <span className="pill">{c.domain}</span>
                    <span
                      className={`pill ${
                        c.risk_level === "high"
                          ? "stop"
                          : c.risk_level === "medium"
                            ? "defer"
                            : "allow"
                      }`}
                    >
                      {RISK_LABELS[c.risk_level] ?? c.risk_level}
                    </span>
                  </div>
                </div>
                <span className="muted" style={{ fontSize: 13, whiteSpace: "nowrap" }}>
                  {new Date(c.created_at).toLocaleString("zh-CN")}
                </span>
              </div>

              <div style={{ marginBottom: 8 }}>
                <span
                  className={`pill ${c.original_decision}`}
                  style={{ fontSize: 12 }}
                >
                  系统原判：{DECISION_LABELS[c.original_decision] ?? c.original_decision}
                </span>
                <span style={{ margin: "0 4px", color: "var(--muted)" }}>
                  &rarr;
                </span>
                <span className="pill override" style={{ fontSize: 12 }}>
                  人工推翻
                </span>
              </div>

              <p className="muted" style={{ margin: "6px 0" }}>
                <strong>推翻理由：</strong>
                {c.override_comment}
              </p>

              <p className="muted" style={{ margin: "6px 0" }}>
                <strong>补赎动作：</strong>
                {c.action_taken}
              </p>

              <p className="muted" style={{ margin: "6px 0 0", fontSize: 13 }}>
                复核人：{c.reviewer}
              </p>

              {c.reasoning_summary && (
                <p
                  className="muted"
                  style={{
                    margin: "8px 0 0",
                    padding: "8px 12px",
                    background: "#f0f0f0",
                    borderRadius: 8,
                    fontSize: 13,
                  }}
                >
                  {c.reasoning_summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
