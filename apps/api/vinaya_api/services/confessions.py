"""Confession service — 补赎机制，"慧"的反馈闭环。

当人工复核推翻（override）系统判断时：
1. 自动生成补赎记录
2. 统计同领域/同风险等级的推翻次数
3. 超过阈值时自动收紧规则（提升该领域的自动放行门槛）
4. 将修正动作写入补赎记录

这让系统能从错误中学习——不只是记录，而是真正修改自己的行为。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from apps.api.vinaya_api.schemas import ConfessionItem, ConfessionListResponse
from apps.api.vinaya_api.services.rules import get_rules_config, save_rules_config

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
CONFESSIONS_FILE = DATA_DIR / "confessions.json"

# 同一领域推翻次数达到此阈值时触发规则收紧
OVERRIDE_THRESHOLD = 3


def _ensure_confessions_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFESSIONS_FILE.exists():
        CONFESSIONS_FILE.write_text("[]", encoding="utf-8")


def _load_confessions() -> list[dict]:
    _ensure_confessions_file()
    return json.loads(CONFESSIONS_FILE.read_text(encoding="utf-8"))


def _save_confessions(items: list[dict]) -> None:
    _ensure_confessions_file()
    CONFESSIONS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def create_confession(
    request_id: str,
    domain: str,
    risk_level: str,
    original_decision: str,
    override_comment: str,
    reviewer: str,
) -> ConfessionItem:
    """人工推翻后自动触发的补赎流程。"""

    # 统计同领域历史推翻次数
    all_confessions = _load_confessions()
    domain_override_count = sum(
        1 for c in all_confessions if c["domain"] == domain
    ) + 1  # 加上当前这次

    # 决定补赎动作
    action_taken = _decide_action(domain, risk_level, domain_override_count)

    confession = ConfessionItem(
        confession_id=f"conf-{uuid4().hex[:12]}",
        request_id=request_id,
        domain=domain,
        risk_level=risk_level,
        original_decision=original_decision,
        override_comment=override_comment,
        reviewer=reviewer,
        action_taken=action_taken,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    all_confessions.append(confession.model_dump())
    _save_confessions(all_confessions)

    # 如果达到阈值，执行规则收紧
    if domain_override_count >= OVERRIDE_THRESHOLD:
        _tighten_rules(domain, domain_override_count)

    return confession


def _decide_action(domain: str, risk_level: str, override_count: int) -> str:
    """根据推翻次数决定补赎动作。"""
    if override_count >= OVERRIDE_THRESHOLD:
        return (
            f"领域 [{domain}] 已被推翻 {override_count} 次，"
            f"达到阈值 {OVERRIDE_THRESHOLD}，系统自动收紧规则：将 "
            f"warning 级戒律提升为 block 级，并降低自动放行上限。"
        )
    return (
        f"记录补赎事项。领域 [{domain}] 当前推翻计数 "
        f"{override_count}/{OVERRIDE_THRESHOLD}。"
    )


def _tighten_rules(domain: str, override_count: int) -> None:
    """当推翻次数超过阈值时，自动收紧规则配置。

    具体动作：
    1. 将所有 severity=warning 的戒律提升为 block
    2. 将自动放行上限降低一级（medium→low, high→medium）
    """
    config = get_rules_config()

    # 收紧戒律：warning → block
    for precept in config.precepts:
        if precept.enabled and precept.severity == "warning":
            precept.severity = "block"

    # 收紧风险阈值：降低自动放行上限
    current_max = config.risk_thresholds.get("auto_allow_max_risk", "low")
    downgrade_map = {"high": "medium", "medium": "low"}
    if current_max in downgrade_map:
        config.risk_thresholds["auto_allow_max_risk"] = downgrade_map[current_max]

    save_rules_config(config)


def get_confessions() -> ConfessionListResponse:
    """获取所有补赎记录。"""
    items = _load_confessions()
    return ConfessionListResponse(
        items=[ConfessionItem.model_validate(c) for c in items]
    )
