# Technical Findings

## Confirmed Working

### 1. MITM and CA trust

- system proxy can point to `127.0.0.1:18080`
- the generated CA certificate can be trusted by the host and recognized by Cursor
- after trust was fixed, Cursor traffic to `api2.cursor.sh` and related endpoints flowed through the proxy without new TLS trust failures

### 2. OpenAI-compatible BYOK path

- `/v1/models` returns local models
- `/v1/chat/completions` can route a locally configured model to the configured upstream provider
- official upstream models remain passthrough when there is no local mapping

### 3. Cursor native model-list protocol

Cursor no longer relies only on JSON model-list APIs for the model picker.

Observed facts:

- endpoint family: `aiserver.v1.AiService/AvailableM*`
- response content type: `application/proto`
- payload format: raw protobuf, not JSON
- the proxy successfully decoded, modified, and re-encoded the binary response

Captured evidence:

- repeated log line: `Injected local models into Cursor AvailableModels binary response`

## Proto Structures Identified

Using Cursor's installed JS bundle, the following structures were identified and mirrored dynamically in Python:

- `aiserver.v1.AvailableModelsResponse`
- `aiserver.v1.AvailableModelsResponse.AvailableModel`
- `aiserver.v1.ModelDetails`
- `aiserver.v1.StreamUnifiedChatRequest`
- `aiserver.v1.StreamUnifiedChatRequestWithTools`
- `aiserver.v1.StreamUnifiedChatRequestWithToolsIdempotent`

This was enough to:

- detect the native model-list response format
- inject local models into the protobuf response body
- inspect model names from some native request shapes

## Real Blocking Point

The current blocker is not:

- Docker deployment
- CA trust
- MITM interception
- protobuf decoding
- protobuf model-list injection

The current blocker is:

- the free-tier Cursor client still does not show the injected custom models as selectable in the UI

This means the client has an additional visibility or entitlement gate beyond the raw `AvailableModels` response.

## What This Means

The project has already reached the point where:

- the proxy can place `sensenova-*` into Cursor's native model-list payload

But it has not reached the point where:

- the free-tier client exposes those injected models to the user as selectable options

## Safe Next Steps

- keep the protobuf model-list injection for protocol validation and observability
- keep provider configuration outside version control
- continue analysis of client-side gating only as product-compatibility diagnosis, not as a feature-bypass implementation
