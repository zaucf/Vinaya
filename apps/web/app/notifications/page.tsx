"use client";

import { useCallback, useEffect, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

type NotificationItem = {
  notification_id: string;
  request_id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
};

const TYPE_LABELS: Record<string, string> = {
  defer: "缓行",
  stop: "止行",
  human_review: "需复核",
  override: "已推翻",
};

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "unread" | "read">("all");

  const fetchNotifications = useCallback(async () => {
    try {
      const params = filter === "unread" ? "?is_read=false" : filter === "read" ? "?is_read=true" : "";
      const res = await fetch(`${apiBaseUrl}/api/notifications${params}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setItems(data.items ?? []);
      }
    } catch {
      // 忽略
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  async function handleMarkRead(notificationId: string) {
    await fetch(`${apiBaseUrl}/api/notifications/${notificationId}/read`, { method: "PUT" });
    fetchNotifications();
  }

  async function handleMarkAllRead() {
    await fetch(`${apiBaseUrl}/api/notifications/read-all`, { method: "PUT" });
    fetchNotifications();
  }

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Notifications</div>
          <h1>通知中心</h1>
          <p className="muted">判断结果为缓行/止行或需要人工复核时，系统自动生成通知。</p>
        </div>
        <div className="quick-links">
          <button className="button secondary" type="button" onClick={handleMarkAllRead}>
            全部标记已读
          </button>
          <a className="button secondary" href="/">
            返回首页
          </a>
        </div>
      </div>

      <section className="grid">
        <article className="card">
          <div className="filters" style={{ marginBottom: 16 }}>
            <label className="field compact">
              <span>筛选</span>
              <select value={filter} onChange={(e) => setFilter(e.target.value as "all" | "unread" | "read")}>
                <option value="all">全部</option>
                <option value="unread">未读</option>
                <option value="read">已读</option>
              </select>
            </label>
          </div>

          {loading ? (
            <p className="muted">加载中...</p>
          ) : items.length === 0 ? (
            <p className="muted">暂无通知。</p>
          ) : (
            <div className="table-like">
              {items.map((item) => (
                <div
                  key={item.notification_id}
                  className="review-row"
                  style={{
                    opacity: item.is_read ? 0.6 : 1,
                    borderLeft: item.is_read ? "3px solid transparent" : "3px solid var(--stop)",
                  }}
                >
                  <div className="review-row-header">
                    <a href={`/requests/${item.request_id}`} style={{ fontWeight: item.is_read ? 400 : 700 }}>
                      {item.title}
                    </a>
                    <span className={`pill ${item.type}`}>
                      {TYPE_LABELS[item.type] ?? item.type}
                    </span>
                  </div>
                  <p className="muted" style={{ margin: "8px 0 0" }}>{item.message}</p>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                    <p className="muted" style={{ margin: 0, fontSize: 12 }}>
                      {item.created_at}
                    </p>
                    {!item.is_read && (
                      <button
                        className="button secondary"
                        type="button"
                        style={{ fontSize: 12, padding: "2px 8px" }}
                        onClick={() => handleMarkRead(item.notification_id)}
                      >
                        标记已读
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>
    </main>
  );
}
