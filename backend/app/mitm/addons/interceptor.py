"""
Request Interceptor for MITM proxy
"""
import json
import logging
import time
import asyncio
import sqlite3
import ssl
import struct
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict, Any
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from mitmproxy import ctx, http
from app.services.provider_service import ProviderService
from app.config import config

logger = logging.getLogger(__name__)

TARGET_HOSTS = ["api.openai.com", "api.deepseek.com", "openai.azure.com"]
CURSOR_AI_SERVICE_PATH = "/aiserver.v1.AiService/"
CONNECT_ENVELOPE_HEADER_LEN = 5


def _add_field(
    message: descriptor_pb2.DescriptorProto,
    *,
    number: int,
    name: str,
    field_type: int,
    label: int = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL,
    type_name: Optional[str] = None,
):
    field = message.field.add()
    field.number = number
    field.name = name
    field.type = field_type
    field.label = label
    if type_name:
        field.type_name = type_name


def _build_cursor_proto_classes() -> dict[str, Any]:
    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "cursor_dynamic.proto"
    file_proto.package = "aiserver.v1"
    file_proto.syntax = "proto3"

    model_details = file_proto.message_type.add()
    model_details.name = "ModelDetails"
    _add_field(model_details, number=1, name="model_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(model_details, number=2, name="api_key", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(model_details, number=6, name="openai_api_base_url", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(model_details, number=8, name="max_mode", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)

    stream_request = file_proto.message_type.add()
    stream_request.name = "StreamUnifiedChatRequest"
    _add_field(
        stream_request,
        number=5,
        name="model_details",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".aiserver.v1.ModelDetails",
    )

    stream_request_with_tools = file_proto.message_type.add()
    stream_request_with_tools.name = "StreamUnifiedChatRequestWithTools"
    _add_field(
        stream_request_with_tools,
        number=1,
        name="stream_unified_chat_request",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".aiserver.v1.StreamUnifiedChatRequest",
    )

    stream_request_idempotent = file_proto.message_type.add()
    stream_request_idempotent.name = "StreamUnifiedChatRequestWithToolsIdempotent"
    _add_field(
        stream_request_idempotent,
        number=1,
        name="client_chunk",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".aiserver.v1.StreamUnifiedChatRequestWithTools",
    )
    _add_field(stream_request_idempotent, number=4, name="idempotency_key", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(stream_request_idempotent, number=5, name="seqno", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_UINT32)

    available_models_response = file_proto.message_type.add()
    available_models_response.name = "AvailableModelsResponse"

    vendor = available_models_response.nested_type.add()
    vendor.name = "ModelVendor"
    _add_field(vendor, number=1, name="id", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
    _add_field(vendor, number=2, name="display_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)

    available_model = available_models_response.nested_type.add()
    available_model.name = "AvailableModel"
    _add_field(available_model, number=1, name="name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(available_model, number=2, name="default_on", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=5, name="supports_agent", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=10, name="supports_images", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=14, name="supports_max_mode", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=15, name="context_token_limit", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_INT32)
    _add_field(available_model, number=17, name="client_display_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(available_model, number=18, name="server_model_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(available_model, number=19, name="supports_non_max_mode", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=22, name="supports_plan_mode", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=23, name="is_user_added", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=24, name="inputbox_short_model_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(available_model, number=26, name="supports_cmd_k", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=40, name="visible_in_routed_model_view", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)
    _add_field(available_model, number=41, name="vendor_name", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING)
    _add_field(
        available_model,
        number=42,
        name="vendor",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        type_name=".aiserver.v1.AvailableModelsResponse.ModelVendor",
    )

    _add_field(
        available_models_response,
        number=2,
        name="models",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
        type_name=".aiserver.v1.AvailableModelsResponse.AvailableModel",
    )
    _add_field(
        available_models_response,
        number=1,
        name="model_names",
        field_type=descriptor_pb2.FieldDescriptorProto.TYPE_STRING,
        label=descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED,
    )
    _add_field(available_models_response, number=11, name="use_model_parameters", field_type=descriptor_pb2.FieldDescriptorProto.TYPE_BOOL)

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_proto)

    def _cls(name: str):
        descriptor = pool.FindMessageTypeByName(name)
        if hasattr(message_factory, "GetMessageClass"):
            return message_factory.GetMessageClass(descriptor)
        return message_factory.MessageFactory(pool).GetPrototype(descriptor)

    return {
        "AvailableModelsResponse": _cls("aiserver.v1.AvailableModelsResponse"),
        "StreamUnifiedChatRequest": _cls("aiserver.v1.StreamUnifiedChatRequest"),
        "StreamUnifiedChatRequestWithTools": _cls("aiserver.v1.StreamUnifiedChatRequestWithTools"),
        "StreamUnifiedChatRequestWithToolsIdempotent": _cls("aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent"),
    }


CURSOR_PROTO = _build_cursor_proto_classes()


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
        elif CURSOR_AI_SERVICE_PATH in flow.request.path:
            self._handle_cursor_ai_service_request(flow)

    def response(self, flow: http.HTTPFlow):
        try:
            if CURSOR_AI_SERVICE_PATH in flow.request.path and "AvailableM" in flow.request.path:
                self._handle_cursor_available_models_response(flow)
        except Exception as e:
            logger.error(f"Error handling response rewrite: {e}")
    
    def _is_target_request(self, flow: http.HTTPFlow) -> bool:
        host = flow.request.pretty_host.lower()
        for target in TARGET_HOSTS:
            if target in host:
                return True
        if "/v1/" in flow.request.path.lower():
            return True
        if CURSOR_AI_SERVICE_PATH in flow.request.path:
            return True
        return False

    def _log_info(self, message: str):
        logger.info(message)
        try:
            with open("/tmp/cursor-interceptor.log", "a", encoding="utf-8") as handle:
                handle.write(message + "\n")
        except Exception:
            pass
        try:
            ctx.log.info(message)
        except Exception:
            pass

    def _log_warning(self, message: str):
        logger.warning(message)
        try:
            with open("/tmp/cursor-interceptor.log", "a", encoding="utf-8") as handle:
                handle.write("WARN: " + message + "\n")
        except Exception:
            pass
        try:
            ctx.log.warn(message)
        except Exception:
            pass

    def _handle_cursor_ai_service_request(self, flow: http.HTTPFlow):
        """
        Extract model names from Cursor native AiService requests so we can
        observe whether Cursor later falls back to OpenAI-compatible paths or
        keeps using protobuf-native endpoints for generation.
        """
        if "AvailableM" in flow.request.path:
            return
        body = flow.request.content or b""
        if not body:
            return

        content_type = (flow.request.headers.get("Content-Type", "") or "").lower()
        model_id = None
        if "json" in content_type:
            try:
                request_data = json.loads(body)
                model_id = self._extract_model_id_from_payload(request_data)
            except Exception:
                model_id = None
        else:
            model_id = self._extract_model_id_from_cursor_request(body)

        if not model_id:
            return

        provider = self._get_provider_for_model_sync(model_id)
        if not provider:
            self._log_info(f"Cursor AiService request model={model_id} kept upstream")
            return

        self._log_info(
            f"Cursor AiService request selected BYOK model={model_id} on path={flow.request.path}; "
            "waiting to see whether Cursor emits OpenAI-compatible downstream traffic or protobuf-native generation traffic"
        )

    def _handle_cursor_available_models_response(self, flow: http.HTTPFlow):
        """
        Inject locally configured models into Cursor's native AvailableModels
        response. Supports JSON, raw protobuf, and Connect-style envelopes.
        """
        if not flow.response or not flow.response.content:
            return

        local_models = self._get_available_models_sync()
        if not local_models:
            return

        content_type = (flow.response.headers.get("Content-Type", "") or "").lower()
        raw = flow.response.content
        self._log_info(
            "AvailableModels response observed "
            f"content-type={content_type or '<empty>'} bytes={len(raw)} head={raw[:16].hex()}"
        )

        if "json" in content_type:
            try:
                payload = json.loads(raw)
            except Exception:
                self._log_info("AvailableModels JSON parse failed; skipped union injection")
                return

            updated = self._inject_models_into_cursor_available_models_payload(payload, local_models)
            if not updated:
                self._log_info("AvailableModels payload shape not recognized; skipped union injection")
                return

            flow.response.content = json.dumps(payload).encode("utf-8")
            flow.response.headers["Content-Type"] = "application/json"
            flow.response.headers.pop("Content-Length", None)
            self._log_info(f"Injected {updated} local models into Cursor AvailableModels JSON response")
            return

        updated_raw = self._inject_models_into_available_models_proto(raw, local_models)
        if updated_raw is None:
            self._log_info("AvailableModels binary parse failed; skipped union injection")
            return
        flow.response.content = updated_raw
        flow.response.headers.pop("Content-Length", None)
        self._log_info("Injected local models into Cursor AvailableModels binary response")
    
    def _handle_chat_completions(self, flow: http.HTTPFlow):
        try:
            body = flow.request.content
            if not body:
                return
            request_data = json.loads(body)
            requested_model = request_data.get("model", "")
            provider = self._get_provider_for_model_sync(requested_model)
            if not provider:
                # Not a BYOK model, keep original provider path untouched.
                return
            self._rewrite_request(flow, provider, request_data, requested_model)
        except Exception as e:
            logger.error(f"Error handling chat completions: {e}")
            self._error_count += 1
    
    def _handle_models(self, flow: http.HTTPFlow):
        try:
            models = self._merge_models_with_upstream(flow)
            response_data = {
                "object": "list",
                "data": [{"id": m["id"], "object": "model", "created": int(time.time()), "owned_by": m["provider"]} for m in models]
            }
            flow.response = http.Response.make(200, json.dumps(response_data).encode(), {"Content-Type": "application/json"})
        except Exception as e:
            logger.error(f"Error handling models: {e}")
    
    def _rewrite_request(
        self,
        flow: http.HTTPFlow,
        provider: Dict[str, Any],
        request_data: Dict[str, Any],
        requested_model: str,
    ):
        parsed = urlparse(provider["base_url"])
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid provider base_url: {provider['base_url']}")

        base_path = parsed.path.rstrip("/")
        original_path = flow.request.path or ""
        if original_path.startswith("/v1/"):
            suffix_path = original_path[len("/v1"):]
        else:
            suffix_path = original_path
        if not suffix_path.startswith("/"):
            suffix_path = "/" + suffix_path

        flow.request.scheme = parsed.scheme
        flow.request.host = parsed.hostname or flow.request.host
        flow.request.port = parsed.port or (443 if parsed.scheme == "https" else 80)
        flow.request.path = f"{base_path}{suffix_path}" if base_path else suffix_path
        flow.request.headers["Authorization"] = f"Bearer {provider['api_key']}"
        # Rewrite model id so free-tier Cursor built-in model names can map to BYOK providers.
        request_data["model"] = provider["model_id"]
        flow.request.content = json.dumps(request_data).encode("utf-8")
        flow.request.headers["Content-Type"] = "application/json"
        logger.info(f"Rewrote request to {flow.request.scheme}://{flow.request.host}:{flow.request.port}{flow.request.path}")
        if requested_model != provider["model_id"]:
            logger.info(f"Model remapped: {requested_model} -> {provider['model_id']}")

    def _rewrite_cursor_ai_service_request(self, flow: http.HTTPFlow, provider: Dict[str, Any]):
        parsed = urlparse(provider["base_url"])
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid provider base_url: {provider['base_url']}")

        flow.request.scheme = parsed.scheme
        flow.request.host = parsed.hostname or flow.request.host
        flow.request.port = parsed.port or (443 if parsed.scheme == "https" else 80)
        flow.request.headers["Authorization"] = f"Bearer {provider['api_key']}"

    def _run_async(self, coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _db_path(self) -> Path:
        # sqlite+aiosqlite:///./cursor-assistant.db -> ./cursor-assistant.db
        raw = config.database.url.replace("sqlite+aiosqlite:///", "", 1)
        return Path(raw).resolve()

    def _get_provider_for_model_sync(self, model_id: str) -> Optional[Dict[str, Any]]:
        if not model_id:
            return None
        try:
            db = self._db_path()
            conn = sqlite3.connect(str(db))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT p.id, p.name, p.type, p.base_url, p.api_key,
                       m.model_id, m.name as model_name, m.max_tokens, m.supports_streaming, m.parameters
                FROM providers p
                JOIN models m ON p.id = m.provider_id
                WHERE p.is_active = 1 AND m.is_active = 1 AND m.model_id = ?
                LIMIT 1
                """,
                (model_id,),
            )
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            params = {}
            if row["parameters"]:
                try:
                    params = json.loads(row["parameters"]) if isinstance(row["parameters"], str) else row["parameters"]
                except Exception:
                    params = {}
            return {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "base_url": row["base_url"],
                "api_key": row["api_key"],
                "model_id": row["model_id"],
                "model_name": row["model_name"],
                "max_tokens": row["max_tokens"],
                "supports_streaming": bool(row["supports_streaming"]),
                "parameters": params,
            }
        except Exception as e:
            logger.error(f"Failed to query provider mapping: {e}")
            return None

    def _get_available_models_sync(self) -> list[Dict[str, Any]]:
        try:
            db = self._db_path()
            conn = sqlite3.connect(str(db))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT m.model_id, m.name, p.name as provider, p.type as provider_type,
                       m.max_tokens, m.supports_streaming
                FROM models m
                JOIN providers p ON p.id = m.provider_id
                WHERE p.is_active = 1 AND m.is_active = 1
                """
            )
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "id": r["model_id"],
                    "name": r["name"],
                    "provider": r["provider"],
                    "provider_type": r["provider_type"],
                    "max_tokens": r["max_tokens"],
                    "supports_streaming": bool(r["supports_streaming"]),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Failed to query available models: {e}")
            return []

    def _merge_models_with_upstream(self, flow: http.HTTPFlow) -> list[Dict[str, Any]]:
        local_models = self._get_available_models_sync()
        local_ids = {m["id"] for m in local_models}
        merged = list(local_models)

        upstream = self._fetch_upstream_models(flow)
        for m in upstream:
            if m.get("id") in local_ids:
                continue
            merged.append(m)
        return merged

    def _fetch_upstream_models(self, flow: http.HTTPFlow) -> list[Dict[str, Any]]:
        try:
            target_url = flow.request.pretty_url
            headers = {}
            for k, v in flow.request.headers.items():
                kl = k.lower()
                if kl in {"host", "content-length", "accept-encoding", "proxy-connection", "connection"}:
                    continue
                headers[k] = v
            req = urllib.request.Request(target_url, headers=headers, method="GET")
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=20, context=context) as resp:
                raw = resp.read()
            parsed = json.loads(raw.decode("utf-8", errors="ignore"))
            data = parsed.get("data", [])
            normalized = []
            for item in data:
                mid = item.get("id")
                if not mid:
                    continue
                normalized.append(
                    {
                        "id": mid,
                        "name": item.get("id"),
                        "provider": item.get("owned_by", "upstream"),
                        "provider_type": "upstream",
                        "max_tokens": 0,
                        "supports_streaming": True,
                    }
                )
            return normalized
        except Exception as e:
            logger.warning(f"Failed to fetch upstream models for merge: {e}")
            return []

    def _decode_connect_envelope(self, raw: bytes) -> Optional[list[tuple[int, bytes]]]:
        if len(raw) < CONNECT_ENVELOPE_HEADER_LEN:
            return None
        pos = 0
        frames: list[tuple[int, bytes]] = []
        while pos + CONNECT_ENVELOPE_HEADER_LEN <= len(raw):
            flags = raw[pos]
            length = struct.unpack(">I", raw[pos + 1 : pos + 5])[0]
            pos += CONNECT_ENVELOPE_HEADER_LEN
            if pos + length > len(raw):
                return None
            frames.append((flags, raw[pos : pos + length]))
            pos += length
        if pos != len(raw) or not frames:
            return None
        return frames

    def _encode_connect_envelope(self, frames: list[tuple[int, bytes]]) -> bytes:
        parts: list[bytes] = []
        for flags, payload in frames:
            parts.append(bytes([flags]) + struct.pack(">I", len(payload)) + payload)
        return b"".join(parts)

    def _parse_cursor_message(self, raw: bytes, message_cls):
        frames = self._decode_connect_envelope(raw)
        payload = raw
        envelope = None
        if frames is not None:
            envelope = frames
            if frames[0][0] & 1:
                self._log_warning(f"Connect envelope for {message_cls.__name__} is compressed; unsupported")
                return None, None
            payload = frames[0][1]
        try:
            message = message_cls()
            message.ParseFromString(payload)
            return message, envelope
        except Exception:
            return None, None

    def _serialize_cursor_message(self, message, envelope: Optional[list[tuple[int, bytes]]]) -> bytes:
        payload = message.SerializeToString()
        if envelope is None:
            return payload
        new_frames = list(envelope)
        new_frames[0] = (new_frames[0][0], payload)
        return self._encode_connect_envelope(new_frames)

    def _inject_models_into_available_models_proto(self, raw: bytes, local_models: list[Dict[str, Any]]) -> Optional[bytes]:
        message_cls = CURSOR_PROTO["AvailableModelsResponse"]
        response, envelope = self._parse_cursor_message(raw, message_cls)
        if response is None:
            return None

        existing_ids = set(response.model_names)
        for model in response.models:
            if getattr(model, "name", ""):
                existing_ids.add(model.name)
            if getattr(model, "server_model_name", ""):
                existing_ids.add(model.server_model_name)

        added = 0
        for local in local_models:
            model_id = local.get("id")
            if not model_id or model_id in existing_ids:
                continue
            response.model_names.append(model_id)
            model = response.models.add()
            model.name = model_id
            model.default_on = True
            model.supports_agent = True
            model.supports_images = False
            model.supports_max_mode = False
            model.supports_non_max_mode = True
            model.supports_plan_mode = True
            model.context_token_limit = int(local.get("max_tokens") or 0)
            model.client_display_name = local.get("name") or model_id
            model.server_model_name = model_id
            model.is_user_added = True
            model.inputbox_short_model_name = model_id
            model.supports_cmd_k = True
            model.visible_in_routed_model_view = True
            model.vendor_name = local.get("provider") or "BYOK"
            model.vendor.id = 2
            model.vendor.display_name = local.get("provider") or "BYOK"
            existing_ids.add(model_id)
            added += 1

        if not added:
            return raw

        return self._serialize_cursor_message(response, envelope)

    def _extract_model_id_from_cursor_request(self, raw: bytes) -> Optional[str]:
        candidates = [
            CURSOR_PROTO["StreamUnifiedChatRequestWithToolsIdempotent"],
            CURSOR_PROTO["StreamUnifiedChatRequestWithTools"],
            CURSOR_PROTO["StreamUnifiedChatRequest"],
        ]
        for message_cls in candidates:
            message, _ = self._parse_cursor_message(raw, message_cls)
            if message is None:
                continue
            model_name = self._extract_model_name_from_proto_message(message)
            if model_name:
                return model_name
        return None

    def _extract_model_name_from_proto_message(self, message: Any) -> Optional[str]:
        if hasattr(message, "model_details") and message.HasField("model_details"):
            model_name = getattr(message.model_details, "model_name", "")
            if model_name:
                return model_name
        if hasattr(message, "stream_unified_chat_request") and message.HasField("stream_unified_chat_request"):
            return self._extract_model_name_from_proto_message(message.stream_unified_chat_request)
        if hasattr(message, "client_chunk") and message.HasField("client_chunk"):
            return self._extract_model_name_from_proto_message(message.client_chunk)
        return None

    def _extract_model_id_from_payload(self, payload: Any) -> Optional[str]:
        if isinstance(payload, dict):
            for key in ("model", "model_id", "modelId", "name"):
                val = payload.get(key)
                if isinstance(val, str) and val:
                    return val
            for v in payload.values():
                found = self._extract_model_id_from_payload(v)
                if found:
                    return found
        elif isinstance(payload, list):
            for item in payload:
                found = self._extract_model_id_from_payload(item)
                if found:
                    return found
        return None

    def _inject_models_into_cursor_available_models_payload(self, payload: Dict[str, Any], local_models: list[Dict[str, Any]]) -> int:
        # Try common field names while preserving upstream content.
        target_list = None
        for key in ("models", "available_models", "availableModels", "data"):
            val = payload.get(key)
            if isinstance(val, list):
                target_list = val
                break
        if target_list is None and isinstance(payload.get("result"), dict):
            result = payload["result"]
            for key in ("models", "available_models", "availableModels", "data"):
                val = result.get(key)
                if isinstance(val, list):
                    target_list = val
                    break
        if target_list is None:
            return 0

        existing_ids = set()
        for item in target_list:
            if isinstance(item, dict):
                mid = item.get("id") or item.get("model") or item.get("model_id") or item.get("modelId") or item.get("name")
                if isinstance(mid, str):
                    existing_ids.add(mid)

        added = 0
        for m in local_models:
            mid = m.get("id")
            if not mid or mid in existing_ids:
                continue
            target_list.append(
                {
                    "id": mid,
                    "name": m.get("name", mid),
                    "model": mid,
                    "owned_by": m.get("provider", "byok"),
                    "context_length": m.get("max_tokens", 0) or 0,
                }
            )
            existing_ids.add(mid)
            added += 1
        return added
