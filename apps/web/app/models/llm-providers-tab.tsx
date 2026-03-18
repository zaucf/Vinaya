"use client";

import { useEffect, useState } from "react";

type LLMProvider = {
  provider_id: string;
  name: string;
  provider_type: "openai-compatible";
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
  timeout_seconds: number;
  system_prompt: string;
  is_default: boolean;
  enabled: boolean;
};

export function LLMProvidersTab() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showModelsDialog, setShowModelsDialog] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    message: string;
    models?: string[];
  } | null>(null);
  const [formData, setFormData] = useState({
    provider_id: "",
    name: "",
    provider_type: "openai-compatible" as const,
    base_url: "",
    api_key: "",
    model: "",
    temperature: 0.7,
    timeout_seconds: 60,
    system_prompt: "",
    is_default: false,
    enabled: true,
  });

  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

  async function loadProviders() {
    try {
      const response = await fetch(`${baseUrl}/api/llm-providers`);
      if (response.ok) {
        const data = await response.json();
        setProviders(data.items);
      }
    } catch (error) {
      console.error("Failed to load providers:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProviders();
  }, []);

  function handleNew() {
    setEditingId(null);
    setFormData({
      provider_id: "",
      name: "",
      provider_type: "openai-compatible",
      base_url: "",
      api_key: "",
      model: "",
      temperature: 0.7,
      timeout_seconds: 60,
      system_prompt: "",
      is_default: false,
      enabled: true,
    });
    setShowForm(true);
  }

  function handleEdit(provider: LLMProvider) {
    setEditingId(provider.provider_id);
    setFormData({
      provider_id: provider.provider_id,
      name: provider.name,
      provider_type: "openai-compatible",
      base_url: provider.base_url,
      api_key: provider.api_key,
      model: provider.model,
      temperature: provider.temperature ?? 0.7,
      timeout_seconds: provider.timeout_seconds ?? 60,
      system_prompt: provider.system_prompt ?? "",
      is_default: provider.is_default,
      enabled: provider.enabled,
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
        ? `${baseUrl}/api/llm-providers/${editingId}`
        : `${baseUrl}/api/llm-providers`;
      const method = editingId ? "PUT" : "POST";

      // 编辑时排除 provider_id
      const payload = editingId
        ? {
            name: formData.name,
            provider_type: formData.provider_type,
            base_url: formData.base_url,
            model: formData.model,
            api_key: formData.api_key,
            temperature: formData.temperature,
            timeout_seconds: formData.timeout_seconds,
            system_prompt: formData.system_prompt,
            enabled: formData.enabled,
            is_default: formData.is_default,
          }
        : formData;

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        await loadProviders();
        setShowForm(false);
        setEditingId(null);
      } else {
        const error = await response.json();
        alert("保存失败：" + JSON.stringify(error));
      }
    } catch (error) {
      console.error("Failed to save provider:", error);
      alert("保存失败：" + error);
    }
  }

  async function handleDelete(providerId: string) {
    if (!confirm("确定删除此 LLM 提供商？")) return;

    try {
      const response = await fetch(`${baseUrl}/api/llm-providers/${providerId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadProviders();
      }
    } catch (error) {
      console.error("Failed to delete provider:", error);
    }
  }

  async function handleTest(providerId: string) {
    try {
      const response = await fetch(`${baseUrl}/api/llm-providers/${providerId}/test`, {
        method: "POST",
      });
      const result = await response.json();
      setTestResult(result);
      setShowModelsDialog(true);
    } catch (error) {
      setTestResult({
        ok: false,
        message: "测试失败：" + error,
      });
      setShowModelsDialog(true);
    }
  }

  if (loading) {
    return <p className="muted">加载中...</p>;
  }

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">LLM 提供商（{providers.length}）</h2>
        <button className="button primary" onClick={handleNew}>
          新增提供商
        </button>
      </div>

      {showModelsDialog && testResult && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowModelsDialog(false)}
        >
          <article
            className="card"
            style={{
              width: "90vw",
              maxWidth: 800,
              maxHeight: "80vh",
              overflow: "auto",
              margin: 16,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>{testResult.ok ? "✓ 连接成功" : "✗ 连接失败"}</h3>
            <p>{testResult.message}</p>
            {testResult.ok && testResult.models && testResult.models.length > 0 && (
              <div>
                <h4 style={{ marginTop: 16, marginBottom: 8 }}>可用模型：</h4>
                <div style={{ maxHeight: 400, overflow: "auto" }}>
                  {testResult.models.map((model, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "6px 12px",
                        margin: "4px 0",
                        backgroundColor: "#f0f0f0",
                        borderRadius: 4,
                        fontSize: 13,
                        fontFamily: "monospace",
                      }}
                    >
                      {model}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <button
              className="button primary"
              onClick={() => setShowModelsDialog(false)}
              style={{ marginTop: 16 }}
            >
              关闭
            </button>
          </article>
        </div>
      )}

      {showForm && (
        <article className="card" style={{ marginBottom: 16 }}>
          <h3>{editingId ? "编辑提供商" : "新增提供商"}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <label>
                Provider ID（小写字母、数字、下划线、短横线）
                <input
                  type="text"
                  value={formData.provider_id}
                  onChange={(e) => setFormData({ ...formData, provider_id: e.target.value })}
                  placeholder="my_provider"
                  pattern="^[a-z0-9_\-]+$"
                  disabled={!!editingId}
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                名称
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </label>
            </div>

            <div className="form-row-2">
              <label>
                Base URL
                <input
                  type="text"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                  required
                />
              </label>
              <label>
                Model
                <input
                  type="text"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  placeholder="gpt-4"
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                API Key
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder="sk-..."
                  required
                />
              </label>
            </div>

            <div className="form-row-2">
              <label>
                Temperature
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={formData.temperature}
                  onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                  required
                />
              </label>
              <label>
                Timeout (秒)
                <input
                  type="number"
                  min="1"
                  max="600"
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                System Prompt
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  rows={3}
                  placeholder="You are a helpful assistant."
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                />
                设为默认提供商
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
                启用
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

      {providers.length === 0 ? (
        <p className="muted">还没有配置 LLM 提供商。</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {providers.map((provider) => (
            <div
              key={provider.provider_id}
              className={`provider-card ${provider.is_default ? "is-default" : ""} ${
                !provider.enabled ? "is-disabled" : ""
              }`}
            >
              <div className="provider-card-top">
                <div>
                  <h3 style={{ margin: 0 }}>{provider.name}</h3>
                  <div className="provider-card-info">
                    <span className="pill">{provider.model}</span>
                    {provider.is_default && <span className="pill allow">默认</span>}
                    {!provider.enabled && <span className="pill stop">已禁用</span>}
                  </div>
                  <p className="muted" style={{ margin: "4px 0 0", fontSize: 13 }}>
                    {provider.base_url}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="button secondary" onClick={() => handleTest(provider.provider_id)}>
                    测试
                  </button>
                  <button className="button secondary" onClick={() => handleEdit(provider)}>
                    编辑
                  </button>
                  <button className="button secondary" onClick={() => handleDelete(provider.provider_id)}>
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
