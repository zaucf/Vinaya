"""Vinaya SDK 使用示例。

展示三种使用方式：
1. 远程模式（连接 API）
2. 本地 mock 模式（测试）
3. 集成到 AI 系统的决策网关
"""

# ============================================================================
# 示例 1：远程模式（连接 API）
# ============================================================================

def example_remote_client():
    """远程模式：通过 HTTP 连接到 Vinaya API 服务器。

    适用场景：
    - 已部署 Vinaya API 服务器
    - 多个客户端共享一个判断引擎
    - 需要集中管理 LLM 配置
    """
    from vinaya import VinayaClient

    # 初始化客户端（连接到本地或远程服务器）
    client = VinayaClient(base_url="http://localhost:8000")

    # 检查服务健康状态
    if not client.health():
        print("Vinaya API 服务器未就绪")
        return

    # 执行判断
    result = client.judge(
        title="代码生成请求",
        request_text="请帮我生成一个 Python 函数，用于计算斐波那契数列",
        domain="code",
        risk_level="low",
        context="这是一个学习练习",
    )

    # 读取机器友好的摘要
    summary = result.summary
    print(f"决策: {summary.decision}")  # 'allow', 'defer', or 'stop'
    print(f"风险等级: {summary.risk_level}")  # 'low', 'medium', or 'high'
    print(f"硬阻断: {summary.hard_block}")
    print(f"需要人工复核: {summary.human_review_required}")

    # 检查戒律违规
    if summary.precept_violations:
        print("戒律违规:")
        for v in summary.precept_violations:
            print(f"  - {v.name}: {v.status} - {v.reason}")

    # 根据决策执行后续操作
    if summary.decision == "allow":
        print("✓ 请求通过，执行操作")
    elif summary.decision == "defer":
        print("⏳ 请求需要更多审查，暂缓执行")
    else:  # stop
        print("✗ 请求被拒绝，终止操作")


# ============================================================================
# 示例 2：本地 Mock 模式（测试）
# ============================================================================

def example_local_mock():
    """本地 Mock 模式：无需 LLM，快速返回模拟结果。

    适用场景：
    - 单元测试
    - 集成测试
    - 开发调试
    - 演示演示
    """
    from vinaya import VinayaLocalClient

    # 初始化本地客户端（mock 模式）
    client = VinayaLocalClient(use_mock=True)

    # 执行判断（立即返回，无需等待 LLM）
    result = client.judge(
        title="测试请求",
        request_text="这是一个测试请求",
        domain="test",
        risk_level="low",
    )

    print(f"[Mock] 决策: {result.summary.decision}")
    print(f"[Mock] 推理: {result.summary.reasoning}")


# ============================================================================
# 示例 3：集成到 AI 系统的决策网关
# ============================================================================

class AIRequestGateway:
    """AI 请求决策网关示例。

    在执行任何 AI 操作前，先通过 Vinaya 判断。
    """

    def __init__(self, vinaya_client):
        self.vinaya = vinaya_client

    def handle_request(self, user_input: str) -> str:
        """处理用户请求的网关。"""
        # 首先通过 Vinaya 判断
        result = self.vinaya.judge(
            title="用户请求",
            request_text=user_input,
            domain="general",
            risk_level="medium",  # 默认中等风险
        )

        summary = result.summary

        # 根据决策处理请求
        if summary.decision == "allow":
            # 执行实际操作
            return self._execute_safely(user_input)
        elif summary.decision == "defer":
            # 需要更多审查
            return f"请求需要进一步审查：{summary.reasoning}"
        else:  # stop
            # 拒绝执行
            return f"请求被拒绝：{summary.reasoning}"

    def _execute_safely(self, user_input: str) -> str:
        """安全执行用户请求（示例）。"""
        # 这里是实际的 AI 操作逻辑
        return f"已执行：{user_input[:50]}..."


def example_ai_gateway():
    """AI 系统集成示例。"""
    from vinaya import VinayaLocalClient

    # 使用本地客户端（在生产环境中可以换成远程客户端）
    vinaya = VinayaLocalClient(use_mock=True)
    gateway = AIRequestGateway(vinaya)

    # 处理用户请求
    user_requests = [
        "请帮我写一个 Python 脚本",
        "如何绕过网站登录验证",
        "解释量子计算的基本原理",
    ]

    for req in user_requests:
        print(f"\n请求: {req}")
        response = gateway.handle_request(req)
        print(f"响应: {response}")


# ============================================================================
# 示例 4：本地 LLM 模式（自定义 LLM 和规则）
# ============================================================================

def example_local_llm():
    """本地 LLM 模式：使用自定义的 LLM 调用函数。

    适用场景：
    - 嵌入到现有 AI 系统
    - 使用自己的 LLM 配置
    - 需要自定义规则
    """
    from vinaya import VinayaLocalClient

    # 定义自定义的 LLM 调用函数
    def my_chat_fn(system_prompt: str, user_prompt: str) -> dict:
        """你的 LLM 调用逻辑。"""
        # 这里是示例，实际使用时替换为你的 LLM 调用
        # 例如：OpenAI、Anthropic、本地模型等
        import json

        # 模拟返回
        return {
            "intention": {
                "primaryIntent": "测试",
                "mixedMotives": [],
                "beneficiaries": [],
                "costBearers": [],
                "intentionRisk": "low",
            },
            "causality": {
                "proximateCauses": [],
                "rootCauses": [],
                "affectedParties": [],
                "externalities": [],
                "causalityRisk": "low",
            },
            "precepts": {
                "preceptFindings": [],
                "hardBlock": False,
                "humanReviewRequired": False,
                "preceptRisk": "low",
            },
            "deliberation": {
                "options": [],
                "preferredOption": "",
                "dissentNotes": [],
                "deliberationRisk": "low",
            },
            "gradualRelease": {
                "mode": "allow",
                "trialPlan": None,
                "releaseRisk": "low",
            },
            "decision": "allow",
            "reasoningSummary": "测试模式通过",
        }

    # 定义自定义的规则配置
    def my_rules_provider():
        """你的规则配置。"""
        from dataclasses import dataclass

        @dataclass
        class Precept:
            name: str
            enabled: bool
            description: str
            severity: str

        @dataclass
        class Config:
            precepts: list
            risk_thresholds: dict

        return Config(
            precepts=[
                Precept(
                    name="无害性",
                    enabled=True,
                    description="不对任何有情众生造成伤害",
                    severity="block",
                ),
            ],
            risk_thresholds={
                "auto_allow_max_risk": "low",
                "force_human_review_min_risk": "high",
            },
        )

    # 初始化本地客户端
    client = VinayaLocalClient(
        chat_fn=my_chat_fn,
        rules_provider=my_rules_provider,
    )

    # 执行判断
    result = client.judge(
        title="自定义 LLM 测试",
        request_text="测试内容",
        domain="test",
        risk_level="low",
    )

    print(f"决策: {result.summary.decision}")


if __name__ == "__main__":
    print("=" * 60)
    print("示例 1：远程模式")
    print("=" * 60)
    # 取消注释以运行远程模式（需要先启动 API 服务器）
    # example_remote_client()

    print("\n" + "=" * 60)
    print("示例 2：本地 Mock 模式")
    print("=" * 60)
    example_local_mock()

    print("\n" + "=" * 60)
    print("示例 3：AI 网关集成")
    print("=" * 60)
    example_ai_gateway()

    print("\n" + "=" * 60)
    print("示例 4：本地 LLM 模式")
    print("=" * 60)
    example_local_llm()
