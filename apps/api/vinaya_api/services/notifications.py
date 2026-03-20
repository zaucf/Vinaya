"""Notification service — 通知机制。

当判断结果为 defer/stop 或需要人工复核时，自动创建通知。
复核推翻时也创建通知。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from apps.api.vinaya_api.schemas import NotificationItem, NotificationListResponse, UnreadCountResponse

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"


def _ensure_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not NOTIFICATIONS_FILE.exists():
        NOTIFICATIONS_FILE.write_text("[]", encoding="utf-8")


def _load() -> list[dict]:
    _ensure_file()
    return json.loads(NOTIFICATIONS_FILE.read_text(encoding="utf-8"))


def _save(items: list[dict]) -> None:
    _ensure_file()
    NOTIFICATIONS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_notification(
    request_id: str,
    title: str,
    message: str,
    notification_type: str,
) -> NotificationItem:
    notification = NotificationItem(
        notification_id=f"notif-{uuid4().hex[:12]}",
        request_id=request_id,
        title=title,
        message=message,
        type=notification_type,  # type: ignore[arg-type]
        is_read=False,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    items = _load()
    items.append(notification.model_dump())
    _save(items)
    return notification


def get_notifications(is_read: bool | None = None) -> NotificationListResponse:
    items = _load()
    if is_read is not None:
        items = [n for n in items if n.get("is_read") == is_read]
    # 未读在前，按时间倒序
    items.sort(key=lambda n: (n.get("is_read", False), n.get("created_at", "")), reverse=False)
    items.sort(key=lambda n: n.get("is_read", False))
    return NotificationListResponse(
        items=[NotificationItem.model_validate(n) for n in items]
    )


def mark_as_read(notification_id: str) -> NotificationItem | None:
    items = _load()
    for item in items:
        if item.get("notification_id") == notification_id:
            item["is_read"] = True
            _save(items)
            return NotificationItem.model_validate(item)
    return None


def mark_all_as_read() -> int:
    items = _load()
    count = 0
    for item in items:
        if not item.get("is_read", False):
            item["is_read"] = True
            count += 1
    if count > 0:
        _save(items)
    return count


def get_unread_count() -> UnreadCountResponse:
    items = _load()
    count = sum(1 for n in items if not n.get("is_read", False))
    return UnreadCountResponse(count=count)
