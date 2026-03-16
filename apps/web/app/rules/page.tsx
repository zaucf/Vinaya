import { RulesManager } from "./rules-manager";

async function getRulesConfig() {
  const baseUrl =
    process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/rules`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch rules config from Python API");
  }

  return response.json();
}

export default async function RulesPage() {
  let config;
  try {
    config = await getRulesConfig();
  } catch {
    return (
      <main>
        <div className="card">
          <h1>规则中心暂时不可用</h1>
          <p className="muted">
            无法从 API 读取规则配置，请确认 Python API 已启动。
          </p>
        </div>
      </main>
    );
  }

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Rules</div>
          <h1>规则与策略配置中心</h1>
          <p className="muted">
            管理五戒规则、缓行策略和风险阈值配置。修改后对后续判断生效。
          </p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <RulesManager initialConfig={config} />
    </main>
  );
}
