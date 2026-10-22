# Pixel Art Studio

An MCP server + web app for creating true pixel art programmatically with AI agents.

## Components

- **mcp-server** — Python MCP server (HTTP/SSE transport) giving AI agents pixel-level canvas control
- **web-api** — FastAPI backend bridging MinIO object storage and PostgreSQL metadata
- **web-ui** — React/TypeScript pixel editor and sprite gallery

## Stack

- Python, MCP SDK, Pillow, imageio, boto3
- FastAPI, asyncpg
- React, TypeScript, Vite
- MinIO (S3-compatible object storage)
- PostgreSQL
- Docker Compose

## Getting Started

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Web UI | http://localhost:3000 |
| Web API | http://localhost:8000 |
| MCP Server | http://localhost:8001/sse |
| MinIO Console | http://localhost:9001 |

## MCP Setup (Claude Desktop)

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pixel-art": {
      "url": "http://localhost:8001/sse"
    }
  }
}
```

## Upgrading to AWS S3

Change env vars in `docker-compose.yml` — no code changes required:

```
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=<aws-access-key>
MINIO_SECRET_KEY=<aws-secret>
MINIO_USE_SSL=true
```
