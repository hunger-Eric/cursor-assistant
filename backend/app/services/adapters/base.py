"""
Base adapter for AI model providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncGenerator


class BaseAdapter(ABC):
    """Abstract base class for model adapters"""
    
    @property
    @abstractmethod
    def provider_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def default_models(self) -> List[Dict[str, str]]:
        pass
    
    @abstractmethod
    async def chat_completions(self, api_key: str, base_url: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def chat_completions_stream(self, api_key: str, base_url: str, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        pass
    
    def get_models(self) -> List[Dict[str, str]]:
        return self.default_models
