import base64
import time
import httpx


class RestClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def process(self, payload_size: str, data: bytes) -> dict:
        resp = await self._client.post("/process", json={
            "payload_size": payload_size,
            "data": base64.b64encode(data).decode(),
            "client_timestamp": int(time.time() * 1_000_000),
        }, timeout=30.0)
        resp.raise_for_status()
        body = resp.json()
        return {
            "data": base64.b64decode(body["data"]),
            "checksum": body["checksum"],
            "server_timestamp": body["server_timestamp"],
            "payload_size": body["payload_size"],
        }

    async def health(self) -> bool:
        try:
            r = await self._client.get("/health", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False
