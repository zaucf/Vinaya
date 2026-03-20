"""Vinaya 远程 HTTP 客户端。

连接到 Vinaya API 服务器，通过 HTTP 调用判断功能。
零外部依赖，仅使用标准库。
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection, HTTPSConnection
from urllib import error, request
from urllib.parse import urljoin, urlparse

from vinaya.types import (
    Decision,
    JudgmentResult,
    JudgmentSummary,
    ReviewResult,
    RiskLevel,
    StageEvent,
)


class VinayaClientError(RuntimeError):
    """Vinaya 客户端错误。"""


class VinayaClient:
    """Vinaya 远程 HTTP 客户端。

    Example:
        >>> client = VinayaClient(base_url="http://localhost:8000")
        >>> client.health()  # 检查服务状态
        >>> result = client.judge(
        ...     title="测试请求",
        ...     request_text="请帮我生成一个...",
        ...     domain="code",
        ...     risk_level="medium"
        ... )
        >>> print(result.summary.decision)  # 'allow', 'defer', or 'stop'
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 120):
        """初始化客户端。

        Args:
            base_url: API 服务器地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _http_request(
        self,
        path: str,
        method: str = "GET",
        body: dict | None = None,
    ) -> dict:
        """发送 HTTP 请求。"""
        url = urljoin(self.base_url, path)

        headers = {"Content-Type": "application/json"}
        data = None
        if body:
            data = json.dumps(body).encode("utf-8")

        req = request.Request(url, data=data, headers=headers, method=method)

        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VinayaClientError(f"HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise VinayaClientError(f"Connection failed: {exc}") from exc

    def health(self) -> bool:
        """检查服务健康状态。

        Returns:
            服务是否正常
        """
        try:
            result = self._http_request("/health")
            return result.get("ok", False)
        except VinayaClientError:
            return False

    def judge(
        self,
        *,
        title: str,
        request_text: str,
        domain: str,
        risk_level: RiskLevel,
        context: str = "",
        request_model_id: str | None = None,
    ) -> JudgmentResult:
        """执行判断请求。

        Args:
            title: 请求标题
            request_text: 请求文本
            domain: 领域
            risk_level: 风险等级
            context: 额外上下文
            request_model_id: 请求模型 ID（可选）

        Returns:
            判断结果，包含摘要和完整报告

        Raises:
            VinayaClientError: 请求失败
        """
        payload = {
            "title": title,
            "request_text": request_text,
            "domain": domain,
            "risk_level": risk_level,
            "context": context,
            "request_model_id": request_model_id,
        }

        response = self._http_request("/api/requests", method="POST", body=payload)
        request_id = response.get("request_id", "")
        report = response.get("report", {})

        return JudgmentResult.from_report(request_id, report)

    def get_report(self, request_id: str) -> JudgmentResult | None:
        """获取已有的判断报告。

        Args:
            request_id: 请求 ID

        Returns:
            判断结果，如果不存在则返回 None
        """
        try:
            response = self._http_request(f"/api/requests/{request_id}")
            request_id = response.get("request_id", "")
            report = response.get("report", {})
            return JudgmentResult.from_report(request_id, report)
        except VinayaClientError:
            return None

    def list_requests(
        self,
        limit: int = 100,
    ) -> list[dict]:
        """列出判断请求列表。

        Args:
            limit: 返回数量限制

        Returns:
            请求列表
        """
        response = self._http_request(f"/api/requests?limit={limit}")
        return response.get("items", [])

    def judge_stream(
        self,
        *,
        on_stage: "Callable[[StageEvent], None] | None" = None,
        title: str,
        request_text: str,
        domain: str,
        risk_level: RiskLevel,
        context: str = "",
        request_model_id: str | None = None,
    ) -> JudgmentResult:
        """流式执行判断请求，通过回调接收阶段事件。

        Args:
            on_stage: 阶段事件回调函数
            title: 请求标题
            request_text: 请求文本
            domain: 领域
            risk_level: 风险等级
            context: 额外上下文
            request_model_id: 请求模型 ID（可选）

        Returns:
            判断结果
        """
        from collections.abc import Callable

        payload = json.dumps({
            "title": title,
            "request_text": request_text,
            "domain": domain,
            "risk_level": risk_level,
            "context": context,
            "request_model_id": request_model_id,
        }).encode("utf-8")

        parsed = urlparse(self.base_url)
        ConnClass = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        conn = ConnClass(host, port, timeout=self.timeout)
        try:
            conn.request(
                "POST",
                "/api/requests/stream",
                body=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = conn.getresponse()
            if resp.status != 200:
                body = resp.read().decode("utf-8", errors="replace")
                raise VinayaClientError(f"HTTP {resp.status}: {body}")

            buffer = ""
            final_data = None

            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    if not block.strip():
                        continue

                    event_type = "message"
                    data_str = ""
                    for line in block.split("\n"):
                        if line.startswith("event: "):
                            event_type = line[7:]
                        elif line.startswith("data: "):
                            data_str = line[6:]

                    if not data_str:
                        continue

                    data = json.loads(data_str)
                    stage_event = StageEvent(
                        event_type=event_type,
                        stage=data.get("stage"),
                        label=data.get("label"),
                        index=data.get("index"),
                        total=data.get("total"),
                        result=data.get("result"),
                        message=data.get("message"),
                    )

                    if on_stage is not None:
                        on_stage(stage_event)

                    if event_type == "done":
                        final_data = data
                    elif event_type == "error":
                        raise VinayaClientError(data.get("message", "Unknown error"))
        finally:
            conn.close()

        if final_data is None:
            raise VinayaClientError("Stream ended without done event")

        request_id = final_data.get("request_id", "")
        report = final_data.get("report", {})
        return JudgmentResult.from_report(request_id, report)

    def judge_batch(
        self,
        requests: list[dict],
        max_workers: int = 4,
    ) -> list[JudgmentResult]:
        """批量执行判断请求。

        Args:
            requests: 判断请求参数列表，每项为 judge() 的关键字参数
            max_workers: 最大并发数

        Returns:
            判断结果列表（与输入顺序一致）
        """
        def _run_one(params: dict) -> JudgmentResult:
            return self.judge(**params)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(_run_one, req) for req in requests]
            return [f.result() for f in futures]

    def submit_review(
        self,
        request_id: str,
        *,
        reviewer: str,
        result: str,
        comment: str,
    ) -> ReviewResult:
        """提交人工复核。

        Args:
            request_id: 请求 ID
            reviewer: 复核人
            result: 复核结果（maintain / revise / override）
            comment: 复核评语

        Returns:
            复核结果
        """
        payload = {
            "reviewer": reviewer,
            "result": result,
            "comment": comment,
        }
        response = self._http_request(
            f"/api/requests/{request_id}/review",
            method="POST",
            body=payload,
        )
        return ReviewResult(
            review_id=response.get("review_id", ""),
            request_id=response.get("request_id", request_id),
            reviewer=response.get("reviewer", reviewer),
            result=response.get("result", result),
            comment=response.get("comment", comment),
            created_at=response.get("created_at", ""),
        )
