import { ModelManager } from "./model-manager";

async function getConfigCenterData() {
  const baseUrl =
    process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const [requestModelsResponse, llmProvidersResponse] = await Promise.all([
    fetch(`${baseUrl}/api/request-models`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/llm-providers`, { cache: "no-store" }),
  ]);

  if (!requestModelsResponse.ok) {
    throw new Error("Failed to fetch Vinaya request models from Python API");
  }

  if (!llmProvidersResponse.ok) {
    throw new Error("Failed to fetch Vinaya LLM providers from Python API");
  }

  const requestModels = await requestModelsResponse.json();
  const llmProviders = await llmProvidersResponse.json();

  return {
    requestModels,
    llmProviders,
  };
}

export default async function RequestModelsPage() {
  const data = await getConfigCenterData();

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Models</div>
          <h1>请求模型与引擎配置中心</h1>
          <p className="muted">
            这里同时管理请求模型模板与 LLM 提供商配置，可切换实际调用的
            provider、base URL 与 model。
          </p>
        </div>
      </div>

      <section className="grid two">
        <ModelManager
          initialItems={data.requestModels.items}
          initialProviders={data.llmProviders.items}
        />
      </section>
    </main>
  );
}
