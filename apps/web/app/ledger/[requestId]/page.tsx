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

export default async function LedgerPage({
  params,
}: {
  params: Promise<{ requestId: string }>;
}) {
  const { requestId } = await params;
  const data = await getRequestReport(requestId);

  if (data === null) {
    return (
      <main>
        <div className="card">
          <h1>因果簿不存在</h1>
          <p className="muted">没有找到对应请求的因果记录。</p>
        </div>
      </main>
    );
  }

  const report = data.report;

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Ledger</div>
          <h1>因果簿</h1>
          <p className="muted">请求编号：{data.request_id}</p>
        </div>
      </div>

      <section className="grid two">
        <article className="card">
          <h2>发心</h2>
          <pre className="pre">{JSON.stringify(report.intention, null, 2)}</pre>
        </article>
        <article className="card">
          <h2>观缘</h2>
          <pre className="pre">{JSON.stringify(report.causality, null, 2)}</pre>
        </article>
        <article className="card">
          <h2>持戒</h2>
          <pre className="pre">{JSON.stringify(report.precepts, null, 2)}</pre>
        </article>
        <article className="card">
          <h2>辩义与缓行</h2>
          <pre className="pre">
            {JSON.stringify(
              {
                deliberation: report.deliberation,
                gradualRelease: report.gradualRelease,
              },
              null,
              2
            )}
          </pre>
          <p style={{ marginTop: 16 }}>
            <a href={`/requests/${requestId}`}>返回请求详情</a>
          </p>
        </article>
      </section>
    </main>
  );
}
