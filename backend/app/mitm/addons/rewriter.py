"""
Request/Response Rewriter
"""
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional
import httpx

logger = logging.getLogger(__name__)


class RequestRewriter:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0, follow_redirects=True)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def forward_request(self, provider: Dict[str, Any], request_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        client = await self.get_client()
        url = f"{provider['base_url']}/chat/completions"
        headers = {k: v for k, v in headers.items() if k.lower() != "content-length"}
        response = await client.post(url, json=request_data, headers=headers)
        return {"status": response.status_code, "data": response.json(), "headers": dict(response.headers)}
    
    async def forward_streaming_request(self, provider: Dict[str, Any], request_data: Dict[str, Any], headers: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
        client = await self.get_client()
        url = f"{provider['base_url']}/chat/completions"
        request_data["stream"] = True
        headers = {k: v for k, v in headers.items() if k.lower() != "content-length"}
        try:
            async with client.stream("POST", url, json=request_data, headers=headers) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                yield {"type": "done"}
                            else:
                                try:
                                    chunk = json.loads(data)
                                    yield {"type": "chunk", "data": chunk}
                                except json.JSONDecodeError:
                                    pass
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield {"type": "error", "error": str(e)}
