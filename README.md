# Vinaya

Vinaya 是一个以戒、定、慧为核心的 AI 判断净化系统。

它不是让 AI 更快决定，而是让 AI 更少犯业。

Vinaya 的职责是在“请求”与“执行”之间插入一层净化流程，使每一个高影响判断都先经历发心、观缘、持戒、辩义、缓行与回向，再决定是否进入执行。

## 工程结构

当前仓库采用 `前端 Next.js + 后端 Python FastAPI + Python 引擎包` 的结构，参考了 edict 在系统分层与 Python 后端路线上的优点，但保留 Vinaya 自己的判断净化主线。

- `apps/web`：前端 Web 看板与原型页面
- `apps/api`：Python FastAPI 服务
- `packages/engine/vinaya_engine`：Vinaya 核心判断净化引擎（Python）
- `docs`：项目宪章、架构、PRD
- `pyproject.toml`：Python 依赖与运行入口说明

## 核心理念

- 先净化判断，再允许执行
- 先问动机，再问方案
- 先看因缘，再下结论
- 先守戒律，再求方便
- 先缓后断，先试后放
- 先记后改，不掩过失

## 三类结论

Vinaya 不输出绝对裁定，只输出三类建议：

- `allow`：可行
- `defer`：缓行
- `stop`：止行

其中 `defer` 不是失败，而是系统克制能力的体现。

## 六阶段流程

- 发心：识别真实目标、受益者、代价承担者和混杂动机
- 观缘：分析近因、远因、深层因和外溢后果
- 持戒：依据五戒检查是否越界、伤害或妄断
- 辩义：生成更低伤害、更可回退的备选路径
- 缓行：优先试行、限权、灰度和人工复核
- 回向：记录因果链、执行结果、误伤和修订建议

## 文档

- `docs/vinaya-charter-v0.1.md`：项目宪章
- `docs/vinaya-architecture-v0.1.md`：系统架构与模块设计
- `docs/vinaya-mvp-prd-v0.1.md`：MVP 产品需求文档

## 启动方式

### 大模型配置

默认情况下，Vinaya 现在会优先调用大模型生成六阶段结构化判断，而不是使用纯模板规则。

启动前请先配置以下环境变量：

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:VINAYA_LLM_MODEL="gpt-4o-mini"
```

可选项：

```powershell
$env:VINAYA_LLM_BASE_URL="https://api.openai.com/v1/chat/completions"
$env:VINAYA_LLM_TEMPERATURE="0.2"
$env:VINAYA_LLM_TIMEOUT="60"
```

如果你想临时退回旧的规则引擎，可设置：

```powershell
$env:VINAYA_USE_MOCK_ENGINE="true"
```

安装前端依赖：

```bash
npm install
```

安装 Python 依赖：

```bash
python -m pip install -e .
```

启动 Python API：

```bash
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 4010
```

如果提示 `WinError 10048`，说明 4010 端口已被旧进程占用。可先查 PID：

```powershell
Get-NetTCPConnection -LocalPort 4010 | Select-Object LocalAddress, LocalPort, State, OwningProcess
```

再按 PID 结束旧进程：

```powershell
Stop-Process -Id <PID>
```

启动前端：

```bash
npm run dev
```

默认前端地址：

```text
http://127.0.0.1:3000
```

默认后端地址：

```text
http://127.0.0.1:4010
```

构建前端：

```bash
npm run build
```

## 当前版本目标

第一版重点不是复杂多 Agent 编排，而是：

- 单请求判断净化闭环
- 五阶段串行处理器
- 三类结论输出
- 因果簿记录
- 人工复核入口
- 基础 Web 界面
- 后端服务骨架
- JSON 文件持久化存储

## 下一步

按顺序推进：

1. 增加人工复核入口与复核记录
2. 为详情页补充找不到请求与 API 异常处理
3. 逐步把 JSON 持久化升级为更稳的存储方案
4. 完善规则中心与缓行策略配置
5. 构建基础看板与规则页
