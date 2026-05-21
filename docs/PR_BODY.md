## What Changed

- added Dockerized local deployment updates for backend, frontend, and MITM proxy ports
- added backend endpoints for proxy lifecycle, certificate download, and provider connectivity testing
- improved provider management and model listing behavior in the web UI
- added Cursor-native protobuf interception for `AiService/AvailableModels`
- merged local BYOK models into Cursor's native model list response
- added observability for Cursor native model-list traffic

## Why

The project previously handled only OpenAI-compatible JSON traffic. Cursor's current desktop client requests its model picker data from `aiserver.v1.AiService/AvailableModels` using protobuf, so local models could not appear unless that binary response was intercepted and rewritten.

## User Impact

- local deployment now exposes:
  - backend: `http://localhost:8000`
  - frontend: `http://localhost:13000`
  - MITM proxy: `127.0.0.1:18080`
- users can configure providers in the web UI and validate connectivity
- local BYOK models are now injected into Cursor's native protobuf model-list response

## Validation

- `docker compose up -d --build --force-recreate backend`
- `docker compose config -q`
- `npm run build`
- runtime verification through proxy logs:
  - observed `Content-Type: application/proto` for `AiService/AvailableM*`
  - observed repeated successful binary response injection

## Known Limitation

Although the proxy now injects custom models into Cursor's native protobuf model-list response, the free-tier Cursor client still does not surface those injected models as selectable in the UI. This indicates an additional client-side visibility gate beyond the server-provided model list.
