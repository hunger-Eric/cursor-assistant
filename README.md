# Cursor Assistant

MITM Proxy for enabling Chinese domestic AI models (DeepSeek, Qwen, GLM, Kimi) in Cursor IDE - works with **free tier**!

## Features
- MITM proxy to intercept Cursor API requests
- Support for Chinese domestic AI models
- Web management interface
- Docker deployment support

## Quick Start

`ash
# Start services
docker-compose up -d

# Access management interface
open http://localhost:8080
`

## Usage

1. Start the application
2. Download and install CA certificate
3. Configure system proxy to localhost:8080
4. Add your model provider in the web interface
5. Use Cursor with your preferred Chinese model!

## License
MIT
