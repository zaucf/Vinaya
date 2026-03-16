"use client";

import { useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

type PreceptConfig = {
  name: string;
  enabled: boolean;
  description: string;
  severity: "warning" | "block";
};

type DeferStrategy = {
  strategy_id: string;
  name: string;
  description: string;
  enabled: boolean;
  default_duration_hours: number;
  require_human_review: boolean;
  auto_rollback: boolean;
};

type RiskThresholds = {
  auto_allow_max_risk: string;
  force_human_review_min_risk: string;
  default_defer_duration_hours: number;
  max_auto_decisions_per_hour: number;
};

type RulesConfig = {
  precepts: PreceptConfig[];
  defer_strategies: DeferStrategy[];
  risk_thresholds: RiskThresholds;
};

export function RulesManager({
  initialConfig,
}: {
  initialConfig: RulesConfig;
}) {
  const [config, setConfig] = useState<RulesConfig>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function togglePrecept(index: number) {
    setConfig((prev) => {
      const next = { ...prev, precepts: [...prev.precepts] };
      next.precepts[index] = {
        ...next.precepts[index],
        enabled: !next.precepts[index].enabled,
      };
      return next;
    });
  }

  function togglePreceptSeverity(index: number) {
    setConfig((prev) => {
      const next = { ...prev, precepts: [...prev.precepts] };
      next.precepts[index] = {
        ...next.precepts[index],
        severity: next.precepts[index].severity === "block" ? "warning" : "block",
      };
      return next;
    });
  }

  function toggleStrategy(index: number) {
    setConfig((prev) => {
      const next = { ...prev, defer_strategies: [...prev.defer_strategies] };
      next.defer_strategies[index] = {
        ...next.defer_strategies[index],
        enabled: !next.defer_strategies[index].enabled,
      };
      return next;
    });
  }

  function updateStrategyDuration(index: number, hours: number) {
    setConfig((prev) => {
      const next = { ...prev, defer_strategies: [...prev.defer_strategies] };
      next.defer_strategies[index] = {
        ...next.defer_strategies[index],
        default_duration_hours: hours,
      };
      return next;
    });
  }

  function toggleStrategyHumanReview(index: number) {
    setConfig((prev) => {
      const next = { ...prev, defer_strategies: [...prev.defer_strategies] };
      next.defer_strategies[index] = {
        ...next.defer_strategies[index],
        require_human_review: !next.defer_strategies[index].require_human_review,
      };
      return next;
    });
  }

  function toggleStrategyAutoRollback(index: number) {
    setConfig((prev) => {
      const next = { ...prev, defer_strategies: [...prev.defer_strategies] };
      next.defer_strategies[index] = {
        ...next.defer_strategies[index],
        auto_rollback: !next.defer_strategies[index].auto_rollback,
      };
      return next;
    });
  }

  function updateThreshold(key: string, value: string | number) {
    setConfig((prev) => ({
      ...prev,
      risk_thresholds: { ...prev.risk_thresholds, [key]: value },
    }));
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/rules`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error("保存失败");
      }

      setMessage("规则配置已保存");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <section className="grid two">
        {/* 五戒配置 */}
        <article className="card">
          <h2 className="section-title">五戒配置</h2>
          <p className="muted" style={{ marginBottom: 16 }}>
            五戒是 Vinaya 的最小红线。可以调整严重等级和是否启用。
          </p>
          <div className="table-like">
            {config.precepts.map((precept, index) => (
              <div key={precept.name} className="review-row">
                <div className="review-row-header">
                  <label className="checkbox-field">
                    <input
                      type="checkbox"
                      checked={precept.enabled}
                      onChange={() => togglePrecept(index)}
                    />
                    <strong>{precept.name}</strong>
                  </label>
                  <button
                    className={`pill ${precept.severity === "block" ? "stop" : "defer"}`}
                    onClick={() => togglePreceptSeverity(index)}
                    style={{ cursor: "pointer", border: "1px solid var(--border)" }}
                  >
                    {precept.severity === "block" ? "止行" : "警告"}
                  </button>
                </div>
                <p className="muted" style={{ margin: "8px 0 0" }}>
                  {precept.description}
                </p>
              </div>
            ))}
          </div>
        </article>

        {/* 人工主权边界 */}
        <article className="card">
          <h2 className="section-title">人工主权边界</h2>
          <ul className="list">
            <li>医疗、司法、惩罚性决定必须保留人工主权</li>
            <li>重大资源分配与不可逆后果事项不得由系统单独裁决</li>
            <li>高风险判断默认进入缓行，并建议人工复核</li>
            <li>人工复核结果应覆盖自动建议并留档</li>
          </ul>

          <h2 className="section-title" style={{ marginTop: 24 }}>
            三类结论
          </h2>
          <ul className="list">
            <li>
              <span className="pill allow">allow</span> 可行，可在限定范围推进
            </li>
            <li>
              <span className="pill defer">defer</span>{" "}
              缓行，需要补信息、试行或人工复核
            </li>
            <li>
              <span className="pill stop">stop</span>{" "}
              止行，已触碰红线或风险不可接受
            </li>
          </ul>
        </article>
      </section>

      <section className="grid two" style={{ marginTop: 16 }}>
        {/* 缓行策略 */}
        <article className="card">
          <h2 className="section-title">缓行策略配置</h2>
          <p className="muted" style={{ marginBottom: 16 }}>
            缓行不是拖延，而是一种主动克制。配置不同场景下的缓行执行策略。
          </p>
          <div className="table-like">
            {config.defer_strategies.map((strategy, index) => (
              <div key={strategy.strategy_id} className="review-row">
                <div className="review-row-header">
                  <label className="checkbox-field">
                    <input
                      type="checkbox"
                      checked={strategy.enabled}
                      onChange={() => toggleStrategy(index)}
                    />
                    <strong>{strategy.name}</strong>
                  </label>
                </div>
                <p className="muted" style={{ margin: "8px 0 12px" }}>
                  {strategy.description}
                </p>
                <div className="filters">
                  <label className="field compact">
                    <span>时长（小时）</span>
                    <input
                      type="number"
                      min={1}
                      max={720}
                      value={strategy.default_duration_hours}
                      onChange={(e) =>
                        updateStrategyDuration(index, parseInt(e.target.value) || 1)
                      }
                    />
                  </label>
                  <label className="checkbox-field" style={{ alignSelf: "end", paddingBottom: 10 }}>
                    <input
                      type="checkbox"
                      checked={strategy.require_human_review}
                      onChange={() => toggleStrategyHumanReview(index)}
                    />
                    <span>需要人工复核</span>
                  </label>
                  <label className="checkbox-field" style={{ alignSelf: "end", paddingBottom: 10 }}>
                    <input
                      type="checkbox"
                      checked={strategy.auto_rollback}
                      onChange={() => toggleStrategyAutoRollback(index)}
                    />
                    <span>自动回退</span>
                  </label>
                </div>
              </div>
            ))}
          </div>
        </article>

        {/* 风险阈值 */}
        <article className="card">
          <h2 className="section-title">风险阈值配置</h2>
          <p className="muted" style={{ marginBottom: 16 }}>
            控制系统自动放行和强制人工复核的风险等级边界。
          </p>
          <div className="form">
            <label className="field">
              <span>自动放行最高风险</span>
              <select
                value={config.risk_thresholds.auto_allow_max_risk}
                onChange={(e) =>
                  updateThreshold("auto_allow_max_risk", e.target.value)
                }
              >
                <option value="low">low（仅低风险可自动放行）</option>
                <option value="medium">medium（中风险以下可自动放行）</option>
                <option value="high">high（所有风险均可自动放行，不推荐）</option>
              </select>
            </label>

            <label className="field">
              <span>强制人工复核最低风险</span>
              <select
                value={config.risk_thresholds.force_human_review_min_risk}
                onChange={(e) =>
                  updateThreshold("force_human_review_min_risk", e.target.value)
                }
              >
                <option value="low">low（所有风险均需人工复核）</option>
                <option value="medium">medium（中风险以上需人工复核）</option>
                <option value="high">high（仅高风险需人工复核）</option>
              </select>
            </label>

            <label className="field">
              <span>默认缓行时长（小时）</span>
              <input
                type="number"
                min={1}
                max={720}
                value={config.risk_thresholds.default_defer_duration_hours}
                onChange={(e) =>
                  updateThreshold(
                    "default_defer_duration_hours",
                    parseInt(e.target.value) || 72
                  )
                }
              />
            </label>

            <label className="field">
              <span>每小时最大自动判断数</span>
              <input
                type="number"
                min={1}
                max={1000}
                value={config.risk_thresholds.max_auto_decisions_per_hour}
                onChange={(e) =>
                  updateThreshold(
                    "max_auto_decisions_per_hour",
                    parseInt(e.target.value) || 50
                  )
                }
              />
            </label>
          </div>
        </article>
      </section>

      <section style={{ marginTop: 16 }}>
        <div className="action-row">
          <button
            className="button"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "保存中..." : "保存配置"}
          </button>
          {message ? (
            <span
              className="muted"
              style={{ alignSelf: "center" }}
            >
              {message}
            </span>
          ) : null}
        </div>
      </section>
    </>
  );
}
