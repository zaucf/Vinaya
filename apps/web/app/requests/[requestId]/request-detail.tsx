import { ReviewForm } from "./review-form";

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
};

const DOMAIN_LABELS: Record<string, string> = {
  "content-moderation": "内容审核",
  "risk-review": "风险复核",
  "operations-trial": "运营试行",
  "hr-decision": "人事决策",
  "finance-approval": "财务审批",
  "legal-compliance": "法律合规",
  "customer-escalation": "客诉升级",
};

type ReviewItem = {
  review_id: string;
  request_id: string;
  reviewer: string;
  result: string;
  comment: string;
  created_at: string;
};

function mapReviewResultLabel(result: string) {
  return (
    {
      maintain: "已维持",
      revise: "已修改",
      override: "已推翻",
    }[result] ?? "已复核"
  );
}

function buildReviewSummary(reviews: ReviewItem[]) {
  if (reviews.length === 0) {
    return "当前仍以系统建议为准，尚未进入人工复核。";
  }

  const latest = reviews[reviews.length - 1];
  return (
    {
      maintain: "人工复核已维持系统建议，可按当前方案继续推进。",
      revise: "人工复核已修改系统建议，后续应以人工修正后的判断为准。",
      override: "人工复核已推翻系统建议，后续不得继续沿用原自动结论。",
    }[latest.result] ?? "人工复核已完成，请以人工意见为准。"
  );
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

async function getReviews(requestId: string): Promise<ReviewItem[]> {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests/${requestId}/reviews`, { cache: "no-store" });

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return data.items ?? [];
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
            <p style={{ marginTop: 16 }}>
              <a href="/requests">返回历史请求</a>
            </p>
          </div>
        </main>
      );
    }

    const reviews = await getReviews(requestId);
    const report = data.report;
    const latestReview = reviews.length > 0 ? reviews[reviews.length - 1] : null;
    const reviewStatus = latestReview ? mapReviewResultLabel(latestReview.result) : "未复核";
    const reviewSummary = buildReviewSummary(reviews);

    return (
      <main>
        <div className="header">
          <div>
            <div className="kicker">Vinaya Request</div>
            <h1>{report.request.title}</h1>
            <p className="muted">请求编号：{data.request_id}</p>
          </div>
          <div className="quick-links">
            <a className="button secondary" href="/requests">历史请求</a>
            <a className="button secondary" href={`/ledger/${requestId}`}>因果簿</a>
            <a className="button secondary" href="/">返回首页</a>
          </div>
        </div>

        <section className="grid two">
          <article className="card">
            <h2>请求内容</h2>
            <ul className="list">
              <li><strong>标题</strong>：{report.request.title}</li>
              <li><strong>领域</strong>：{DOMAIN_LABELS[report.request.domain] ?? report.request.domain}</li>
              <li><strong>风险等级</strong>：{RISK_LEVEL_LABELS[report.request.riskLevel] ?? report.request.riskLevel}</li>
              <li><strong>请求内容</strong>：{report.request.requestText}</li>
              {report.request.context ? (
                <li><strong>补充上下文</strong>：{report.request.context}</li>
              ) : null}
            </ul>
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
            <h2>辩义</h2>
            <ul className="list">
              <li>推荐方案：{report.deliberation.preferredOption}</li>
              {report.deliberation.options.map(
                (item: { name: string; score: number }) => (
                  <li key={item.name}>{item.name}：{Math.round(item.score * 100)}分</li>
                )
              )}
              {report.deliberation.dissentNotes.length > 0 && (
                <li>分歧记录：{report.deliberation.dissentNotes.join("；")}</li>
              )}
              <li>辩义风险：{RISK_LEVEL_LABELS[report.deliberation.deliberationRisk] ?? report.deliberation.deliberationRisk}</li>
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
            <h2 className="section-title">复核记录（{reviews.length}）</h2>
            {reviews.length === 0 ? (
              <p className="muted">当前还没有人工复核记录。</p>
            ) : (
              <div className="table-like">
                {[...reviews].reverse().map((review) => (
                  <div key={review.review_id} className="review-row">
                    <div className="review-row-header">
                      <strong>{review.reviewer}</strong>
                      <span className={`pill ${review.result}`}>
                        {mapReviewResultLabel(review.result)}
                      </span>
                    </div>
                    <p className="muted" style={{ margin: "8px 0 0" }}>{review.comment}</p>
                    <p className="muted" style={{ margin: "4px 0 0", fontSize: 12 }}>
                      {review.created_at}
                    </p>
                  </div>
                ))}
              </div>
            )}
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
          <p style={{ marginTop: 16 }}>
            <a href="/requests">返回历史请求</a>
          </p>
        </div>
      </main>
    );
  }
}
