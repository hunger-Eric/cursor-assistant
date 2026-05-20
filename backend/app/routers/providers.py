"""
Provider management API routes
"""
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/api/providers", tags=["providers"])
provider_service = ProviderService()


class ProviderCreate(BaseModel):
    name: str
    type: str
    api_key: str
    base_url: str
    models: List[dict] = []


class ProviderResponse(BaseModel):
    id: int
    name: str
    type: str
    base_url: str
    is_active: bool
    models: List[dict]


@router.get("", response_model=List[ProviderResponse])
async def get_providers():
    return await provider_service.get_all_providers()


@router.post("")
async def create_provider(provider: ProviderCreate):
    result = await provider_service.create_provider(provider.name, provider.type, provider.api_key, provider.base_url, provider.models)
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
