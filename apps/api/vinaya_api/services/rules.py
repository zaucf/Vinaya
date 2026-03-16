"""Rules configuration service for Vinaya.

Manages the five precepts configuration, defer strategies,
and risk threshold settings.
"""

from __future__ import annotations

import json
from pathlib import Path

from apps.api.vinaya_api.schemas import (
    DeferStrategyConfig,
    PreceptConfig,
    RulesConfigResponse,
)

DATA_DIR = Path(__file__).resolve().parents[4] / "data"
RULES_FILE = DATA_DIR / "rules-config.json"

DEFAULT_PRECEPTS: list[dict] = [
    {
        "name": "不妄语",
        "enabled": True,
        "description": "不把不确定性伪装成确定性，不编造事实或依据",
        "severity": "block",
    },
    {
        "name": "不害生",
        "enabled": True,
        "description": "不为了效率制造明显可预见的伤害",
        "severity": "block",
    },
    {
        "name": "不偷夺",
        "enabled": True,
        "description": "不不公平地剥夺机会、资源、申诉空间或尊严",
        "severity": "warning",
    },
    {
        "name": "不越界",
        "enabled": True,
        "description": "不超出系统被授权的适用边界",
        "severity": "block",
    },
    {
        "name": "不昏乱",
        "enabled": True,
        "description": "证据不足、上下文残缺时不做高强度判断",
        "severity": "warning",
    },
]

DEFAULT_DEFER_STRATEGIES: list[dict] = [
    {
        "strategy_id": "trial-restrict",
        "name": "限期限制",
        "description": "限制部分功能一段时间，到期自动复核",
        "enabled": True,
        "default_duration_hours": 72,
        "require_human_review": True,
        "auto_rollback": True,
    },
    {
        "strategy_id": "scope-reduce",
        "name": "范围收缩",
        "description": "仅在小范围试行，观察效果后再决定是否扩大",
        "enabled": True,
        "default_duration_hours": 168,
        "require_human_review": True,
        "auto_rollback": False,
    },
    {
        "strategy_id": "human-review",
        "name": "人工复核",
        "description": "暂不执行，升级到人工审批队列",
        "enabled": True,
        "default_duration_hours": 24,
        "require_human_review": True,
        "auto_rollback": False,
    },
    {
        "strategy_id": "evidence-gather",
        "name": "补充证据",
        "description": "在证据不足时暂缓执行，要求补充相关信息后再判断",
        "enabled": True,
        "default_duration_hours": 48,
        "require_human_review": False,
        "auto_rollback": False,
    },
]

DEFAULT_RISK_THRESHOLDS: dict = {
    "auto_allow_max_risk": "low",
    "force_human_review_min_risk": "high",
    "default_defer_duration_hours": 72,
    "max_auto_decisions_per_hour": 50,
}


def _ensure_rules_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not RULES_FILE.exists():
        default_config = {
            "precepts": DEFAULT_PRECEPTS,
            "defer_strategies": DEFAULT_DEFER_STRATEGIES,
            "risk_thresholds": DEFAULT_RISK_THRESHOLDS,
        }
        RULES_FILE.write_text(
            json.dumps(default_config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def get_rules_config() -> RulesConfigResponse:
    _ensure_rules_file()
    raw = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    return RulesConfigResponse(
        precepts=[PreceptConfig.model_validate(p) for p in raw["precepts"]],
        defer_strategies=[DeferStrategyConfig.model_validate(s) for s in raw["defer_strategies"]],
        risk_thresholds=raw["risk_thresholds"],
    )


def save_rules_config(config: RulesConfigResponse) -> RulesConfigResponse:
    _ensure_rules_file()
    data = {
        "precepts": [p.model_dump() for p in config.precepts],
        "defer_strategies": [s.model_dump() for s in config.defer_strategies],
        "risk_thresholds": config.risk_thresholds,
    }
    RULES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config
