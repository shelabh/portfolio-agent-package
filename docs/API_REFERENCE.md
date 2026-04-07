# API Reference

## Python SDK

### `PortfolioAgent.from_settings()`

Create the supported agent using repository settings.

### `PortfolioAgent.add_text(content, source, ...)`

Chunk and index raw text.

### `PortfolioAgent.add_file(path, ...)`

Ingest and index a local file.

### `PortfolioAgent.add_github_repository(url, ...)`

Ingest and index a GitHub repository.

### `PortfolioAgent.add_website(url, ...)`

Ingest and index public website content.

### `PortfolioAgent.query(query, ...)`

Query the indexed corpus and receive a `RAGResponse`.

### `create_app(agent=None)`

Build the supported FastAPI wrapper around a `PortfolioAgent` instance.

## HTTP API

Base path: `/api/v1`

### `GET /health`

Returns basic liveness/readiness information for the SDK-backed app.

### `POST /query`

Request body:

```json
{
  "query": "What are the core skills?",
  "session_id": "demo",
  "max_results": 5,
  "include_sources": true
}
```

Supported fields:
- `query`
- `session_id`
- `user_id`
- `max_results`
- `include_sources`
- `persona`
- `metadata`

### `POST /documents`

Indexes raw text.

Example body:

```json
{
  "content": "Jane builds Python APIs with FastAPI.",
  "document_type": "txt",
  "source": "inline.txt"
}
```

### `POST /documents/file`

Indexes an uploaded file.

## Manual Verification

For a real end-to-end validation of the SDK and HTTP wrapper, use [MANUAL_E2E.md](MANUAL_E2E.md).
