"""Vinaya 远程 HTTP 客户端。

连接到 Vinaya API 服务器，通过 HTTP 调用判断功能。
零外部依赖，仅使用标准库。
"""

from __future__ import annotations

import json
from urllib import error, request
from urllib.parse import urljoin

from vinaya.types import Decision, JudgmentResult, JudgmentSummary, RiskLevel


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
