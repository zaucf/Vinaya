"""多角色辩义引擎。

三个角色（倡导者 / 批评者 / 仲裁者）独立分析后综合，
替换原始辩义输出，提升辩义阶段的深度与可信度。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .types import DeliberationResult, RoleDebatePosition, VinayaRequest

ADVOCATE_PROMPT = """你是辩义阶段的"倡导者"角色。你站在请求方的立场，为执行找到最优方案，最大化收益。

你会收到一个判断请求以及前序阶段（发心/观缘/持戒）的分析结果。
请从请求方的角度出发，论证为什么应该推进，并推荐最优执行方案。

请返回严格 JSON（不要 Markdown），格式如下：
{
  "role": "advocate",
  "stance": "你的总体立场（一句话）",
  "reasoning": "详细论证（2-3 句话）",
  "suggestedOption": "你推荐的方案名称"
}"""

CRITIC_PROMPT = """你是辩义阶段的"批评者"角色。你站在风险方的立场，找出方案的缺陷和盲点。

你会收到一个判断请求以及前序阶段（发心/观缘/持戒）的分析结果。
请从风险防控的角度出发，指出潜在问题、盲点和不足。

请返回严格 JSON（不要 Markdown），格式如下：
{
  "role": "critic",
  "stance": "你的总体立场（一句话）",
  "reasoning": "详细论证（2-3 句话）",
  "suggestedOption": "你推荐的方案名称"
}"""

MODERATOR_PROMPT = """你是辩义阶段的"仲裁者"角色。你需要综合倡导者和批评者的意见，给出最终方案评分和推荐。

你会收到：
1. 判断请求和前序阶段分析
2. 倡导者的意见
3. 批评者的意见

请综合两方观点，客观评判，给出最终方案。

请返回严格 JSON（不要 Markdown），格式如下：
{
  "role": "moderator",
  "stance": "你的综合立场（一句话）",
  "reasoning": "综合论证（2-3 句话）",
  "suggestedOption": "你推荐的最终方案名称",
  "options": [{"name": "方案名", "score": 0.85}, ...],
  "preferredOption": "最终推荐方案",
  "dissentNotes": ["分歧记录1", ...],
  "deliberationRisk": "low|medium|high",
  "consensusLevel": 0.75
}"""


def _build_context_message(
    request: VinayaRequest,
    prior_stages: dict[str, Any],
) -> str:
    """构建角色上下文信息。"""
    return json.dumps(
        {
            "request": {
                "title": request.get("title"),
                "requestText": request.get("requestText"),
                "domain": request.get("domain"),
                "riskLevel": request.get("riskLevel"),
            },
            "priorStages": prior_stages,
        },
        ensure_ascii=False,
        indent=2,
    )


def _call_role(
    role_prompt: str,
    user_message: str,
    chat_fn: Callable,
) -> dict[str, Any]:
    """调用单个角色的 LLM。"""
    return chat_fn(system_prompt=role_prompt, user_prompt=user_message)


def run_multirole_deliberation(
    request: VinayaRequest,
    prior_stages: dict[str, Any],
    chat_fn: Callable,
) -> DeliberationResult:
    """运行多角色辩义。

    Args:
        request: 判断请求数据
        prior_stages: 前序阶段结果 {"intention": ..., "causality": ..., "precepts": ...}
        chat_fn: LLM 调用函数

    Returns:
        包含 roleDebates 和 consensusLevel 的 DeliberationResult
    """
    context_msg = _build_context_message(request, prior_stages)

    # 并行调用倡导者和批评者
    with ThreadPoolExecutor(max_workers=2) as pool:
        advocate_future = pool.submit(_call_role, ADVOCATE_PROMPT, context_msg, chat_fn)
        critic_future = pool.submit(_call_role, CRITIC_PROMPT, context_msg, chat_fn)

        advocate_result = advocate_future.result()
        critic_result = critic_future.result()

    # 仲裁者：收到前两者输出
    moderator_msg = json.dumps(
        {
            "request": {
                "title": request.get("title"),
                "requestText": request.get("requestText"),
                "domain": request.get("domain"),
                "riskLevel": request.get("riskLevel"),
            },
            "priorStages": prior_stages,
            "advocateOpinion": advocate_result,
            "criticOpinion": critic_result,
        },
        ensure_ascii=False,
        indent=2,
    )
    moderator_result = _call_role(MODERATOR_PROMPT, moderator_msg, chat_fn)

    # 组装角色辩论记录
    role_debates: list[RoleDebatePosition] = []
    for r in [advocate_result, critic_result, moderator_result]:
        role_debates.append({
            "role": r.get("role", "unknown"),
            "stance": r.get("stance", ""),
            "reasoning": r.get("reasoning", ""),
            "suggestedOption": r.get("suggestedOption", ""),
        })

    # 从仲裁者结果提取最终辩义结论
    return {
        "options": moderator_result.get("options", []),
        "preferredOption": moderator_result.get("preferredOption", ""),
        "dissentNotes": moderator_result.get("dissentNotes", []),
        "deliberationRisk": moderator_result.get("deliberationRisk", "medium"),
        "roleDebates": role_debates,
        "consensusLevel": moderator_result.get("consensusLevel", 0.5),
    }
