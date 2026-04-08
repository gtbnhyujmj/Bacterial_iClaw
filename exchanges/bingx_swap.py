from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from core import ApiCredentials, BaseExchangeClient, ExchangeEnv


@dataclass
class BingXSwapEnv(ExchangeEnv):
    """變化相：BingX Swap 的環境設定。"""
    base_url: str = "https://open-api.bingx.com"


class BingXSwapClient(BaseExchangeClient):
    """變化相：把 BingX 的規則包進來。

    目前從 notebook 拆出來的規則：
    - base_url = https://open-api.bingx.com
    - header: X-BX-APIKEY
    - signature: HMAC-SHA256(secret, query_string)
    - signed query 放在 URL 上
    """

    def generate_signature(self, query_string: str) -> str:
        return self.sign_hmac_sha256(self.credentials.secret_key, query_string)

    def build_headers(self, *, auth_required: bool) -> Dict[str, str]:
        headers: Dict[str, str] = dict(self.env.extra_headers)
        if auth_required:
            headers["X-BX-APIKEY"] = self.credentials.api_key
        return headers

    # ---------- endpoint wrapper ----------
    def get_symbol_price_ticker(self, symbol: str) -> Dict[str, Any]:
        """對應原 notebook 的 /openApi/swap/v1/ticker/price"""
        path = "/openApi/swap/v1/ticker/price"
        params = {
            "symbol": symbol,
            # 原 notebook 有 timestamp；是否真的需要 signed/auth，之後可依正式文件調整
        }
        return self.request_json(
            method="GET",
            path=path,
            params=params,
            signed=True,
            auth_required=True,
        )

    # 之後可以繼續長：
    # def get_depth(...):
    # def get_kline(...):
    # def place_order(...):
    # def cancel_order(...):
