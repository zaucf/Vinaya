import { RequestForm } from "./request-form";
import { NavBar } from "./nav-bar";

const principles = [
  "先净化判断，再允许执行",
  "先问动机，再问方案",
  "先看因缘，再下结论",
  "先守戒律，再求方便",
  "先缓后断，先试后放",
  "先记后改，不掩过失",
];

const stages = ["发心", "观缘", "持戒", "辩义", "缓行", "回向"];

const outputs = [
  {
    key: "allow",
    label: "可行",
    note: "满足基本戒律要求，风险可控，可在限定范围推进。",
  },
  {
    key: "defer",
    label: "缓行",
    note: "默认克制性输出，需要试行、限权或人工复核。",
  },
  { key: "stop", label: "止行", note: "触碰红线或会造成明显不可回退伤害。" },
];

export default function HomePage() {
  return (
    <main>
      <NavBar />

      <div className="hero">
        <h1>在 AI 失控之前，拦住它。</h1>
        <p className="muted">
          Vinaya 在每一次 AI 决策前植入六阶段戒律审查——不让冲动穿越防线，让每一步都经得起因果回溯。
        </p>
      </div>

      <section style={{ marginBottom: 24 }}>
        <RequestForm />
      </section>

      <section className="grid three">
        <article className="card">
          <h2 className="section-title">核心信条</h2>
          <ul className="list">
            {principles.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">六阶段流程</h2>
          <div>
            {stages.map((stage) => (
              <span className="pill" key={stage}>
                {stage}
              </span>
            ))}
          </div>
          <p className="muted" style={{ marginTop: 16 }}>
            每个请求都将按序经过六阶段净化流程，逐层过滤风险与冲动。
          </p>
        </article>

        <article className="card">
          <h2 className="section-title">三类结论</h2>
          <div>
            {outputs.map((item) => (
              <div key={item.key} style={{ marginBottom: 12 }}>
                <span className={`pill ${item.key}`}>{item.label}</span>
                <p className="muted" style={{ marginTop: 8 }}>
                  {item.note}
                </p>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid two" style={{ marginTop: 16 }}>
        <article className="card">
          <h2 className="section-title">当前文档</h2>
          <ul className="list">
            <li>`docs/vinaya-charter-v0.1.md`</li>
            <li>`docs/vinaya-architecture-v0.1.md`</li>
            <li>`docs/vinaya-mvp-prd-v0.1.md`</li>
          </ul>
        </article>

        <article className="card">
          <h2 className="section-title">当前链路</h2>
          <ul className="list">
            <li>
              <a href="/dashboard">判断看板查看系统克制能力指标</a>
            </li>
            <li>首页表单提交到 Python FastAPI</li>
            <li>FastAPI 调用 Python 引擎生成判断报告</li>
            <li>详情页按 request id 拉取并展示报告</li>
            <li>
              <a href="/requests">历史页查看持久化请求列表</a>
            </li>
            <li>
              <a href="/models">请求模型中心管理动态配置</a>
            </li>
            <li>
              <a href="/rules">规则说明页查看五戒与人工主权边界</a>
            </li>
          </ul>
        </article>
      </section>
    </main>
  );
}
