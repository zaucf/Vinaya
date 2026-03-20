"use client";

import { useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

export default function ExportPage() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [downloading, setDownloading] = useState(false);

  async function handleDownload(format: "json" | "csv" | "pdf") {
    setDownloading(true);
    try {
      const params = new URLSearchParams();
      params.set("format", format);
      if (dateFrom) params.set("from", dateFrom);
      if (dateTo) params.set("to", dateTo);

      const res = await fetch(`${apiBaseUrl}/api/export?${params.toString()}`);
      if (!res.ok) {
        throw new Error("导出失败");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;

      const ext = format === "json" ? "json" : format === "csv" ? "csv" : "pdf";
      a.download = `vinaya-audit.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "导出失败");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Export</div>
          <h1>导出与审计</h1>
          <p className="muted">按时间范围导出完整判断链，满足合规审计需求。支持 JSON / CSV / PDF 三种格式。</p>
        </div>
        <div className="quick-links">
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <section className="grid">
        <article className="card">
          <h2 className="section-title">选择导出范围</h2>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
            <label className="field" style={{ flex: 1, minWidth: 200 }}>
              <span>起始日期</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </label>
            <label className="field" style={{ flex: 1, minWidth: 200 }}>
              <span>截止日期</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </label>
          </div>

          <h2 className="section-title">下载格式</h2>
          <div className="action-row" style={{ gap: 12 }}>
            <button
              className="button"
              type="button"
              disabled={downloading}
              onClick={() => handleDownload("json")}
            >
              JSON
            </button>
            <button
              className="button secondary"
              type="button"
              disabled={downloading}
              onClick={() => handleDownload("csv")}
            >
              CSV
            </button>
            <button
              className="button secondary"
              type="button"
              disabled={downloading}
              onClick={() => handleDownload("pdf")}
            >
              PDF
            </button>
          </div>

          {downloading && <p className="muted" style={{ marginTop: 12 }}>正在生成导出文件...</p>}
        </article>
      </section>
    </main>
  );
}
