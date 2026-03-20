"use client";

import { useEffect, useState } from "react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_VINAYA_API_URL ?? "http://127.0.0.1:4010";

export function NavBar() {
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function fetchCount() {
      try {
        const res = await fetch(`${apiBaseUrl}/api/notifications/unread-count`, {
          cache: "no-store",
        });
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) {
            setUnreadCount(data.count ?? 0);
          }
        }
      } catch {
        // 静默忽略
      }
    }

    fetchCount();
    const timer = setInterval(fetchCount, 15000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <nav className="top-bar">
      <a href="/" className="brand">Vinaya · 戒定慧引擎</a>
      <div className="nav-links">
        <a className="button nav-button" href="/dashboard">
          判断看板
        </a>
        <a className="button nav-button" href="/requests">
          历史请求
        </a>
        <a className="button nav-button" href="/notifications" style={{ position: "relative" }}>
          通知
          {unreadCount > 0 && (
            <span
              style={{
                position: "absolute",
                top: -6,
                right: -6,
                background: "var(--stop)",
                color: "#fff",
                borderRadius: "50%",
                minWidth: 18,
                height: 18,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 11,
                fontWeight: 700,
                padding: "0 4px",
              }}
            >
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </a>
        <a className="button nav-button" href="/export">
          导出
        </a>
        <a className="button nav-button" href="/models">
          模型中心
        </a>
        <a className="button nav-button" href="/rules">
          规则说明
        </a>
        <a className="button nav-button" href="/cases">
          案例库
        </a>
      </div>
    </nav>
  );
}
