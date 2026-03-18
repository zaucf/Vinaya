async function getDemoReport() {
  const baseUrl =
    process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/demo`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch Vinaya demo report from Python API");
  }

  return response.json();
}

export default async function DemoPage() {
  const sampleReport = await getDemoReport();

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Demo</div>
          <h1>判断净化报告示例</h1>
          <p className="muted">
            该页面当前直接从 Python FastAPI 服务读取示例报告，用来验证前端与
            Python 引擎链路。
          </p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <section className="grid two">
        <article className="card">
          <h2>请求</h2>
          <p>
            <strong>{sampleReport.request.title}</strong>
          </p>
          <p className="muted">{sampleReport.request.requestText}</p>
          <p className="muted">风险等级：{sampleReport.request.riskLevel}</p>
        </article>

        <article className="card">
          <h2>最终结论</h2>
          <span className={`pill ${sampleReport.decision}`}>
            {sampleReport.decision}
          </span>
          <p className="muted" style={{ marginTop: 12 }}>
            {sampleReport.reasoningSummary}
          </p>
        </article>
      </section>

      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2>发心</h2>
          <ul className="list">
            <li>主要目标：{sampleReport.intention.primaryIntent}</li>
            <li>受益者：{sampleReport.intention.beneficiaries.join("、")}</li>
            <li>代价承担者：{sampleReport.intention.costBearers.join("、")}</li>
          </ul>
        </article>

        <article className="card">
          <h2>观缘</h2>
          <ul className="list">
            {sampleReport.causality.externalities.map((item: string) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>持戒</h2>
          <ul className="list">
            {sampleReport.precepts.preceptFindings.map(
              (item: { name: string; reason: string }) => (
                <li key={item.name}>
                  {item.name}：{item.reason}
                </li>
              )
            )}
          </ul>
        </article>

        <article className="card">
          <h2>缓行方案</h2>
          {sampleReport.gradualRelease.trialPlan ? (
            <ul className="list">
              <li>动作：{sampleReport.gradualRelease.trialPlan.action}</li>
              <li>范围：{sampleReport.gradualRelease.trialPlan.scope}</li>
              <li>
                回退条件：
                {sampleReport.gradualRelease.trialPlan.rollbackCondition}
              </li>
            </ul>
          ) : (
            <p className="muted">当前无需缓行计划。</p>
          )}
        </article>
      </section>
    </main>
  );
}
