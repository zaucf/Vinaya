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
- 一个 OpenAI 兼容的 LLM API Key

### 2. 安装依赖

```bash
# 安装前端依赖
npm install

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

```bash
# 启动后端 API（端口 4010）
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 4010

# 另开一个终端，启动前端（端口 3000）
npm run dev
```

或者用 npm 脚本：

```bash
npm run api:dev   # 启动后端
npm run dev       # 启动前端
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

1. 显式状态机：让请求流转过程可观察、可暂停、可干预
2. 补赎机制：人工推翻后触发规则修订建议和案例写入
3. 辩义多角色拆分：从单次 LLM 调用升级为多视角 Agent 对抗
4. 风险自动分类：根据请求内容自动预判风险等级
5. 回退与案例库：支持判断回退和历史案例积累
