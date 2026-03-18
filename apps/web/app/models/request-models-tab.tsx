"use client";

import { useEffect, useState } from "react";

type RequestModel = {
  model_id: string;
  name: string;
  description: string;
  domain: string;
  default_risk_level: "low" | "medium" | "high";
  default_title: string;
  placeholder_request_text: string;
  placeholder_context: string;
  human_review_required: boolean;
};

export function RequestModelsTab() {
  const [models, setModels] = useState<RequestModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    model_id: "",
    name: "",
    description: "",
    domain: "",
    default_risk_level: "medium" as "low" | "medium" | "high",
    default_title: "",
    placeholder_request_text: "",
    placeholder_context: "",
    human_review_required: false,
  });

  const PRESET_DOMAINS = [
    { value: "content-moderation", label: "内容审核" },
    { value: "risk-review", label: "风险复核" },
    { value: "operations-trial", label: "运营试行" },
    { value: "hr-decision", label: "人事决策" },
    { value: "finance-approval", label: "财务审批" },
    { value: "legal-compliance", label: "法律合规" },
    { value: "customer-escalation", label: "客诉升级" },
  ];
  const [customDomain, setCustomDomain] = useState(false);

  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

  async function loadModels() {
    try {
      const response = await fetch(`${baseUrl}/api/request-models`);
      if (response.ok) {
        const data = await response.json();
        setModels(data.items);
      }
    } catch (error) {
      console.error("Failed to load models:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadModels();
  }, []);

  function handleNew() {
    setEditingId(null);
    setCustomDomain(false);
    setFormData({
      model_id: "",
      name: "",
      description: "",
      domain: "",
      default_risk_level: "medium",
      default_title: "",
      placeholder_request_text: "",
      placeholder_context: "",
      human_review_required: false,
    });
    setShowForm(true);
  }

  function handleEdit(model: RequestModel) {
    setEditingId(model.model_id);
    const isPreset = PRESET_DOMAINS.some((d) => d.value === model.domain);
    setCustomDomain(!isPreset);
    setFormData({
      model_id: model.model_id,
      name: model.name,
      description: model.description,
      domain: model.domain,
      default_risk_level: model.default_risk_level,
      default_title: model.default_title,
      placeholder_request_text: model.placeholder_request_text,
      placeholder_context: model.placeholder_context,
      human_review_required: model.human_review_required,
    });
    setShowForm(true);
  }

  function handleCancel() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const url = editingId
        ? `${baseUrl}/api/request-models/${editingId}`
        : `${baseUrl}/api/request-models`;
      const method = editingId ? "PUT" : "POST";

      const payload = editingId
        ? {
            name: formData.name,
            description: formData.description,
            domain: formData.domain,
            default_risk_level: formData.default_risk_level,
            default_title: formData.default_title,
            placeholder_request_text: formData.placeholder_request_text,
            placeholder_context: formData.placeholder_context,
            human_review_required: formData.human_review_required,
          }
        : formData;

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        await loadModels();
        setShowForm(false);
        setEditingId(null);
      } else {
        const error = await response.json();
        alert("保存失败：" + JSON.stringify(error));
      }
    } catch (error) {
      console.error("Failed to save model:", error);
      alert("保存失败：" + error);
    }
  }

  async function handleDelete(modelId: string) {
    if (!confirm("确定删除此请求模型？")) return;

    try {
      const response = await fetch(`${baseUrl}/api/request-models/${modelId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadModels();
      }
    } catch (error) {
      console.error("Failed to delete model:", error);
    }
  }

  const riskLabel: Record<string, string> = {
    low: "低风险",
    medium: "中风险",
    high: "高风险",
  };

  const riskClass: Record<string, string> = {
    low: "allow",
    medium: "defer",
    high: "stop",
  };

  if (loading) {
    return <p className="muted">加载中...</p>;
  }

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">请求模型（{models.length}）</h2>
        <button className="button primary" onClick={handleNew}>
          新增模型
        </button>
      </div>

      {showForm && (
        <article className="card" style={{ marginBottom: 16 }}>
          <h3>{editingId ? "编辑模型" : "新增模型"}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row-2">
              <label>
                Model ID（小写字母、数字、下划线、短横线）
                <input
                  type="text"
                  value={formData.model_id}
                  onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                  placeholder="finance_approval"
                  pattern="^[a-z0-9_\-]+$"
                  disabled={!!editingId}
                  required
                />
              </label>
              <label>
                名称
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="财务审批"
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                描述
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="用于财务相关的审批决策"
                  required
                />
              </label>
            </div>

            <div className="form-row-2">
              <label>
                领域 (domain)
                {customDomain ? (
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      type="text"
                      value={formData.domain}
                      onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                      placeholder="my-custom-domain"
                      required
                      style={{ flex: 1 }}
                    />
                    <button
                      type="button"
                      className="button secondary"
                      style={{ whiteSpace: "nowrap" }}
                      onClick={() => {
                        setCustomDomain(false);
                        setFormData({ ...formData, domain: PRESET_DOMAINS[0].value });
                      }}
                    >
                      选预设
                    </button>
                  </div>
                ) : (
                  <div style={{ display: "flex", gap: 8 }}>
                    <select
                      value={formData.domain}
                      onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                      required
                      style={{ flex: 1 }}
                    >
                      <option value="" disabled>请选择领域</option>
                      {PRESET_DOMAINS.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}（{d.value}）
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      className="button secondary"
                      style={{ whiteSpace: "nowrap" }}
                      onClick={() => {
                        setCustomDomain(true);
                        setFormData({ ...formData, domain: "" });
                      }}
                    >
                      自定义
                    </button>
                  </div>
                )}
              </label>
              <label>
                默认风险等级
                <select
                  value={formData.default_risk_level}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      default_risk_level: e.target.value as "low" | "medium" | "high",
                    })
                  }
                  required
                >
                  <option value="low">低风险</option>
                  <option value="medium">中风险</option>
                  <option value="high">高风险</option>
                </select>
              </label>
            </div>

            <div className="form-row">
              <label>
                默认标题
                <input
                  type="text"
                  value={formData.default_title}
                  onChange={(e) => setFormData({ ...formData, default_title: e.target.value })}
                  placeholder="财务审批请求"
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                请求文本占位符
                <textarea
                  value={formData.placeholder_request_text}
                  onChange={(e) =>
                    setFormData({ ...formData, placeholder_request_text: e.target.value })
                  }
                  rows={3}
                  placeholder="请描述你的审批请求..."
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                上下文占位符
                <textarea
                  value={formData.placeholder_context}
                  onChange={(e) =>
                    setFormData({ ...formData, placeholder_context: e.target.value })
                  }
                  rows={2}
                  placeholder="补充相关背景信息..."
                />
              </label>
            </div>

            <div className="form-row">
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={formData.human_review_required}
                  onChange={(e) =>
                    setFormData({ ...formData, human_review_required: e.target.checked })
                  }
                />
                强制人工审核
              </label>
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button type="submit" className="button primary">
                保存
              </button>
              <button type="button" className="button secondary" onClick={handleCancel}>
                取消
              </button>
            </div>
          </form>
        </article>
      )}

      {models.length === 0 ? (
        <p className="muted">还没有配置请求模型。</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {models.map((model) => (
            <div key={model.model_id} className="provider-card">
              <div className="provider-card-top">
                <div>
                  <h3 style={{ margin: 0 }}>{model.name}</h3>
                  <div className="provider-card-info">
                    <span className="pill">{model.domain}</span>
                    <span className={`pill ${riskClass[model.default_risk_level]}`}>
                      {riskLabel[model.default_risk_level]}
                    </span>
                    {model.human_review_required && (
                      <span className="pill defer">需人工审核</span>
                    )}
                  </div>
                  <p className="muted" style={{ margin: "4px 0 0", fontSize: 13 }}>
                    {model.description}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="button secondary" onClick={() => handleEdit(model)}>
                    编辑
                  </button>
                  <button className="button secondary" onClick={() => handleDelete(model.model_id)}>
                    删除
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
