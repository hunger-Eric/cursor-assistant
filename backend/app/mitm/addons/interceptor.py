"""
Request Interceptor for MITM proxy
"""
import json
import logging
import time
from typing import Optional, Dict, Any
from mitmproxy import http
from app.services.provider_service import ProviderService

logger = logging.getLogger(__name__)

TARGET_HOSTS = ["api.openai.com", "api.deepseek.com", "openai.azure.com"]


class CursorInterceptor:
    def __init__(self):
        self.provider_service = ProviderService()
        self._request_count = 0
        self._error_count = 0
        
    @property
    def request_count(self) -> int:
        return self._request_count
    
    @property
    def error_count(self) -> int:
        return self._error_count
    
    def request(self, flow: http.HTTPFlow):
        self._request_count += 1
        if not self._is_target_request(flow):
            return
        logger.info(f"Intercepted: {flow.request.method} {flow.request.pretty_url}")
        if "/v1/chat/completions" in flow.request.path:
            self._handle_chat_completions(flow)
        elif "/v1/models" in flow.request.path:
            self._handle_models(flow)
    
    def _is_target_request(self, flow: http.HTTPFlow) -> bool:
        host = flow.request.pretty_host.lower()
        for target in TARGET_HOSTS:
            if target in host:
                return True
        if "/v1/" in flow.request.path.lower():
            return True
        return False
    
    def _handle_chat_completions(self, flow: http.HTTPFlow):
        try:
            body = flow.request.content
            if not body:
                return
            request_data = json.loads(body)
            model = request_data.get("model", "")
            provider = self.provider_service.get_provider_for_model(model)
            if not provider:
                flow.response = http.Response.make(
                    400,
                    json.dumps({"error": {"message": f"No provider for model: {model}"}}).encode(),
                    {"Content-Type": "application/json"}
                )
                return
            self._rewrite_request(flow, provider, request_data)
        except Exception as e:
            logger.error(f"Error handling chat completions: {e}")
            self._error_count += 1
    
    def _handle_models(self, flow: http.HTTPFlow):
        try:
            models = self.provider_service.get_available_models()
            response_data = {
                "object": "list",
                "data": [{"id": m["id"], "object": "model", "created": int(time.time()), "owned_by": m["provider"]} for m in models]
            }
            flow.response = http.Response.make(200, json.dumps(response_data).encode(), {"Content-Type": "application/json"})
        except Exception as e:
            logger.error(f"Error handling models: {e}")
    
    def _rewrite_request(self, flow: http.HTTPFlow, provider: Dict[str, Any], request_data: Dict[str, Any]):
        flow.request.host = provider["base_url"].replace("https://", "").replace("http://", "")
        flow.request.scheme = "https"
        if "Authorization" not in flow.request.headers:
            flow.request.headers["Authorization"] = f"Bearer {provider['api_key']}"
        logger.info(f"Rewrote request to {flow.request.host}")
