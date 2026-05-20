"""
Provider Service for managing AI model providers
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from app.models.provider import Provider, Model
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class ProviderService:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_all_providers(self) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Provider).where(Provider.is_active == True))
            providers = result.scalars().all()
            return [{
                "id": p.id, "name": p.name, "type": p.type, "base_url": p.base_url,
                "api_key": p.api_key, "is_active": p.is_active,
                "models": [{"id": m.id, "model_id": m.model_id, "name": m.name, "max_tokens": m.max_tokens, "supports_streaming": m.supports_streaming, "is_active": m.is_active} for m in p.models if m.is_active]
            } for p in providers]
    
    def get_provider_for_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        if model_id in self._cache:
            return self._cache[model_id]
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        providers = loop.run_until_complete(self._get_provider_for_model_async(model_id))
        if providers:
            result = providers[0]
            self._cache[model_id] = result
            return result
        return None
    
    async def _get_provider_for_model_async(self, model_id: str) -> Optional[List[Dict[str, Any]]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Provider, Model).join(Model, Provider.id == Model.provider_id).where(
                    Model.model_id == model_id, Model.is_active == True, Provider.is_active == True
                )
            )
            rows = result.first()
            if not rows:
                return None
            provider, model = rows
            return [{"id": provider.id, "name": provider.name, "type": provider.type, "base_url": provider.base_url, "api_key": provider.api_key, "model_id": model.model_id, "model_name": model.name, "max_tokens": model.max_tokens, "supports_streaming": model.supports_streaming, "parameters": model.parameters or {}}]
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Model, Provider).join(Provider, Model.provider_id == Provider.id).where(Model.is_active == True, Provider.is_active == True))
            rows = result.all()
            return [{"id": m.model_id, "name": m.name, "provider": p.name, "provider_type": p.type, "max_tokens": m.max_tokens, "supports_streaming": m.supports_streaming} for m, p in rows]
    
    async def create_provider(self, name: str, provider_type: str, api_key: str, base_url: str, models: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            provider = Provider(name=name, type=provider_type, api_key=api_key, base_url=base_url, is_active=True)
            session.add(provider)
            await session.flush()
            if models:
                for m in models:
                    model = Model(provider_id=provider.id, model_id=m["model_id"], name=m["name"], max_tokens=m.get("max_tokens", 4096), supports_streaming=m.get("supports_streaming", True), is_active=True, parameters=m.get("parameters", {}))
                    session.add(model)
            await session.commit()
            return {"id": provider.id, "name": provider.name}
    
    async def delete_provider(self, provider_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Provider).where(Provider.id == provider_id))
            provider = result.scalar_one_or_none()
            if provider:
                await session.delete(provider)
                await session.commit()
                return True
            return False
    
    def clear_cache(self):
        self._cache.clear()
