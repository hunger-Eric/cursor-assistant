"""
Qwen (Tongyi Qianwen) adapter
"""
from typing import Dict, Any, List, AsyncGenerator
import httpx
from app.services.adapters.base import BaseAdapter


class QwenAdapter(BaseAdapter):
    @property
    def provider_type(self) -> str:
        return "qwen"
    
    @property
    def default_models(self) -> List[Dict[str, str]]:
        return [
            {"id": "qwen-plus", "name": "通义千问 Plus"},
            {"id": "qwen-turbo", "name": "通义千问 Turbo"},
            {"id": "qwen-max", "name": "通义千问 Max"},
        ]
    
    async def chat_completions(self, api_key: str, base_url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=request_data, headers=headers)
            return response.json()
    
    async def chat_completions_stream(self, api_key: str, base_url: str, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        url = f"{base_url}/chat/completions"
        request_data["stream"] = True
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=request_data, headers=headers) as response:
                async for line in response.aiter_lines():
                    if line.strip():
                        yield line
