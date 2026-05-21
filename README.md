# Cursor Assistant

MITM Proxy for experimenting with domestic AI model integration in Cursor.

## Features

- MITM proxy for intercepting Cursor network traffic
- web UI for provider management
- Docker deployment for backend, frontend, and proxy
- OpenAI-compatible model routing for BYOK providers
- native protobuf model-list injection for Cursor `AiService/AvailableModels`

## Local Ports

- backend: `http://localhost:8000`
- frontend: `http://localhost:13000`
- proxy: `127.0.0.1:18080`

## Quick Start

```bash
docker compose up -d --build
```

Then open:

- frontend: `http://localhost:13000`

## Provider Import

Do not commit runtime databases or secrets. Instead:

1. Copy `backend/providers.example.json` to `backend/providers.local.json`
2. Fill in your real keys locally
3. Import them with:

```bash
python backend/scripts/import_providers.py backend/providers.local.json
```

The local import file is intended to stay untracked.

## Current Status

- protobuf model-list injection is working
- custom models can be inserted into Cursor's native `AvailableModels` response
- the free-tier Cursor client still does not expose those injected models as selectable in the UI

See:

- `docs/TECHNICAL_FINDINGS.md`
- `docs/PR_BODY.md`

## License

MIT
