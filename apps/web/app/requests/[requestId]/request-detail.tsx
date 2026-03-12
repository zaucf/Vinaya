import { ReviewForm } from "./review-form";

function mapReviewResultLabel(review: { result: string } | null) {
  if (!review) {
    return "未复核";
  }

  return {
    maintain: "已维持",
    revise: "已修改",
    override: "已推翻",
  }[review.result] ?? "已复核";
}

function buildReviewSummary(review: { result: string } | null) {
  if (!review) {
    return "当前仍以系统建议为准，尚未进入人工复核。";
  }

  return {
    maintain: "人工复核已维持系统建议，可按当前方案继续推进。",
    revise: "人工复核已修改系统建议，后续应以人工修正后的判断为准。",
    override: "人工复核已推翻系统建议，后续不得继续沿用原自动结论。",
  }[review.result] ?? "人工复核已完成，请以人工意见为准。";
}

async function getRequestReport(requestId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests/${requestId}`, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to fetch Vinaya request report from Python API");
  }

  return response.json();
}

async function getReview(requestId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests/${requestId}/review`, { cache: "no-store" });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to fetch review from Python API");
  }

  return response.json();
}

export async function RequestDetail({ requestId }: { requestId: string }) {
  try {
    const data = await getRequestReport(requestId);

    if (data === null) {
      return (
        <main>
          <div className="card">
            <h1>请求不存在</h1>
            <p className="muted">未找到该 request id 对应的判断报告。</p>
          </div>
        </main>
      );
    }

    const review = await getReview(requestId);
    const report = data.report;
    const reviewStatus = mapReviewResultLabel(review);
    const reviewSummary = buildReviewSummary(review);

    return (
      <main>
        <div className="header">
          <div>
            <div className="kicker">Vinaya Request</div>
            <h1>{report.request.title}</h1>
            <p className="muted">请求编号：{data.request_id}</p>
          </div>
        </div>

        <section className="grid two">
          <article className="card">
            <h2>请求内容</h2>
            <p className="muted">{report.request.requestText}</p>
            <p className="muted">领域：{report.request.domain}</p>
            <p className="muted">风险等级：{report.request.riskLevel}</p>
          </article>

          <article className="card">
            <h2>最终结论</h2>
            <span className={`pill ${report.decision}`}>{report.decision}</span>
            <span className="pill">{reviewStatus}</span>
            <p className="muted" style={{ marginTop: 12 }}>
              {report.reasoningSummary}
            </p>
            <p className="muted">{reviewSummary}</p>
          </article>
        </section>

        <section className="grid two" style={{ marginTop: 16 }}>
          <article className="card">
            <h2>发心</h2>
            <ul className="list">
              <li>主要目标：{report.intention.primaryIntent}</li>
              <li>混杂动机：{report.intention.mixedMotives.join("、")}</li>
              <li>受益者：{report.intention.beneficiaries.join("、")}</li>
              <li>代价承担者：{report.intention.costBearers.join("、")}</li>
            </ul>
          </article>

          <article className="card">
            <h2>观缘</h2>
            <ul className="list">
              {report.causality.externalities.map((item: string) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="card">
            <h2>持戒</h2>
            <ul className="list">
              {report.precepts.preceptFindings.map(
                (item: { name: string; reason: string }) => (
                  <li key={item.name}>{item.name}：{item.reason}</li>
                )
              )}
            </ul>
          </article>

          <article className="card">
            <h2>缓行方案</h2>
            {report.gradualRelease.trialPlan ? (
              <ul className="list">
                <li>动作：{report.gradualRelease.trialPlan.action}</li>
                <li>范围：{report.gradualRelease.trialPlan.scope}</li>
                <li>复核时间：{report.gradualRelease.trialPlan.reviewAt}</li>
                <li>回退条件：{report.gradualRelease.trialPlan.rollbackCondition}</li>
              </ul>
            ) : (
              <p className="muted">当前无需缓行计划。</p>
            )}
          </article>
        </section>

        <section className="grid two" style={{ marginTop: 16 }}>
          <ReviewForm requestId={requestId} />

          <article className="card">
            <h2 className="section-title">当前复核</h2>
            {review ? (
              <ul className="list">
                <li>复核人：{review.reviewer}</li>
                <li>结论：{reviewStatus}</li>
                <li>意见：{review.comment}</li>
                <li>时间：{review.created_at}</li>
              </ul>
            ) : (
              <p className="muted">当前还没有人工复核记录。</p>
            )}
            <p style={{ marginTop: 16 }}>
              <a href={`/ledger/${requestId}`}>查看因果簿独立页</a>
            </p>
          </article>
        </section>
      </main>
    );
  } catch {
    return (
      <main>
        <div className="card">
          <h1>请求详情暂时不可用</h1>
          <p className="muted">当前无法从 Python API 读取请求详情，请稍后重试。</p>
        </div>
      </main>
    );
  }
}
