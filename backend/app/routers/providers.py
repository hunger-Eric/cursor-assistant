"""
Provider management API routes
"""
from typing import List
import time
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.provider_service import ProviderService
from app.services.adapters.deepseek import DeepSeekAdapter
from app.services.adapters.qwen import QwenAdapter
from app.services.adapters.glm import GLMAdapter
from app.services.adapters.kimi import KimiAdapter

router = APIRouter(prefix="/api/providers", tags=["providers"])
provider_service = ProviderService()


class ProviderCreate(BaseModel):
    name: str
    type: str
    api_key: str
    base_url: str
    models: List[dict] = []


class ProviderTestRequest(BaseModel):
    provider_id: int


class ProviderResponse(BaseModel):
    id: int
    name: str
    type: str
    base_url: str
    is_active: bool
    models: List[dict]


# 默认提供者配置模板
PROVIDER_TEMPLATES = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "adapter": DeepSeekAdapter
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "adapter": QwenAdapter
    },
    "glm": {
        "name": "智谱 AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "adapter": GLMAdapter
    },
    "kimi": {
        "name": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "adapter": KimiAdapter
    }
}


@router.get("", response_model=List[ProviderResponse])
async def get_providers():
    return await provider_service.get_all_providers()


@router.get("/templates")
async def get_provider_templates():
    """获取可用的提供者模板"""
    templates = []
    for provider_type, template in PROVIDER_TEMPLATES.items():
        adapter = template["adapter"]()
        templates.append({
            "type": provider_type,
            "name": template["name"],
            "base_url": template["base_url"],
            "default_models": adapter.default_models
        })
    return templates


@router.post("")
async def create_provider(provider: ProviderCreate):
    # 如果没有提供模型，使用对应类型的默认模型
    if not provider.models and provider.type in PROVIDER_TEMPLATES:
        adapter = PROVIDER_TEMPLATES[provider.type]["adapter"]()
        provider.models = [
            {
                "model_id": m["id"],
                "name": m["name"],
                "max_tokens": 4096,
                "supports_streaming": True,
                "parameters": {}
            }
            for m in adapter.default_models
        ]
    result = await provider_service.create_provider(
        provider.name, provider.type, provider.api_key, provider.base_url, provider.models
    )
    return result


@router.delete("/{provider_id}")
async def delete_provider(provider_id: int):
    success = await provider_service.delete_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"success": True}


@router.get("/models")
async def get_models():
    return await provider_service.get_available_models()


@router.post("/test")
async def test_provider(payload: ProviderTestRequest):
    providers = await provider_service.get_all_providers()
    provider = next((p for p in providers if p["id"] == payload.provider_id), None)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    headers = {
        "Authorization": f"Bearer {provider['api_key']}",
        "Content-Type": "application/json",
    }

    # Use models endpoint to perform a lightweight connectivity validation.
    url = f"{provider['base_url'].rstrip('/')}/models"
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
        latency_ms = int((time.time() - start) * 1000)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail=f"Provider returned {response.status_code}: {response.text}",
            )
        return {"ok": True, "latency_ms": latency_ms}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
