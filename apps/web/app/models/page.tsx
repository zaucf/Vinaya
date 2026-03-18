"use client";

import { useState } from "react";
import { LLMProvidersTab } from "./llm-providers-tab";
import { RequestModelsTab } from "./request-models-tab";

export default function ModelsPage() {
  const [activeTab, setActiveTab] = useState<"providers" | "models">("providers");

  return (
    <main>
      <div className="header">
        <div>
          <div className="kicker">Vinaya Configuration</div>
          <h1>配置中心</h1>
          <p className="muted">管理 LLM 提供商和请求模型</p>
        </div>
      </div>

      <div className="tab-bar">
        <button
          className={`tab-item ${activeTab === "providers" ? "active" : ""}`}
          onClick={() => setActiveTab("providers")}
        >
          LLM 提供商
        </button>
        <button
          className={`tab-item ${activeTab === "models" ? "active" : ""}`}
          onClick={() => setActiveTab("models")}
        >
          请求模型
        </button>
      </div>

      {activeTab === "providers" ? <LLMProvidersTab /> : <RequestModelsTab />}
    </main>
  );
}
