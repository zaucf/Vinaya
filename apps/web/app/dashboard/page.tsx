async function getRequestHistory() {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch Vinaya request history from Python API");
  }

  return response.json();
}

async function getConfessions() {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/confessions`, { cache: "no-store" });

  if (!response.ok) {
    return { items: [] };
  }

  return response.json();
}

type RequestItem = {
  request_id: string;
  title: string;
  domain: string;
  risk_level: string;
  decision: string;
  review_status: string;
};

function calculateStats(items: RequestItem[]) {
  const total = items.length;
  const decisions = { allow: 0, defer: 0, stop: 0 };
  const risks = { low: 0, medium: 0, high: 0 };
  const reviews = { 未复核: 0, 已维持: 0, 已修改: 0, 已推翻: 0 };

  items.forEach((item) => {
    decisions[item.decision as keyof typeof decisions]++;
    risks[item.risk_level as keyof typeof risks]++;
    reviews[item.review_status as keyof typeof reviews]++;
  });

  const deferRate = total > 0 ? ((decisions.defer / total) * 100).toFixed(1) : "0.0";
  const reviewRate = total > 0 ? (((total - reviews.未复核) / total) * 100).toFixed(1) : "0.0";
  const overrideRate =
    total - reviews.未复核 > 0
      ? ((reviews.已推翻 / (total - reviews.未复核)) * 100).toFixed(1)
      : "0.0";

  return {
    total,
    decisions,
    risks,
    reviews,
    deferRate,
    reviewRate,
    overrideRate,
  };
}

export default async function DashboardPage() {
  let data;
  let confessions;
  try {
    data = await getRequestHistory();
    confessions = await getConfessions();
  } catch {
    return (
      <main>
        <div className="card">
          <h1>看板暂时不可用</h1>
          <p className="muted">无法从 API 读取数据，请稍后重试。</p>
        </div>
      </main>
    );
  }

  const stats = calculateStats(data.items);

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Dashboard</div>
          <h1>判断看板</h1>
          <p className="muted">
            展示系统克制能力：缓行比例、人工复核率、推翻率等核心指标。
          </p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/requests">
            历史请求
          </a>
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      {/* 核心指标 */}
      <section className="grid two">
        <article className="card">
          <h2>总请求数</h2>
          <p style={{ fontSize: 48, fontWeight: 700, margin: "12px 0" }}>
            {stats.total}
          </p>
          <p className="muted">已处理的判断请求总数</p>
        </article>

        <article className="card">
          <h2>缓行比例</h2>
          <p style={{ fontSize: 48, fontWeight: 700, margin: "12px 0" }}>
            {stats.deferRate}%
          </p>
          <p className="muted">
            系统克制能力的核心指标，缓行不是失败而是审慎
          </p>
        </article>

        <article className="card">
          <h2>人工复核率</h2>
          <p style={{ fontSize: 48, fontWeight: 700, margin: "12px 0" }}>
            {stats.reviewRate}%
          </p>
          <p className="muted">已进入人工复核的请求比例</p>
        </article>

        <article className="card">
          <h2>复核推翻率</h2>
          <p style={{ fontSize: 48, fontWeight: 700, margin: "12px 0" }}>
            {stats.overrideRate}%
          </p>
          <p className="muted">
            人工复核中推翻系统建议的比例，越低说明系统判断越准确
          </p>
        </article>
      </section>

      {/* 三类结论分布 */}
      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">三类结论分布</h2>
          <div className="table-like">
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill allow">allow（可行）</span>
                <strong>{stats.decisions.allow}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                满足基本戒律要求，风险可控，可在限定范围推进
              </p>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill defer">defer（缓行）</span>
                <strong>{stats.decisions.defer}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                默认克制性输出，需要试行、限权或人工复核
              </p>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill stop">stop（止行）</span>
                <strong>{stats.decisions.stop}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                触碰红线或会造成明显不可回退伤害
              </p>
            </div>
          </div>
        </article>

        {/* 风险等级分布 */}
        <article className="card">
          <h2 className="section-title">风险等级分布</h2>
          <div className="table-like">
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill allow">low（低风险）</span>
                <strong>{stats.risks.low}</strong>
              </div>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill defer">medium（中风险）</span>
                <strong>{stats.risks.medium}</strong>
              </div>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill stop">high（高风险）</span>
                <strong>{stats.risks.high}</strong>
              </div>
            </div>
          </div>
        </article>
      </section>

      {/* 复核状态分布 */}
      <section className="grid" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">复核状态分布</h2>
          <div className="table-like">
            <div className="review-row">
              <div className="review-row-header">
                <span>未复核</span>
                <strong>{stats.reviews.未复核}</strong>
              </div>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill maintain">已维持</span>
                <strong>{stats.reviews.已维持}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                人工复核维持系统建议
              </p>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill revise">已修改</span>
                <strong>{stats.reviews.已修改}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                人工复核修改系统建议
              </p>
            </div>
            <div className="review-row">
              <div className="review-row-header">
                <span className="pill override">已推翻</span>
                <strong>{stats.reviews.已推翻}</strong>
              </div>
              <p className="muted" style={{ margin: "8px 0 0" }}>
                人工复核推翻系统建议
              </p>
            </div>
          </div>
        </article>
      </section>

      {/* 补赎记录（慧：系统从错误中学习的证据） */}
      {confessions.items.length > 0 ? (
        <section className="grid" style={{ marginTop: 16 }}>
          <article className="card">
            <h2 className="section-title">
              补赎台（{confessions.items.length} 条记录）
            </h2>
            <p className="muted" style={{ marginBottom: 16 }}>
              每一次人工推翻都会触发补赎：记录错误、统计趋势、自动收紧规则。这是"慧"的反馈闭环。
            </p>
            <div className="table-like">
              {confessions.items
                .slice()
                .reverse()
                .map(
                  (item: {
                    confession_id: string;
                    request_id: string;
                    domain: string;
                    risk_level: string;
                    original_decision: string;
                    override_comment: string;
                    reviewer: string;
                    action_taken: string;
                    created_at: string;
                  }) => (
                    <div key={item.confession_id} className="review-row">
                      <div className="review-row-header">
                        <span>
                          <strong>{item.domain}</strong>
                          <span className="pill" style={{ marginLeft: 8 }}>
                            {item.risk_level}
                          </span>
                          <span
                            className={`pill ${item.original_decision}`}
                            style={{ marginLeft: 4 }}
                          >
                            原判：{item.original_decision}
                          </span>
                        </span>
                        <span className="pill override">被推翻</span>
                      </div>
                      <p className="muted" style={{ margin: "8px 0 4px" }}>
                        推翻意见：{item.override_comment}
                      </p>
                      <p className="muted" style={{ margin: "4px 0" }}>
                        补赎动作：{item.action_taken}
                      </p>
                      <p
                        className="muted"
                        style={{ margin: "4px 0 0", fontSize: 12 }}
                      >
                        复核人：{item.reviewer} · {item.created_at}
                        {" · "}
                        <a href={`/requests/${item.request_id}`}>
                          查看原始请求
                        </a>
                      </p>
                    </div>
                  )
                )}
            </div>
          </article>
        </section>
      ) : null}

      {/* 系统理念 */}
      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">成功标准</h2>
          <p className="muted">
            Vinaya 的成功不以"自动执行更多任务"为标志，而以以下指标衡量：
          </p>
          <ul className="list">
            <li>高风险请求中"缓行"比例是否合理</li>
            <li>人工复核推翻率是否下降</li>
            <li>明显误伤率是否下降</li>
            <li>不确定性表达是否更充分</li>
            <li>回退机制是否真正可用</li>
            <li>因果记录是否能支撑规则修订</li>
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">核心信条</h2>
          <ul className="list">
            <li>先净化判断，再允许执行</li>
            <li>先问动机，再问方案</li>
            <li>先看因缘，再下结论</li>
            <li>先守戒律，再求方便</li>
            <li>先缓后断，先试后放</li>
            <li>先记后改，不掩过失</li>
          </ul>
        </article>
      </section>
    </main>
  );
}
