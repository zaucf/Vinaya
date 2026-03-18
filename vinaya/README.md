# Vinaya SDK

AI judgment purification engine — Python SDK for AI system integration.

## 安装

```bash
# 安装 SDK（零依赖）
pip install -e .

# 安装 SDK + API 服务器（FastAPI 等）
pip install -e ".[server]"
```

## 使用方式

### 1. 远程模式（HTTP 客户端）

连接到已部署的 Vinaya API 服务器：

```python
from vinaya import VinayaClient

client = VinayaClient(base_url="http://localhost:8000")
result = client.judge(
    title="代码生成请求",
    request_text="请帮我生成一个 Python 函数",
    domain="code",
    risk_level="low",
)

print(result.summary.decision)  # 'allow', 'defer', or 'stop'
```

### 2. 本地模式（直接调用）

嵌入到你的 AI 系统中，无需 HTTP 服务器：

```python
from vinaya import VinayaLocalClient

# Mock 模式（测试用）
client = VinayaLocalClient(use_mock=True)
result = client.judge(title="测试", request_text="...", domain="test", risk_level="low")

# 真实 LLM 模式
from my_llm import my_chat_json
from my_rules import get_rules

client = VinayaLocalClient(chat_fn=my_chat_json, rules_provider=get_rules)
result = client.judge(...)
```

### 3. AI 网关集成

```python
from vinaya import VinayaLocalClient

vinaya = VinayaLocalClient(use_mock=True)

def handle_user_request(user_input: str):
    result = vinaya.judge(
        title="用户请求",
        request_text=user_input,
        domain="general",
        risk_level="medium",
    )

    if result.summary.decision == "allow":
        return execute_request(user_input)
    elif result.summary.decision == "defer":
        return "请求需要进一步审查"
    else:  # stop
        return "请求被拒绝"
```

## 数据结构

### JudgmentSummary（机器友好）

```python
@dataclass
class JudgmentSummary:
    request_id: str
    decision: Literal["allow", "defer", "stop"]
    risk_level: Literal["low", "medium", "high"]
    hard_block: bool
    human_review_required: bool
    reasoning: str
    precept_violations: tuple[PreceptViolation, ...]
```

### JudgmentResult（摘要 + 报告）

```python
@dataclass
class JudgmentResult:
    summary: JudgmentSummary  # 机器友好
    report: dict              # 人工可读完整报告
```

## 更多示例

参见 `docs/sdk_examples.py`。
