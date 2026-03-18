import { HistoryList } from "./history-list";

async function getRequestHistory() {
  const baseUrl = process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";
  const response = await fetch(`${baseUrl}/api/requests`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch Vinaya request history from Python API");
  }

  return response.json();
}

export default async function RequestHistoryPage() {
  const data = await getRequestHistory();

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya History</div>
          <h1>历史请求</h1>
          <p className="muted">这里展示通过 Python API 持久化保存的判断请求记录。</p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <section className="grid">
        <article className="card">
          <h2 className="section-title">请求列表</h2>
          <HistoryList items={data.items} />
        </article>
      </section>
    </main>
  );
}
