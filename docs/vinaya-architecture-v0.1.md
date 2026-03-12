# Vinaya 系统架构与模块设计 v0.1

## 一、目标

Vinaya 不是一个追求快速放行请求的通用工作流系统，而是一个将 AI 判断先净化、再执行的决策中间层。系统目标是：

- 在请求进入执行前完成动机、因缘、戒律、伤害与风险检查
- 让“缓行”成为核心结果，而不是异常分支
- 为高影响任务建立可审计、可回退、可人工接管的治理流程
- 通过因果记录与补赎机制持续修正系统行为

## 二、总体架构

Vinaya 建议采用六层结构：

- 接入层
- 净化编排层
- 判断执行层
- 治理与审计层
- 存储层
- 运营与看板层

逻辑流如下：

1. 用户或外部系统提交请求
2. 接入层完成标准化、分类和风险预标记
3. 净化编排层依次运行发心、观缘、持戒、辩义、缓行
4. 判断执行层根据结论决定放行、试行、止行或升级人工
5. 治理与审计层记录全过程，并在错误后触发补赎
6. 运营与看板层展示当前状态、风险分布、缓行任务和因果簿

## 三、核心模块

## 1. 接入层

职责：

- 接收用户请求、系统事件或第三方平台输入
- 将自然语言请求转为结构化请求对象
- 提取上下文、影响范围、敏感性和请求来源
- 进行基础风险预分类

建议子模块：

- Request Gateway：统一 API / Webhook / UI 入口
- Intent Normalizer：请求标准化与字段清洗
- Risk Pre-Classifier：基础风险等级判断
- Context Resolver：补充历史记录、角色、权限和环境信息

输出对象建议：

```json
{
  "requestId": "vinaya-req-001",
  "source": "web-ui",
  "requestText": "是否对该用户做永久封禁",
  "actor": "moderator-12",
  "target": ["user-8848"],
  "domain": "content-moderation",
  "preRisk": "high",
  "contextRefs": ["case-1201", "policy-9"]
}
```

## 2. 净化编排层

这是 Vinaya 的核心。它不是普通任务调度器，而是判断净化状态机。

建议状态顺序：

- intake
- intention
- causality
- precepts
- deliberation
- gradual-release
- decision
- dedication
- archived

其中最重要的五个核心处理器如下。

### 2.1 发心引擎 Intention Engine

职责：

- 识别请求想达成的真实目标
- 判断是否存在求快、逐利、避责、控制欲、报复性等杂染动机
- 标记利益获得者和代价承担者

输入：

- 结构化请求
- 操作者身份
- 历史相似案例

输出：

```json
{
  "primaryIntent": "降低社区违规内容扩散",
  "mixedMotives": ["节省审核成本", "快速给举报方交代"],
  "beneficiaries": ["平台秩序", "多数用户"],
  "costBearers": ["被处理用户"],
  "intentionRisk": "medium"
}
```

### 2.2 观缘引擎 Causality Mapper

职责：

- 分析近因、远因、表层因、深层因
- 建立影响链和外溢后果图
- 判断是否属于治标不治本

建议能力：

- 规则模板 + LLM 推理混合
- 因果节点抽取
- 脆弱对象识别
- 长期后果假设生成

输出：

```json
{
  "proximateCauses": ["多次被举报", "触发敏感词规则"],
  "rootCauses": ["误伤规则过宽", "申诉流程慢"],
  "affectedParties": ["目标用户", "审核团队", "社区旁观者"],
  "externalities": ["误封争议扩大", "平台公信力下降"],
  "causalityRisk": "high"
}
```

### 2.3 持戒引擎 Precept Guard

职责：

- 依据 Vinaya 五戒做硬约束判断
- 对高风险请求给出越戒标签
- 决定是否直接止行或强制人工升级

规则检查维度：

- 不妄语：信息不足却做确定判断
- 不害生：有明显可预见伤害
- 不偷夺：剥夺申诉、解释或资源机会
- 不越界：超出授权场景和权限
- 不昏乱：证据不足、上下文不全、情境混乱

输出：

```json
{
  "preceptFindings": [
    {"name": "不害生", "status": "warning", "reason": "永久封禁不可逆且影响重大"},
    {"name": "不偷夺", "status": "warning", "reason": "当前无明确申诉窗口"}
  ],
  "hardBlock": false,
  "escalateToHuman": true,
  "preceptRisk": "high"
}
```

### 2.4 辩义引擎 Compassion Council

职责：

- 组织多视角辩论
- 不寻找“最强动作”，而寻找“最净路径”
- 给出替代方案和低伤害方案

建议最小角色集：

- 观者：分析结构与因缘
- 戒者：检查规则红线与越界风险
- 悲者：评估痛苦、误伤、脆弱群体影响
- 行者：设计可试行、可回退的执行路径
- 记者：记录分歧、不确定性与决策依据

输出：

```json
{
  "options": [
    {"name": "直接永久封禁", "score": 0.22},
    {"name": "限期冻结并人工复核", "score": 0.81},
    {"name": "先限制部分功能并开放申诉", "score": 0.88}
  ],
  "preferredOption": "先限制部分功能并开放申诉",
  "dissentNotes": ["证据链仍不完整，不宜立即永久处理"],
  "deliberationRisk": "medium"
}
```

### 2.5 缓行引擎 Gradual Release Engine

职责：

- 将强动作转为分阶段、限权、可回退策略
- 让“缓行”成为默认选项
- 生成试行计划、观察期和止损条件

核心能力：

- 风险转译：从裁决型动作转为试行型动作
- 灰度策略生成
- 升级阈值定义
- 回退计划生成

输出：

```json
{
  "mode": "defer",
  "trialPlan": {
    "action": "限制发布 72 小时",
    "scope": "仅高风险功能",
    "reviewAt": "2026-03-14T09:00:00Z",
    "rollbackCondition": "若申诉成立或证据不足则立即恢复",
    "humanOwner": "moderation-lead-3"
  },
  "releaseRisk": "medium"
}
```

## 3. 判断执行层

职责：

- 将净化后的结论转换为系统动作
- 管理放行、缓行、止行、人工升级
- 确保所有动作可撤销、可记录

建议子模块：

- Decision Resolver：汇总所有净化结果，给出最终判定
- Action Dispatcher：触发外部系统动作或生成待办
- Human Escalation Queue：高风险人工审批队列
- Rollback Controller：执行回退与恢复

最终结论仅允许三类：

- allow：可行
- defer：缓行
- stop：止行

建议输出协议：

```json
{
  "decision": "defer",
  "reasoningSummary": "存在不可逆风险与申诉缺口，应先限期限制并人工复核",
  "requiredActions": ["create-human-review", "apply-temporary-restriction"],
  "expiry": "2026-03-14T09:00:00Z",
  "rollbackEnabled": true
}
```

## 4. 治理与审计层

职责：

- 记录判断链、因果链、执行链
- 管理补赎流程
- 为后续规则修订提供依据

建议子模块：

- Karma Ledger：因果簿，记录每次重要判断
- Confession Handler：错误后的复盘与补赎触发器
- Policy Registry：戒律、规则、风险模板配置中心
- Case Library：案例库，供观缘与辩义引用

补赎触发条件建议：

- 用户申诉成功
- 人工复核推翻系统建议
- 执行动作产生明显误伤
- 某类错误连续发生超过阈值

补赎动作建议：

- 降低自动化级别
- 强化相应规则
- 更新提示词或模板
- 新增人工必审条件
- 写入案例警示

## 5. 存储层

建议至少包含以下存储结构：

- Requests：原始请求与上下文
- Judgments：各阶段判断结果
- Policies：戒律、规则、阈值配置
- Cases：历史案例与申诉结果
- Actions：实际执行动作与回退记录
- Audits：审计日志与人工干预记录

如果快速起步，可采用：

- SQLite 或 PostgreSQL 存元数据
- JSONL 存逐步判断轨迹
- 对象存储保存附件与原始证据

## 6. 运营与看板层

看板不是为了“炫酷监控”，而是为了显示系统如何克制。

建议看板重点展示：

- 当前请求所处分阶段
- 风险等级分布
- 被缓行的任务数量
- 被止行的任务原因
- 高频触发的戒律警告
- 申诉成功率与误伤率
- 人工接管比例
- 补赎触发记录

建议核心页面：

- Judgment Board：判断看板
- Risk Monitor：风险分布与趋势
- Karma Ledger：因果簿
- Confession Console：补赎与复盘台
- Policy Center：戒律与规则中心
- Case Library：案例库

## 四、状态机设计

建议状态流转：

- `submitted`：请求已提交
- `normalized`：请求已标准化
- `intention_reviewed`：完成发心
- `causality_reviewed`：完成观缘
- `precepts_reviewed`：完成持戒
- `deliberated`：完成辩义
- `deferred`：进入缓行或试行
- `allowed`：可行并放行
- `stopped`：止行
- `escalated`：升级人工
- `executed`：已执行
- `rolled_back`：已回退
- `dedicated`：完成回向记录
- `archived`：归档完成

关键规则：

- 高风险请求不能从 `submitted` 直接进入 `allowed`
- 触发硬性越戒时必须进入 `stopped` 或 `escalated`
- 进入 `executed` 的任务必须具备对应审计记录
- 回退后仍需进入 `dedicated`，不能直接归档

## 五、角色设计

系统中建议存在两类角色：系统角色与人工角色。

### 系统角色

- 观者：负责因缘分析
- 戒者：负责红线审查
- 悲者：负责伤害与脆弱群体评估
- 行者：负责低伤害执行路径设计
- 记者：负责记录、归纳和不确定性标注

### 人工角色

- 守戒人：审批高风险或越戒事项
- 复核人：在缓行期或争议案件中复查判断
- 纠偏人：在误伤发生后决定补救与规则更新
- 管理员：维护政策中心和风险阈值

## 六、接口与协议建议

最小 API 集可包括：

- `POST /api/requests`：提交判断请求
- `GET /api/requests/{id}`：查看当前状态
- `GET /api/requests/{id}/ledger`：查看因果簿
- `POST /api/requests/{id}/review`：人工复核
- `POST /api/requests/{id}/rollback`：回退动作
- `GET /api/policies`：获取戒律与规则
- `POST /api/policies`：更新规则
- `GET /api/cases`：查询案例库
- `POST /api/confessions`：记录补赎事件

统一输出中应保留以下字段：

- requestId
- riskLevel
- decision
- confidence
- uncertaintyNotes
- preceptAlerts
- humanReviewRequired
- rollbackEnabled
- ledgerRef

## 七、MVP 建议范围

第一版只做最核心闭环，不做复杂生态。

建议 MVP 包含：

- 一个 Web 表单或简单前端
- 单请求净化流程
- 五个核心处理器的串行运行
- 三类结论输出：可行 / 缓行 / 止行
- 因果簿落库与查看
- 人工复核入口
- 一个基础看板

第一版不做：

- 复杂多租户体系
- 多团队协作编排
- 大量第三方集成
- 自动学习与自我改写规则
- 复杂实时消息总线

## 八、技术实现建议

如果追求快速起步，建议技术栈简化为：

- 前端：Next.js 或 React
- 后端：FastAPI 或 Node.js + NestJS
- 存储：PostgreSQL + JSONB
- 队列：可先不引入，串行处理即可
- LLM 调用：统一封装 Provider Gateway
- 审计：数据库主存 + JSONL 附加日志

如果参考 edict 的优点，可以借鉴：

- 完整状态流转可视化
- 审计与时间线展示
- 人工干预能力
- 角色明确分工

但应避免直接照搬：

- 朝廷角色命名
- 任务导向优先于判断导向
- 偏执行编排而非判断净化

## 九、成功标准

Vinaya 的第一阶段成功，不以“自动执行更多任务”为标志，而以以下指标衡量：

- 高风险请求中“缓行”比例是否合理
- 人工复核推翻率是否下降
- 明显误伤率是否下降
- 不确定性表达是否更充分
- 回退机制是否真正可用
- 因果记录是否能支撑规则修订

一句话说，Vinaya 成功的标志不是更敢判断，而是更会克制。
