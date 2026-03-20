# Vinaya

Vinaya 是一个以**戒、定、慧**为核心的 AI 判断净化系统。

它不是让 AI 更快决定，而是让 AI 更少犯业。

- **戒**：五戒红线——不妄语、不害生、不偷夺、不越界、不昏乱，为判断划定不可逾越的底线
- **定**：克制与缓行——高影响判断默认不直接全量执行，"缓行"是成熟系统的能力而非失败
- **慧**：判断净化——在"请求"与"执行"之间插入六阶段净化流程（发心、观缘、持戒、辩义、缓行、回向），让每一次重要判断都经过观照再决定是否进入执行

## 快速启动

### 1. 环境要求

- Python >= 3.11
- Node.js >= 18
- pnpm >= 10
- 一个 OpenAI 兼容的 LLM API Key

### 2. 安装依赖

```bash
# 安装前端依赖（项目根目录执行，monorepo 会自动解析 workspace 包）
pnpm install

# 安装 Python 依赖
python -m pip install -e .
```

### 3. 配置 LLM

默认通过 Web 界面（`/models` 页面）管理 LLM 提供商。也可在启动前通过环境变量配置：

```bash
# Linux / macOS
export OPENAI_API_KEY="your_api_key"

# Windows PowerShell
$env:OPENAI_API_KEY="your_api_key"
```

首次启动时会自动创建一个 OpenAI 默认提供商（gpt-4o-mini），可在 `/models` 页面修改为任意 OpenAI 兼容 API（DeepSeek、Ollama、Azure 等）。

如果想不接 LLM，用规则引擎生成模拟数据：

```bash
export VINAYA_USE_MOCK_ENGINE="true"
```

### 4. 启动服务

需要两个终端分别启动前后端：

**终端 1 — 启动后端 API（端口 4010）：**

```bash
# 在项目根目录执行
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 4010
```

**终端 2 — 启动前端（端口 3000）：**

```bash
# 在项目根目录执行
cd apps/web
pnpm dev
```

验证启动成功：

```bash
# 后端健康检查
curl http://127.0.0.1:4010/health
# 返回 {"ok":true,"service":"vinaya-api"}
```

打开浏览器访问 `http://127.0.0.1:3000`。

### 5. 存储后端（可选）

默认使用 JSON 文件存储（`data/` 目录）。切换到 SQLite：

```bash
# 迁移现有数据
python apps/api/migrate_to_sqlite.py

# 启用 SQLite
export VINAYA_USE_SQLITE="true"
```

## 工程结构

```
vinaya/
├── apps/
│   ├── web/                    # Next.js 15 前端
│   │   └── app/
│   │       ├── page.tsx            # 首页 + 请求提交
│   │       ├── dashboard/          # 判断看板
│   │       ├── requests/           # 请求列表 + 详情 + 复核
│   │       ├── ledger/             # 因果簿
│   │       ├── rules/              # 规则与策略配置
│   │       └── models/             # LLM 提供商 + 请求模型管理
│   └── api/                    # Python FastAPI 后端
│       ├── main.py                 # API 入口与路由
│       ├── migrate_to_sqlite.py    # 数据迁移脚本
│       └── vinaya_api/
│           ├── schemas.py          # Pydantic 数据模型
│           ├── repository.py       # 存储路由层（JSON / SQLite）
│           ├── repository_json.py  # JSON 文件存储实现
│           ├── repository_sqlite.py # SQLite 存储实现
│           ├── llm.py              # LLM 调用封装
│           └── services/           # 业务逻辑
├── packages/
│   └── engine/
│       └── vinaya_engine/      # 核心判断净化引擎
│           ├── llm_pipeline.py     # LLM 驱动的六阶段引擎
│           ├── pipeline.py         # 规则驱动的六阶段引擎（Mock）
│           └── types.py            # TypedDict 类型定义
├── data/                       # 持久化数据目录
├── docs/                       # 项目文档
└── pyproject.toml              # Python 项目配置
```

## 核心概念

### 六阶段净化流程

1. **发心**：识别真实目标、受益者、代价承担者和混杂动机
2. **观缘**：分析近因、远因、深层因和外溢后果
3. **持戒**：依据五戒检查是否越界、伤害或妄断
4. **辩义**：生成更低伤害、更可回退的备选路径
5. **缓行**：优先试行、限权、灰度和人工复核
6. **回向**：记录因果链、执行结果和修订建议

### 三类结论

- `allow`：可行，风险可控，可在限定范围推进
- `defer`：缓行，需要补信息、试行或人工复核（这不是失败，是克制）
- `stop`：止行，已触碰红线或风险不可接受

### 五戒

- **不妄语**：不把不确定性伪装成确定性
- **不害生**：不为效率制造明显伤害
- **不偷夺**：不剥夺机会、资源和申诉空间
- **不越界**：不超出系统授权边界
- **不昏乱**：证据不足时不做强判

## 页面一览

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 项目介绍 + 判断请求提交表单 |
| 判断看板 | `/dashboard` | 总量统计、缓行比例、复核率、推翻率 |
| 历史请求 | `/requests` | 请求列表 + 搜索筛选 |
| 请求详情 | `/requests/{id}` | 六阶段展示 + 人工复核 |
| 因果簿 | `/ledger/{id}` | 完整判断链的结构化展示 |
| 规则中心 | `/rules` | 五戒配置 + 缓行策略 + 风险阈值 |
| 配置中心 | `/models` | 请求模型 + LLM 提供商管理 |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/requests` | GET | 请求历史列表 |
| `/api/requests` | POST | 提交判断请求 |
| `/api/requests/{id}` | GET | 请求详情 |
| `/api/requests/{id}/review` | POST | 提交人工复核 |
| `/api/requests/{id}/reviews` | GET | 复核历史列表 |
| `/api/rules` | GET/PUT | 规则配置 |
| `/api/request-models` | CRUD | 请求模型管理 |
| `/api/llm-providers` | CRUD | LLM 提供商管理 |
| `/api/llm-providers/{id}/test` | POST | 连接测试 |

## 文档

- `docs/vinaya-charter-v0.1.md`：项目宪章——定位、使命、五戒、核心原则
- `docs/vinaya-architecture-v0.1.md`：系统架构——六层结构、状态机、角色设计、API 协议
- `docs/vinaya-mvp-prd-v0.1.md`：MVP PRD——功能列表、验收标准、页面范围
- `docs/vinaya-status-v0.1.md`：项目现状——设计对照、已完成功能、偏离分析、后续方向
- `docs/sdk_examples.py`：SDK 使用示例代码

## Python SDK

Vinaya 提供 Python SDK，支持两种使用方式：

### 安装

```bash
# 仅安装 SDK（零依赖）
pip install -e .

# 安装 SDK + API 服务器（包含 FastAPI 等依赖）
pip install -e ".[server]"
```

### 使用方式

#### 1. 远程模式（HTTP 客户端）

连接到已部署的 Vinaya API 服务器：

```python
from vinaya import VinayaClient

client = VinayaClient(base_url="http://localhost:4010")

# 执行判断
result = client.judge(
    title="代码生成请求",
    request_text="请帮我生成一个 Python 斐波那契函数",
    domain="code",
    risk_level="low",
)

# 读取机器友好的摘要
print(result.summary.decision)  # 'allow', 'defer', or 'stop'
print(result.summary.risk_level)  # 'low', 'medium', or 'high'
print(result.summary.hard_block)  # True/False
print(result.summary.reasoning)

# 检查戒律违规
for violation in result.summary.precept_violations:
    print(f"- {violation.name}: {violation.status}")
```

#### 2. 本地模式（直接调用）

嵌入到你的 AI 系统中，无需 HTTP 服务器：

```python
from vinaya import VinayaLocalClient

# Mock 模式（测试/开发用）
client = VinayaLocalClient(use_mock=True)
result = client.judge(
    title="测试请求",
    request_text="测试内容",
    domain="test",
    risk_level="low",
)

# 真实 LLM 模式
from my_llm import my_chat_json
from my_rules import get_rules

client = VinayaLocalClient(
    chat_fn=my_chat_json,
    rules_provider=get_rules,
)
result = client.judge(...)
```

#### 3. AI 网关集成

```python
from vinaya import VinayaLocalClient

vinaya = VinayaLocalClient(use_mock=True)

def handle_user_request(user_input: str) -> str:
    """处理用户请求的决策网关。"""
    result = vinaya.judge(
        title="用户请求",
        request_text=user_input,
        domain="general",
        risk_level="medium",
    )

    if result.summary.decision == "allow":
        return execute_request(user_input)
    elif result.summary.decision == "defer":
        return f"请求需要进一步审查：{result.summary.reasoning}"
    else:  # stop
        return f"请求被拒绝：{result.summary.reasoning}"
```

### 数据结构

```python
from vinaya import JudgmentResult, JudgmentSummary, Decision, RiskLevel

# JudgmentSummary（机器友好）
@dataclass
class JudgmentSummary:
    request_id: str
    decision: Decision  # 'allow' | 'defer' | 'stop'
    risk_level: RiskLevel  # 'low' | 'medium' | 'high'
    hard_block: bool
    human_review_required: bool
    reasoning: str
    precept_violations: tuple[PreceptViolation, ...]

# JudgmentResult（摘要 + 完整报告）
@dataclass
class JudgmentResult:
    summary: JudgmentSummary  # AI 系统读取
    report: dict              # 人工查看
```

更多示例参见 `docs/sdk_examples.py`。

### SDK 当前限制与计划增强

当前 SDK 已满足基本集成需求，以下是已识别的增强方向：

| 能力 | 现状 | 计划 |
|------|------|------|
| 异步调用 | 仅同步 `judge()` | 增加 `AsyncVinayaClient` 和 `async judge()` |
| 流式推送 | API 支持 SSE，SDK 未暴露 | 增加 `judge_stream()` 逐阶段回调 |
| 批量判断 | 不支持 | 增加 `judge_batch()` 并发处理 |
| 复核 API | 仅 Web 界面可操作 | SDK 增加 `submit_review()` |
| 装饰器模式 | 不支持 | 增加 `@vinaya.guard()` 函数守卫 |
| 框架中间件 | 不支持 | 提供 FastAPI / Django 中间件 |

#### 装饰器模式（计划中）

```python
from vinaya import VinayaLocalClient

vinaya = VinayaLocalClient(use_mock=True)

@vinaya.guard(domain="finance-approval", risk_level="high")
def approve_large_payment(amount: float, recipient: str) -> dict:
    """只有通过 Vinaya 判断的请求才会真正执行。"""
    return {"status": "approved", "amount": amount, "to": recipient}

# 调用时自动触发判断，defer/stop 会抛出异常或返回拦截结果
result = approve_large_payment(50000, "vendor-abc")
```

#### 流式推送（计划中）

```python
client = VinayaClient(base_url="http://localhost:4010")

# 逐阶段回调，适合实时 UI 或日志
def on_stage(stage: str, label: str, result: dict):
    print(f"[{label}] 完成")

result = client.judge_stream(
    title="高风险操作",
    request_text="批量删除用户数据",
    risk_level="high",
    on_stage=on_stage,
)
```

## 当前版本状态

MVP 核心验证目标已全部达成：

- ✅ 用户能提交判断请求并选择请求模型
- ✅ LLM 引擎完成六阶段净化分析
- ✅ 输出 allow / defer / stop 三类结论
- ✅ 自动生成因果簿并可独立查看
- ✅ 人工复核支持维持/修改/推翻，保留完整历史
- ✅ 判断看板展示系统克制能力指标
- ✅ 规则中心支持五戒、缓行策略和风险阈值配置
- ✅ LLM 提供商在线管理和连接测试
- ✅ 双存储后端（JSON / SQLite）可切换

详细的设计对照与偏离分析见 `docs/vinaya-status-v0.1.md`。

## 下一步

### P0 — 立即可做

1. **风险自动分类**：提交请求时自动预判风险等级，减少人工误判。一次轻量 LLM 预分类即可实现
2. **补赎 + 案例库**：人工推翻判断后，自动生成规则修订建议并写入案例库，形成"判断 → 复核 → 修正 → 进化"闭环

### P1 — 短期规划

3. **权限与多用户**：区分提交者与复核者身份，记录"谁提交、谁复核"，为审计链提供责任归属
4. **通知机制**：判断结果为 defer 或 stop 时，自动通知人工负责人介入复核
5. **导出与审计**：支持按时间范围导出完整判断链，满足合规审计需求

### P2 — 中期演进

6. **显式状态机**：让请求流转过程可观察、可暂停、可干预，支持在关键阶段等待人工确认后再继续
7. **辩义多角色拆分**：从单次 LLM 调用升级为多视角 Agent 对抗，提升辩义阶段的深度与可信度
8. **SDK 增强**：异步客户端、流式推送 `judge_stream()`、批量判断 `judge_batch()`、复核 API `submit_review()`、`@vinaya.guard()` 装饰器、FastAPI/Django 中间件
