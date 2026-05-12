"""HydraFlow AI HTTP 客户端封装"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional, AsyncIterator
import httpx
from dataclasses import dataclass

from src.core.exceptions import NetworkError


@dataclass
class HTTPResponse:
    """HTTP 响应封装"""
    status_code: int
    headers: dict
    content: bytes
    json: Optional[dict] = None
    text: Optional[str] = None

    @property
    def ok(self) -> bool:
        """是否成功"""
        return 200 <= self.status_code < 300

    def raise_for_status(self) -> None:
        """状态码异常则抛出异常"""
        if not self.ok:
            raise NetworkError(f"HTTP {self.status_code}")


class HTTPClient:
    """HTTP 客户端封装 - 支持重试和超时"""

    _instance: Optional["HTTPClient"] = None

    def __new__(cls) -> "HTTPClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._client: Optional[httpx.AsyncClient] = None
        self._timeout = httpx.Timeout(30.0, connect=10.0)
        self._limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                limits=self._limits,
                follow_redirects=True,
            )
        return self._client

    async def __aenter__(self) -> "HTTPClient":
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()

    @asynccontextmanager
    async def client_session(self) -> AsyncIterator[httpx.AsyncClient]:
        """创建客户端会话（使用上下文管理器）"""
        async with httpx.AsyncClient(
            timeout=self._timeout,
            limits=self._limits,
            follow_redirects=True,
        ) as client:
            yield client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[bytes] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> HTTPResponse:
        """发送 HTTP 请求"""
        client = await self._get_client()
        timeout_val = httpx.Timeout(timeout) if timeout else self._timeout

        last_error = None
        for attempt in range(max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    content=data,
                    timeout=timeout_val,
                )

                content = response.content
                json_data = None
                text = None

                try:
                    json_data = response.json()
                except Exception:
                    text = response.text

                return HTTPResponse(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                    json=json_data,
                    text=text,
                )

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                continue

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    last_error = e
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
                raise NetworkError(f"HTTP {e.response.status_code}: {str(e)}")

            except Exception as e:
                raise NetworkError(f"HTTP 请求失败: {str(e)}")

        raise NetworkError(f"HTTP 请求失败（已重试 {max_retries} 次）: {last_error}")

    async def get(
        self,
        url: str,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> HTTPResponse:
        """GET 请求"""
        return await self.request("GET", url, headers=headers, params=params, timeout=timeout, max_retries=max_retries)

    async def post(
        self,
        url: str,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[bytes] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> HTTPResponse:
        """POST 请求"""
        return await self.request("POST", url, headers=headers, json=json, data=data, timeout=timeout, max_retries=max_retries)

    async def put(
        self,
        url: str,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[bytes] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> HTTPResponse:
        """PUT 请求"""
        return await self.request("PUT", url, headers=headers, json=json, data=data, timeout=timeout, max_retries=max_retries)

    async def delete(
        self,
        url: str,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> HTTPResponse:
        """DELETE 请求"""
        return await self.request("DELETE", url, headers=headers, timeout=timeout, max_retries=max_retries)

    async def patch(
        self,
        url: str,
        headers: Optional[dict] = None,
        json: Optional[dict] = None,
        data: Optional[bytes] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ) -> HTTPResponse:
        """PATCH 请求"""
        return await self.request("PATCH", url, headers=headers, json=json, data=data, timeout=timeout, max_retries=max_retries)


class APIClient:
    """API 客户端基类"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._http = get_http_client()

    def _get_headers(self, additional_headers: Optional[dict] = None) -> dict:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if additional_headers:
            headers.update(additional_headers)
        return headers

    async def get(self, path: str, params: Optional[dict] = None) -> HTTPResponse:
        """GET 请求"""
        url = f"{self.base_url}{path}"
        return await self._http.get(url, headers=self._get_headers(), params=params, timeout=self.timeout)

    async def post(self, path: str, json: Optional[dict] = None) -> HTTPResponse:
        """POST 请求"""
        url = f"{self.base_url}{path}"
        return await self._http.post(url, headers=self._get_headers(), json=json, timeout=self.timeout)

    async def put(self, path: str, json: Optional[dict] = None) -> HTTPResponse:
        """PUT 请求"""
        url = f"{self.base_url}{path}"
        return await self._http.put(url, headers=self._get_headers(), json=json, timeout=self.timeout)

    async def delete(self, path: str) -> HTTPResponse:
        """DELETE 请求"""
        url = f"{self.base_url}{path}"
        return await self._http.delete(url, headers=self._get_headers(), timeout=self.timeout)


class OpenAIClient(APIClient):
    """OpenAI API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(base_url, api_key)


class AnthropicClient(APIClient):
    """Anthropic API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1"):
        super().__init__(base_url, api_key)
        self._get_headers = lambda additional=None: {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            **(additional or {}),
        }


class StabilityAIClient(APIClient):
    """Stability AI API 客户端"""

    def __init__(self, api_key: str, base_url: str = "https://api.stability.ai/v1"):
        super().__init__(base_url, api_key)


_http_client_instance: Optional[HTTPClient] = None


def get_http_client() -> HTTPClient:
    """获取 HTTP 客户端单例"""
    global _http_client_instance
    if _http_client_instance is None:
        _http_client_instance = HTTPClient()
    return _http_client_instance
