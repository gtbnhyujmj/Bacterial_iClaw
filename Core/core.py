from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Optional
import hmac
import time
import requests


@dataclass
class ApiCredentials:
    api_key: str = ""
    secret_key: str = ""


@dataclass
class ExchangeEnv:
    """固定相：描述交易所執行環境的最小必要資訊。"""
    base_url: str
    recv_window: Optional[int] = None
    timeout: int = 10
    extra_headers: Dict[str, str] = field(default_factory=dict)


class BaseExchangeClient(ABC):
    """固定相：所有交易所都共用的核心骨架。

    子類別只需要處理：
    1. API 路徑規則
    2. Header 規則
    3. 簽名規則
    4. 參數格式規則
    5. endpoint 對應
    """

    def __init__(self, env: ExchangeEnv, credentials: Optional[ApiCredentials] = None):
        self.env = env
        self.credentials = credentials or ApiCredentials()

    # ---------- 共用工具 ----------
    def now_ms(self) -> int:
        return int(time.time() * 1000)

    def sign_hmac_sha256(self, secret: str, payload: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

    def build_query_string(self, params: Mapping[str, Any]) -> str:
        """固定相預設：字典排序後組成 query string。
        若某交易所有特殊編碼規則，再由子類 override。
        """
        items = [(k, v) for k, v in params.items() if v is not None]
        items.sort(key=lambda x: x[0])
        return "&".join(f"{k}={v}" for k, v in items)

    def merge_default_params(self, params: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        merged = dict(params or {})
        merged.setdefault("timestamp", self.now_ms())
        if self.env.recv_window is not None:
            merged.setdefault("recvWindow", self.env.recv_window)
        return merged

    def build_url(self, path: str, query_string: str = "") -> str:
        if query_string:
            return f"{self.env.base_url}{path}?{query_string}"
        return f"{self.env.base_url}{path}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        payload: Any = None,
        signed: bool = False,
        auth_required: bool = False,
    ) -> requests.Response:
        """固定相主流程：
        先整理參數 -> 視需要簽名 -> 組 URL -> 補 headers -> 發 request
        """
        method = method.upper()
        final_params = self.prepare_params(params or {}, signed=signed)
        query_string = self.build_query_string(final_params)

        if signed:
            query_string = self.attach_signature(query_string)

        url = self.build_url(path, query_string)
        headers = self.build_headers(auth_required=auth_required)

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=payload,
            timeout=self.env.timeout,
        )
        return response

    def request_json(self, *args, **kwargs) -> Dict[str, Any]:
        response = self.request(*args, **kwargs)
        response.raise_for_status()
        return response.json()

    # ---------- 可被交易所差異化覆寫 ----------
    def prepare_params(self, params: Mapping[str, Any], *, signed: bool) -> Dict[str, Any]:
        """預設：只有 signed request 才自動補 timestamp 等欄位。"""
        if signed:
            return self.merge_default_params(params)
        return dict(params)

    def attach_signature(self, query_string: str) -> str:
        signature = self.generate_signature(query_string)
        return f"{query_string}&signature={signature}" if query_string else f"signature={signature}"

    @abstractmethod
    def generate_signature(self, query_string: str) -> str:
        pass

    @abstractmethod
    def build_headers(self, *, auth_required: bool) -> Dict[str, str]:
        pass
