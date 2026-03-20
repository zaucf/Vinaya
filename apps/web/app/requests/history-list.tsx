"use client";

import { useMemo, useState } from "react";

type HistoryItem = {
  request_id: string;
  title: string;
  domain: string;
  risk_level: string;
  decision: string;
  review_status: string;
  submitter?: string;
};

export function HistoryList({ items }: { items: HistoryItem[] }) {
  const [keyword, setKeyword] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [decisionFilter, setDecisionFilter] = useState("all");
  const [reviewFilter, setReviewFilter] = useState("all");

  const filteredItems = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return items.filter((item) => {
      if (normalizedKeyword) {
        const haystack = `${item.title} ${item.domain}`.toLowerCase();
        if (!haystack.includes(normalizedKeyword)) {
          return false;
        }
      }
      if (riskFilter !== "all" && item.risk_level !== riskFilter) {
        return false;
      }
      if (decisionFilter !== "all" && item.decision !== decisionFilter) {
        return false;
      }
      if (reviewFilter !== "all" && item.review_status !== reviewFilter) {
        return false;
      }
      return true;
    });
  }, [items, keyword, riskFilter, decisionFilter, reviewFilter]);

  return (
    <div className="grid" style={{ gap: 12 }}>
      <div className="filters">
        <label className="field compact keyword-field">
          <span>关键词</span>
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="搜索标题或领域"
          />
        </label>
        <label className="field compact">
          <span>风险</span>
          <select
            value={riskFilter}
            onChange={(event) => setRiskFilter(event.target.value)}
          >
            <option value="all">全部</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>
        <label className="field compact">
          <span>结论</span>
          <select
            value={decisionFilter}
            onChange={(event) => setDecisionFilter(event.target.value)}
          >
            <option value="all">全部</option>
            <option value="allow">allow</option>
            <option value="defer">defer</option>
            <option value="stop">stop</option>
          </select>
        </label>
        <label className="field compact">
          <span>复核</span>
          <select
            value={reviewFilter}
            onChange={(event) => setReviewFilter(event.target.value)}
          >
            <option value="all">全部</option>
            <option value="未复核">未复核</option>
            <option value="已维持">已维持</option>
            <option value="已修改">已修改</option>
            <option value="已推翻">已推翻</option>
          </select>
        </label>
      </div>

      {filteredItems.length === 0 ? (
        <p className="muted">当前筛选条件下没有请求。</p>
      ) : (
        <div className="table-like">
          {filteredItems.map((item) => (
            <a
              key={item.request_id}
              className="history-row"
              href={`/requests/${item.request_id}`}
            >
              <div>
                <strong>{item.title}</strong>
                <p className="muted">{item.domain}{item.submitter && item.submitter !== "anonymous" ? ` · 提交人: ${item.submitter}` : ""}</p>
              </div>
              <div>
                <span className="pill">{item.risk_level}</span>
                <span className={`pill ${item.decision}`}>{item.decision}</span>
                <span className="pill">{item.review_status}</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
