import json
import time
from typing import Any, Dict

import httpx

from app.core.config import settings
from app.core.security import kraken_authent


class KrakenFuturesClient:
    def __init__(self, api_key: str, api_secret: str, environment: str = "demo"):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = settings.kraken_demo_base_url if environment == "demo" else settings.kraken_prod_base_url

    async def _request(self, method: str, endpoint_path: str, payload: Dict[str, Any] | None = None):
        payload = payload or {}
        nonce = str(int(time.time() * 1000))
        body = json.dumps(payload, separators=(",", ":")) if method in {"POST", "PUT", "DELETE"} else ""
        authent = kraken_authent(endpoint_path, body, nonce, self.api_secret)
        headers = {
            "APIKey": self.api_key,
            "Nonce": nonce,
            "Authent": authent,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.request(method, f"{self.base_url}{endpoint_path}", content=body if body else None, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def get_positions(self):
        return await self._request("GET", "/openpositions")

    async def get_orders(self):
        return await self._request("GET", "/openorders")

    async def get_fills(self):
        return await self._request("GET", "/fills")

    async def send_order(self, order: Dict[str, Any]):
        return await self._request("POST", "/sendorder", order)

    async def cancel_order(self, order_id: str):
        return await self._request("POST", "/cancelorder", {"order_id": order_id})

    async def amend_order(self, order: Dict[str, Any]):
        return await self._request("POST", "/editorder", order)
