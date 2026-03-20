"""Vinaya 异步客户端。

零外部依赖，使用 asyncio + http.client 实现异步操作。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse

from vinaya.types import (
    Decision,
    JudgmentResult,
    JudgmentSummary,
    ReviewResult,
    RiskLevel,
    StageEvent,
)

_DEFAULT_POOL = ThreadPoolExecutor(max_workers=4)


class AsyncVinayaClientError(RuntimeError):
    """异步客户端错误。"""


class AsyncVinayaClient:
    """Vinaya 异步客户端。

    零外部依赖，使用标准库 asyncio + http.client。

    Example:
        >>> import asyncio
        >>> from vinaya import AsyncVinayaClient
        >>> async def main():
        ...     client = AsyncVinayaClient(base_url="http://localhost:8000")
        ...     result = await client.judge(
        ...         title="测试", request_text="...",
        ...         domain="test", risk_level="medium",
        ...     )
        ...     print(result.summary.decision)
        >>> asyncio.run(main())
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _sync_http_request(
        self,
        path: str,
        method: str = "GET",
        body: dict | None = None,
    ) -> dict:
        """同步 HTTP 请求（在线程池中执行）。"""
        parsed = urlparse(self.base_url)
        ConnClass = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        conn = ConnClass(host, port, timeout=self.timeout)
        try:
            headers = {"Content-Type": "application/json"}
            data = json.dumps(body).encode("utf-8") if body else None
            conn.request(method, path, body=data, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read().decode("utf-8")
            if resp.status >= 400:
                raise AsyncVinayaClientError(f"HTTP {resp.status}: {resp_body}")
            return json.loads(resp_body)
        finally:
            conn.close()

    async def _http_request(
        self,
        path: str,
        method: str = "GET",
        body: dict | None = None,
    ) -> dict:
        """异步 HTTP 请求。"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _DEFAULT_POOL,
            self._sync_http_request,
            path,
            method,
            body,
        )

    async def health(self) -> bool:
        """检查服务健康状态。"""
        try:
            result = await self._http_request("/health")
            return result.get("ok", False)
        except AsyncVinayaClientError:
            return False

    async def judge(
        self,
        *,
        title: str,
        request_text: str,
        domain: str,
        risk_level: RiskLevel,
        context: str = "",
        request_model_id: str | None = None,
    ) -> JudgmentResult:
        """异步执行判断请求。"""
        payload = {
            "title": title,
            "request_text": request_text,
            "domain": domain,
            "risk_level": risk_level,
            "context": context,
            "request_model_id": request_model_id,
        }
        response = await self._http_request("/api/requests", method="POST", body=payload)
        request_id = response.get("request_id", "")
        report = response.get("report", {})
        return JudgmentResult.from_report(request_id, report)

    async def judge_stream(
        self,
        *,
        title: str,
        request_text: str,
        domain: str,
        risk_level: RiskLevel,
        context: str = "",
        request_model_id: str | None = None,
    ) -> AsyncIterator[StageEvent]:
        """异步流式判断，逐个 yield StageEvent。

        最后一个事件的 event_type 为 'done'，其 result 包含完整报告。
        """
        payload = json.dumps({
            "title": title,
            "request_text": request_text,
            "domain": domain,
            "risk_level": risk_level,
            "context": context,
            "request_model_id": request_model_id,
        }).encode("utf-8")

        def _stream_sync():
            """在线程中执行同步 SSE 读取，返回事件列表。"""
            parsed = urlparse(self.base_url)
            ConnClass = HTTPSConnection if parsed.scheme == "https" else HTTPConnection
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            conn = ConnClass(host, port, timeout=self.timeout)
            events = []
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
                    raise AsyncVinayaClientError(f"HTTP {resp.status}: {body}")

                buffer = ""
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
                        events.append((event_type, data))
            finally:
                conn.close()
            return events

        loop = asyncio.get_event_loop()
        events = await loop.run_in_executor(_DEFAULT_POOL, _stream_sync)

        for event_type, data in events:
            if event_type == "error":
                raise AsyncVinayaClientError(data.get("message", "Unknown error"))
            yield StageEvent(
                event_type=event_type,
                stage=data.get("stage"),
                label=data.get("label"),
                index=data.get("index"),
                total=data.get("total"),
                result=data.get("result") if event_type != "done" else data,
                message=data.get("message"),
            )

    async def judge_batch(
        self,
        requests: list[dict],
        max_workers: int = 4,
    ) -> list[JudgmentResult]:
        """异步批量判断。"""
        sem = asyncio.Semaphore(max_workers)

        async def _run_one(params: dict) -> JudgmentResult:
            async with sem:
                return await self.judge(**params)

        tasks = [asyncio.create_task(_run_one(req)) for req in requests]
        return await asyncio.gather(*tasks)

    async def submit_review(
        self,
        request_id: str,
        *,
        reviewer: str,
        result: str,
        comment: str,
    ) -> ReviewResult:
        """异步提交人工复核。"""
        payload = {
            "reviewer": reviewer,
            "result": result,
            "comment": comment,
        }
        response = await self._http_request(
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
