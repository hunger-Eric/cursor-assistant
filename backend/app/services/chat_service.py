"""
Chat Service for handling chat completions
"""
import json
import time
import logging
from typing import Dict, Any, AsyncGenerator, Optional
import httpx
from app.models.request_log import RequestLog
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def chat_completions(self, provider: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        client = await self.get_client()
        url = f"{provider['base_url']}/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {provider['api_key']}"}
        body = {"model": request_data.get("model", provider.get("model_id")), "messages": request_data.get("messages", []), "temperature": request_data.get("temperature", 0.7), "top_p": request_data.get("top_p", 1.0), "max_tokens": request_data.get("max_tokens", provider.get("max_tokens", 4096)), "stream": False}
        body = {k: v for k, v in body.items() if v is not None}
        start_time = time.time()
        try:
            response = await client.post(url, json=body, headers=headers)
            latency_ms = int((time.time() - start_time) * 1000)
            if response.status_code != 200:
                raise Exception(f"Provider returned {response.status_code}: {response.text}")
            result = response.json()
            usage = result.get("usage", {})
            await self._log_request(provider, request_data, latency_ms, status="success", prompt_tokens=usage.get("prompt_tokens", 0), completion_tokens=usage.get("completion_tokens", 0), total_tokens=usage.get("total_tokens", 0))
            return result
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            await self._log_request(provider, request_data, latency_ms, status="error", error_message=str(e))
            raise
    
    async def _log_request(self, provider: Dict[str, Any], request_data: Dict[str, Any], latency_ms: int, status: str = "success", error_message: str = None, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
        try:
            async with AsyncSessionLocal() as session:
                log = RequestLog(model_id=request_data.get("model", ""), provider_id=str(provider.get("id", "")), provider_type=provider.get("type", ""), prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens, latency_ms=latency_ms, status=status, error_message=error_message)
                session.add(log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
