async function getRequestReport(requestId: string) {
  const baseUrl =
    process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests/${requestId}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to fetch Vinaya ledger data from Python API");
  }

  return response.json();
}

function RiskPill({ level }: { level: string }) {
  const cls = level === "high" ? "stop" : level === "medium" ? "defer" : "allow";
  return <span className={`pill ${cls}`}>{level}</span>;
}

export default async function LedgerPage({
  params,
}: {
  params: Promise<{ requestId: string }>;
}) {
  const { requestId } = await params;

  let data;
  try {
    data = await getRequestReport(requestId);
  } catch {
    return (
      <main>
        <div className="card">
          <h1>因果簿暂时不可用</h1>
          <p className="muted">无法从 API 读取数据，请稍后重试。</p>
          <p style={{ marginTop: 16 }}>
            <a href="/requests">返回历史请求</a>
          </p>
        </div>
      </main>
    );
  }

  if (data === null) {
    return (
      <main>
        <div className="card">
          <h1>因果簿不存在</h1>
          <p className="muted">没有找到对应请求的因果记录。</p>
          <p style={{ marginTop: 16 }}>
            <a href="/requests">返回历史请求</a>
          </p>
        </div>
      </main>
    );
  }

  const report = data.report;

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Ledger · 因果簿</div>
          <h1>{report.request.title}</h1>
          <p className="muted">请求编号：{data.request_id}</p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href={`/requests/${requestId}`}>
            返回详情
          </a>
          <a className="button secondary" href="/requests">
            历史请求
          </a>
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      {/* 原始请求 */}
      <section className="grid two">
        <article className="card">
          <h2>原始请求</h2>
          <ul className="list">
            <li>标题：{report.request.title}</li>
            <li>内容：{report.request.requestText}</li>
            <li>领域：{report.request.domain}</li>
            <li>风险等级：{report.request.riskLevel}</li>
            {report.request.context ? (
              <li>补充上下文：{report.request.context}</li>
            ) : null}
          </ul>
        </article>

        <article className="card">
          <h2>最终判定</h2>
          <span className={`pill ${report.decision}`}>{report.decision}</span>
          <p className="muted" style={{ marginTop: 12 }}>
            {report.reasoningSummary}
          </p>
        </article>
      </section>

      {/* 发心分析 */}
      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2>
            发心分析 <RiskPill level={report.intention.intentionRisk} />
          </h2>
          <ul className="list">
            <li>
              <strong>主要目标</strong>：{report.intention.primaryIntent}
            </li>
            <li>
              <strong>混杂动机</strong>：
              {report.intention.mixedMotives.length > 0
                ? report.intention.mixedMotives.join("、")
                : "无"}
            </li>
            <li>
              <strong>受益者</strong>：{report.intention.beneficiaries.join("、")}
            </li>
            <li>
              <strong>代价承担者</strong>：{report.intention.costBearers.join("、")}
            </li>
          </ul>
        </article>

        {/* 观缘分析 */}
        <article className="card">
          <h2>
            观缘分析 <RiskPill level={report.causality.causalityRisk} />
          </h2>
          <ul className="list">
            <li>
              <strong>近因</strong>：{report.causality.proximateCauses.join("、")}
            </li>
            <li>
              <strong>远因</strong>：{report.causality.rootCauses.join("、")}
            </li>
            <li>
              <strong>影响对象</strong>：{report.causality.affectedParties.join("、")}
            </li>
            <li>
              <strong>外溢后果</strong>：
              {report.causality.externalities.map((item: string) => (
                <span key={item} style={{ display: "block", marginTop: 4 }}>
                  · {item}
                </span>
              ))}
            </li>
          </ul>
        </article>
      </section>

      {/* 持戒检查 */}
      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2>
            持戒检查 <RiskPill level={report.precepts.preceptRisk} />
          </h2>
          {report.precepts.hardBlock ? (
            <p className="error-text" style={{ marginBottom: 12 }}>
              触发硬性止行
            </p>
          ) : null}
          {report.precepts.humanReviewRequired ? (
            <p style={{ color: "var(--warn)", marginBottom: 12 }}>
              建议人工复核
            </p>
          ) : null}
          <div className="table-like">
            {report.precepts.preceptFindings.map(
              (item: { name: string; status: string; reason: string }) => (
                <div key={item.name} className="review-row">
                  <div className="review-row-header">
                    <strong>{item.name}</strong>
                    <span
                      className={`pill ${
                        item.status === "block"
                          ? "stop"
                          : item.status === "warning"
                          ? "defer"
                          : "allow"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>
                  <p className="muted" style={{ margin: "8px 0 0" }}>
                    {item.reason}
                  </p>
                </div>
              )
            )}
          </div>
        </article>

        {/* 辩义分析 */}
        <article className="card">
          <h2>
            辩义分析 <RiskPill level={report.deliberation.deliberationRisk} />
          </h2>
          <p className="muted" style={{ marginBottom: 12 }}>
            推荐方案：<strong>{report.deliberation.preferredOption}</strong>
          </p>
          <div className="table-like">
            {report.deliberation.options.map(
              (option: { name: string; score: number }) => (
                <div key={option.name} className="review-row">
                  <div className="review-row-header">
                    <span>{option.name}</span>
                    <span className="pill">
                      {(option.score * 100).toFixed(0)}分
                    </span>
                  </div>
                </div>
              )
            )}
          </div>
          {report.deliberation.dissentNotes.length > 0 ? (
            <div style={{ marginTop: 12 }}>
              <p className="muted">
                <strong>分歧记录：</strong>
              </p>
              <ul className="list">
                {report.deliberation.dissentNotes.map((note: string) => (
                  <li key={note} className="muted">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </article>
      </section>

      {/* 缓行方案 */}
      <section className="grid" style={{ marginTop: 16 }}>
        <article className="card">
          <h2>
            缓行方案 <RiskPill level={report.gradualRelease.releaseRisk} />
          </h2>
          <p className="muted">
            模式：<span className={`pill ${report.gradualRelease.mode}`}>{report.gradualRelease.mode}</span>
          </p>
          {report.gradualRelease.trialPlan ? (
            <ul className="list" style={{ marginTop: 12 }}>
              <li>
                <strong>执行动作</strong>：{report.gradualRelease.trialPlan.action}
              </li>
              <li>
                <strong>适用范围</strong>：{report.gradualRelease.trialPlan.scope}
              </li>
              <li>
                <strong>复核时间</strong>：{report.gradualRelease.trialPlan.reviewAt}
              </li>
              <li>
                <strong>回退条件</strong>：{report.gradualRelease.trialPlan.rollbackCondition}
              </li>
              <li>
                <strong>人工负责人</strong>：{report.gradualRelease.trialPlan.humanOwner}
              </li>
            </ul>
          ) : (
            <p className="muted" style={{ marginTop: 12 }}>
              当前无需缓行计划。
            </p>
          )}
        </article>
      </section>

      {/* 回向 */}
      {report.dedication && (
        <section className="grid" style={{ marginTop: 16 }}>
          <article className="card">
            <h2>
              回向 <RiskPill level={report.dedication.dedicationRisk} />
            </h2>
            {report.dedication.lessonsLearned && report.dedication.lessonsLearned.length > 0 && (
              <>
                <h3 style={{ fontSize: 14, marginBottom: 8 }}>经验教训</h3>
                <ul className="list">
                  {report.dedication.lessonsLearned.map((item: string) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}
            {report.dedication.followUpActions && report.dedication.followUpActions.length > 0 && (
              <>
                <h3 style={{ fontSize: 14, marginTop: 12, marginBottom: 8 }}>后续跟踪</h3>
                <ul className="list">
                  {report.dedication.followUpActions.map((item: string) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </>
            )}
            {report.dedication.meritDedication && (
              <p className="muted" style={{ marginTop: 12 }}>
                <strong>功德回向：</strong>{report.dedication.meritDedication}
              </p>
            )}
          </article>
        </section>
      )}
    </main>
  );
}
