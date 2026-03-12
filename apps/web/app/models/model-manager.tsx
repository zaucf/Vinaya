"use client";

import { useMemo, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

type RiskLevel = "low" | "medium" | "high";

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

type LLMProvider = {
  provider_id: string;
  name: string;
  provider_type: "openai-compatible";
  base_url: string;
  model: string;
  api_key_env: string;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
  is_default: boolean;
  system_prompt: string;
};

const emptyRequestModelForm = {
  modelId: "",
  name: "",
  description: "",
  domain: "",
  defaultRiskLevel: "medium" as RiskLevel,
  defaultTitle: "",
  requestPlaceholder: "",
  contextPlaceholder: "",
  humanReviewRequired: true,
};

const emptyProviderForm = {
  providerId: "",
  name: "",
  providerType: "openai-compatible" as const,
  baseUrl: "https://api.openai.com/v1/chat/completions",
  model: "gpt-4o-mini",
  apiKeyEnv: "OPENAI_API_KEY",
  temperature: "0.2",
  timeoutSeconds: "60",
  enabled: true,
  isDefault: false,
  systemPrompt:
    "你是 Vinaya 判断净化引擎。你必须基于输入请求，输出严格 JSON，不要输出 Markdown。",
};

export function ModelManager({
  initialItems,
  initialProviders,
}: {
  initialItems: RequestModel[];
  initialProviders: LLMProvider[];
}) {
  const [items, setItems] = useState<RequestModel[]>(initialItems);
  const [providers, setProviders] = useState<LLMProvider[]>(initialProviders);

  const [modelId, setModelId] = useState(emptyRequestModelForm.modelId);
  const [name, setName] = useState(emptyRequestModelForm.name);
  const [description, setDescription] = useState(
    emptyRequestModelForm.description
  );
  const [domain, setDomain] = useState(emptyRequestModelForm.domain);
  const [defaultRiskLevel, setDefaultRiskLevel] = useState<RiskLevel>(
    emptyRequestModelForm.defaultRiskLevel
  );
  const [defaultTitle, setDefaultTitle] = useState(
    emptyRequestModelForm.defaultTitle
  );
  const [requestPlaceholder, setRequestPlaceholder] = useState(
    emptyRequestModelForm.requestPlaceholder
  );
  const [contextPlaceholder, setContextPlaceholder] = useState(
    emptyRequestModelForm.contextPlaceholder
  );
  const [humanReviewRequired, setHumanReviewRequired] = useState(
    emptyRequestModelForm.humanReviewRequired
  );
  const [editingModelId, setEditingModelId] = useState<string | null>(null);

  const [providerId, setProviderId] = useState(emptyProviderForm.providerId);
  const [providerName, setProviderName] = useState(emptyProviderForm.name);
  const [providerType, setProviderType] = useState(
    emptyProviderForm.providerType
  );
  const [baseUrl, setBaseUrl] = useState(emptyProviderForm.baseUrl);
  const [providerModel, setProviderModel] = useState(emptyProviderForm.model);
  const [apiKeyEnv, setApiKeyEnv] = useState(emptyProviderForm.apiKeyEnv);
  const [temperature, setTemperature] = useState(emptyProviderForm.temperature);
  const [timeoutSeconds, setTimeoutSeconds] = useState(
    emptyProviderForm.timeoutSeconds
  );
  const [enabled, setEnabled] = useState(emptyProviderForm.enabled);
  const [isDefault, setIsDefault] = useState(emptyProviderForm.isDefault);
  const [systemPrompt, setSystemPrompt] = useState(
    emptyProviderForm.systemPrompt
  );
  const [editingProviderId, setEditingProviderId] = useState<string | null>(
    null
  );

  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [providerDeletingId, setProviderDeletingId] = useState<string | null>(
    null
  );
  const [providerTestingId, setProviderTestingId] = useState<string | null>(
    null
  );
  const [providerTestResult, setProviderTestResult] = useState<string | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);

  const sortedItems = useMemo(
    () =>
      [...items].sort((left, right) =>
        left.model_id.localeCompare(right.model_id)
      ),
    [items]
  );

  const sortedProviders = useMemo(
    () =>
      [...providers].sort((left, right) =>
        left.provider_id.localeCompare(right.provider_id)
      ),
    [providers]
  );

  function resetRequestModelForm() {
    setModelId(emptyRequestModelForm.modelId);
    setName(emptyRequestModelForm.name);
    setDescription(emptyRequestModelForm.description);
    setDomain(emptyRequestModelForm.domain);
    setDefaultRiskLevel(emptyRequestModelForm.defaultRiskLevel);
    setDefaultTitle(emptyRequestModelForm.defaultTitle);
    setRequestPlaceholder(emptyRequestModelForm.requestPlaceholder);
    setContextPlaceholder(emptyRequestModelForm.contextPlaceholder);
    setHumanReviewRequired(emptyRequestModelForm.humanReviewRequired);
    setEditingModelId(null);
  }

  function resetProviderForm() {
    setProviderId(emptyProviderForm.providerId);
    setProviderName(emptyProviderForm.name);
    setProviderType(emptyProviderForm.providerType);
    setBaseUrl(emptyProviderForm.baseUrl);
    setProviderModel(emptyProviderForm.model);
    setApiKeyEnv(emptyProviderForm.apiKeyEnv);
    setTemperature(emptyProviderForm.temperature);
    setTimeoutSeconds(emptyProviderForm.timeoutSeconds);
    setEnabled(emptyProviderForm.enabled);
    setIsDefault(emptyProviderForm.isDefault);
    setSystemPrompt(emptyProviderForm.systemPrompt);
    setEditingProviderId(null);
  }

  async function handleRequestModelSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      name,
      description,
      domain,
      default_risk_level: defaultRiskLevel,
      default_title: defaultTitle,
      placeholder_request_text: requestPlaceholder,
      placeholder_context: contextPlaceholder,
      human_review_required: humanReviewRequired,
    };

    try {
      const isEditing = editingModelId !== null;
      const endpoint = isEditing
        ? `${apiBaseUrl}/api/request-models/${editingModelId}`
        : `${apiBaseUrl}/api/request-models`;
      const response = await fetch(endpoint, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          isEditing
            ? payload
            : {
                model_id: modelId,
                ...payload,
              }
        ),
      });

      if (!response.ok) {
        const detail = await response
          .json()
          .catch(() => ({ detail: "请求模型保存失败" }));
        throw new Error(detail.detail ?? "请求模型保存失败");
      }

      const saved = (await response.json()) as RequestModel;
      setItems((current) => {
        const exists = current.some((item) => item.model_id === saved.model_id);
        return exists
          ? current.map((item) =>
              item.model_id === saved.model_id ? saved : item
            )
          : [...current, saved];
      });
      resetRequestModelForm();
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : "请求模型保存失败"
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleProviderSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload = {
      name: providerName,
      provider_type: providerType,
      base_url: baseUrl,
      model: providerModel,
      api_key_env: apiKeyEnv,
      temperature: Number(temperature),
      timeout_seconds: Number(timeoutSeconds),
      enabled,
      is_default: isDefault,
      system_prompt: systemPrompt,
    };

    try {
      const isEditing = editingProviderId !== null;
      const endpoint = isEditing
        ? `${apiBaseUrl}/api/llm-providers/${editingProviderId}`
        : `${apiBaseUrl}/api/llm-providers`;
      const response = await fetch(endpoint, {
        method: isEditing ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          isEditing
            ? payload
            : {
                provider_id: providerId,
                ...payload,
              }
        ),
      });

      if (!response.ok) {
        const detail = await response
          .json()
          .catch(() => ({ detail: "LLM 提供商保存失败" }));
        throw new Error(detail.detail ?? "LLM 提供商保存失败");
      }

      const saved = (await response.json()) as LLMProvider;
      setProviders((current) => {
        const merged = current.some(
          (item) => item.provider_id === saved.provider_id
        )
          ? current.map((item) =>
              item.provider_id === saved.provider_id ? saved : item
            )
          : [...current, saved];
        return saved.is_default
          ? merged.map((item) =>
              item.provider_id === saved.provider_id
                ? saved
                : { ...item, is_default: false }
            )
          : merged;
      });
      resetProviderForm();
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "LLM 提供商保存失败"
      );
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(item: RequestModel) {
    setEditingModelId(item.model_id);
    setModelId(item.model_id);
    setName(item.name);
    setDescription(item.description);
    setDomain(item.domain);
    setDefaultRiskLevel(item.default_risk_level);
    setDefaultTitle(item.default_title);
    setRequestPlaceholder(item.placeholder_request_text);
    setContextPlaceholder(item.placeholder_context);
    setHumanReviewRequired(item.human_review_required);
    setError(null);
  }

  function startProviderEdit(item: LLMProvider) {
    setEditingProviderId(item.provider_id);
    setProviderId(item.provider_id);
    setProviderName(item.name);
    setProviderType(item.provider_type);
    setBaseUrl(item.base_url);
    setProviderModel(item.model);
    setApiKeyEnv(item.api_key_env);
    setTemperature(String(item.temperature));
    setTimeoutSeconds(String(item.timeout_seconds));
    setEnabled(item.enabled);
    setIsDefault(item.is_default);
    setSystemPrompt(item.system_prompt);
    setProviderTestResult(null);
    setError(null);
  }

  async function handleProviderTest(providerIdToTest: string) {
    setProviderTestingId(providerIdToTest);
    setProviderTestResult(null);
    setError(null);

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/llm-providers/${providerIdToTest}/test`,
        {
          method: "POST",
        }
      );
      const detail = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(detail?.detail ?? "LLM 提供商测试失败");
      }

      setProviderTestResult(
        detail?.message ?? "连接测试已完成，但未返回详细信息。"
      );
    } catch (testError) {
      setError(
        testError instanceof Error ? testError.message : "LLM 提供商测试失败"
      );
    } finally {
      setProviderTestingId(null);
    }
  }

  async function handleDelete(modelIdToDelete: string) {
    setError(null);

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/request-models/${modelIdToDelete}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const detail = await response
          .json()
          .catch(() => ({ detail: "请求模型删除失败" }));
        throw new Error(detail.detail ?? "请求模型删除失败");
      }

      setItems((current) =>
        current.filter((item) => item.model_id !== modelIdToDelete)
      );
      if (editingModelId === modelIdToDelete) {
        resetRequestModelForm();
      }
    } catch (deleteError) {
      setError(
        deleteError instanceof Error ? deleteError.message : "请求模型删除失败"
      );
    } finally {
      setDeletingId(null);
    }
  }

  async function handleProviderDelete(providerIdToDelete: string) {
    setProviderDeletingId(providerIdToDelete);
    setError(null);

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/llm-providers/${providerIdToDelete}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const detail = await response
          .json()
          .catch(() => ({ detail: "LLM 提供商删除失败" }));
        throw new Error(detail.detail ?? "LLM 提供商删除失败");
      }

      setProviders((current) =>
        current.filter((item) => item.provider_id !== providerIdToDelete)
      );
      if (editingProviderId === providerIdToDelete) {
        resetProviderForm();
      }
    } catch (deleteError) {
      setError(
        deleteError instanceof Error
          ? deleteError.message
          : "LLM 提供商删除失败"
      );
    } finally {
      setProviderDeletingId(null);
    }
  }

  return (
    <>
      <form className="card form" onSubmit={handleRequestModelSubmit}>
        <h2 className="section-title">
          {editingModelId ? "编辑请求模型" : "新增请求模型"}
        </h2>
        <label className="field">
          <span>模型 ID</span>
          <input
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
            placeholder="例如 risk_screen_v1"
            required
            disabled={editingModelId !== null}
          />
        </label>
        <label className="field">
          <span>模型名称</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>描述</span>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            rows={3}
            required
          />
        </label>
        <label className="field">
          <span>领域</span>
          <input
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>默认风险</span>
          <select
            value={defaultRiskLevel}
            onChange={(event) =>
              setDefaultRiskLevel(event.target.value as RiskLevel)
            }
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>
        <label className="field">
          <span>默认标题</span>
          <input
            value={defaultTitle}
            onChange={(event) => setDefaultTitle(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>请求内容提示</span>
          <textarea
            value={requestPlaceholder}
            onChange={(event) => setRequestPlaceholder(event.target.value)}
            rows={4}
            required
          />
        </label>
        <label className="field">
          <span>上下文提示</span>
          <textarea
            value={contextPlaceholder}
            onChange={(event) => setContextPlaceholder(event.target.value)}
            rows={4}
          />
        </label>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={humanReviewRequired}
            onChange={(event) => setHumanReviewRequired(event.target.checked)}
          />
          <span>默认要求人工复核</span>
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="action-row">
          <button className="button" type="submit" disabled={submitting}>
            {submitting
              ? "保存中..."
              : editingModelId
              ? "保存修改"
              : "创建请求模型"}
          </button>
          {editingModelId ? (
            <button
              className="button secondary"
              type="button"
              onClick={resetRequestModelForm}
            >
              取消编辑
            </button>
          ) : null}
        </div>
      </form>

      <form className="card form" onSubmit={handleProviderSubmit}>
        <h2 className="section-title">
          {editingProviderId ? "编辑 LLM 提供商" : "新增 LLM 提供商"}
        </h2>
        <label className="field">
          <span>Provider ID</span>
          <input
            value={providerId}
            onChange={(event) => setProviderId(event.target.value)}
            placeholder="例如 default_openai"
            required
            disabled={editingProviderId !== null}
          />
        </label>
        <label className="field">
          <span>名称</span>
          <input
            value={providerName}
            onChange={(event) => setProviderName(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>类型</span>
          <select
            value={providerType}
            onChange={(event) =>
              setProviderType(event.target.value as "openai-compatible")
            }
          >
            <option value="openai-compatible">openai-compatible</option>
          </select>
        </label>
        <label className="field">
          <span>Base URL</span>
          <input
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>模型名</span>
          <input
            value={providerModel}
            onChange={(event) => setProviderModel(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>API Key 环境变量名</span>
          <input
            value={apiKeyEnv}
            onChange={(event) => setApiKeyEnv(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Temperature</span>
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={temperature}
            onChange={(event) => setTemperature(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>超时秒数</span>
          <input
            type="number"
            min="1"
            max="600"
            value={timeoutSeconds}
            onChange={(event) => setTimeoutSeconds(event.target.value)}
            required
          />
        </label>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => setEnabled(event.target.checked)}
          />
          <span>启用该提供商</span>
        </label>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={isDefault}
            onChange={(event) => setIsDefault(event.target.checked)}
          />
          <span>设为默认提供商</span>
        </label>
        <label className="field">
          <span>系统提示词</span>
          <textarea
            value={systemPrompt}
            onChange={(event) => setSystemPrompt(event.target.value)}
            rows={8}
            required
          />
        </label>
        {error ? <p className="error-text">{error}</p> : null}
        {providerTestResult ? (
          <p className="muted">最近测试结果：{providerTestResult}</p>
        ) : null}
        <div className="action-row">
          <button className="button" type="submit" disabled={submitting}>
            {submitting
              ? "保存中..."
              : editingProviderId
              ? "保存修改"
              : "创建 LLM 提供商"}
          </button>
          {editingProviderId ? (
            <button
              className="button secondary"
              type="button"
              onClick={resetProviderForm}
            >
              取消编辑
            </button>
          ) : null}
        </div>
      </form>

      <article className="card">
        <h2 className="section-title">已配置请求模型</h2>
        <div className="table-like">
          {sortedItems.map((item) => (
            <div className="model-row" key={item.model_id}>
              <div>
                <strong>{item.name}</strong>
                <p className="muted">{item.model_id}</p>
                <p className="muted">{item.description}</p>
              </div>
              <div className="model-actions">
                <div>
                  <span className="pill">{item.domain}</span>
                  <span className="pill">{item.default_risk_level}</span>
                  <span className="pill">
                    {item.human_review_required ? "人工复核" : "可先试行"}
                  </span>
                </div>
                <div className="action-row">
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => startEdit(item)}
                  >
                    编辑
                  </button>
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => handleDelete(item.model_id)}
                    disabled={deletingId === item.model_id}
                  >
                    {deletingId === item.model_id ? "删除中..." : "删除"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="card">
        <h2 className="section-title">已配置 LLM 提供商</h2>
        <div className="table-like">
          {sortedProviders.map((item) => (
            <div className="model-row" key={item.provider_id}>
              <div>
                <strong>{item.name}</strong>
                <p className="muted">{item.provider_id}</p>
                <p className="muted">{item.base_url}</p>
                <p className="muted">
                  model={item.model} · env={item.api_key_env}
                </p>
              </div>
              <div className="model-actions">
                <div>
                  <span className="pill">{item.provider_type}</span>
                  <span className="pill">temp {item.temperature}</span>
                  <span className="pill">timeout {item.timeout_seconds}s</span>
                  <span className="pill">{item.enabled ? "启用" : "停用"}</span>
                  {item.is_default ? <span className="pill">默认</span> : null}
                </div>
                <div className="action-row">
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => startProviderEdit(item)}
                  >
                    编辑
                  </button>
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => handleProviderTest(item.provider_id)}
                    disabled={providerTestingId === item.provider_id}
                  >
                    {providerTestingId === item.provider_id
                      ? "测试中..."
                      : "测试连接"}
                  </button>
                  <button
                    className="button secondary"
                    type="button"
                    onClick={() => handleProviderDelete(item.provider_id)}
                    disabled={
                      providerDeletingId === item.provider_id || item.is_default
                    }
                  >
                    {providerDeletingId === item.provider_id
                      ? "删除中..."
                      : "删除"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </article>
    </>
  );
}
