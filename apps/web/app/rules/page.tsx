export default function RulesPage() {
  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Rules</div>
          <h1>规则说明</h1>
          <p className="muted">
            这一页用于展示 Vinaya 的五戒、三类结论与人工主权边界。
          </p>
        </div>
      </div>

      <section className="grid two">
        <article className="card">
          <h2 className="section-title">五戒</h2>
          <ul className="list">
            <li>不妄语：不把不确定性包装成确定性</li>
            <li>不害生：不为了效率制造明显伤害</li>
            <li>不偷夺：不不公平地剥夺机会、资源与尊严</li>
            <li>不越界：不超出系统授权边界</li>
            <li>不昏乱：证据不足时不做高强度判断</li>
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">三类结论</h2>
          <ul className="list">
            <li>`allow`：可行，可在限定范围推进</li>
            <li>`defer`：缓行，需要补信息、试行或人工复核</li>
            <li>`stop`：止行，已触碰红线或风险不可接受</li>
          </ul>
        </article>
      </section>

      <section className="grid" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">人工主权边界</h2>
          <ul className="list">
            <li>医疗、司法、惩罚性决定必须保留人工主权</li>
            <li>重大资源分配与不可逆后果事项不得由系统单独裁决</li>
            <li>高风险判断默认进入缓行，并建议人工复核</li>
            <li>人工复核结果应覆盖自动建议并留档</li>
          </ul>
          <p style={{ marginTop: 16 }}>
            <a href="/requests">查看历史请求</a>
          </p>
        </article>
      </section>
    </main>
  );
}
