# Portfolio Agent API Reference

This document provides comprehensive API documentation for the Portfolio Agent system.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses API key authentication. Include your API key in the request headers:

```http
Authorization: Bearer your-api-key-here
```

## Endpoints

### Health Check

#### GET /health

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-27T10:00:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "dependencies": {
    "database": {"status": "healthy", "details": "PostgreSQL connection OK"},
    "redis": {"status": "healthy", "details": "Redis connection OK"},
    "llm_provider": {"status": "healthy", "details": "OpenAI API reachable"},
    "vector_store": {"status": "healthy", "details": "FAISS index loaded"}
  }
}
```

#### GET /ready

Check if the service is ready to receive traffic.

**Response:**
```json
{
  "status": "ready"
}
```

### Query Endpoints

#### POST /query

Send a query to the RAG agent and get a response.

**Request Body:**
```json
{
  "query": "What are your main technical skills?",
  "user_id": "user123",
  "session_id": "session456",
  "stream": false
}
```

**Response:**
```json
{
  "response": "I have extensive experience with Python, JavaScript, and machine learning...",
  "citations": ["doc1.pdf", "github_repo_link"],
  "metadata": {
    "confidence": 0.95,
    "processing_time": 1.2,
    "sources_used": 3
  }
}
```

#### POST /query/stream

Send a query and stream the response in real-time.

**Request Body:**
```json
{
  "query": "Tell me about your recent projects",
  "user_id": "user123",
  "session_id": "session456",
  "stream": true
}
```

**Response:** Server-Sent Events stream
```
data: {"chunk": "I've worked on several interesting projects recently..."}

data: {"chunk": " including a machine learning application..."}

event: end
data: {}
```

### Document Management

#### POST /documents/upload

Upload and ingest a document into the vector store.

**Request:** Multipart form data
- `file`: The document file (PDF, TXT, DOCX, etc.)
- `metadata`: JSON string with document metadata (optional)

**Response:**
```json
{
  "status": "success",
  "document_id": "doc_uuid_123",
  "message": "Document 'resume.pdf' received and queued for ingestion."
}
```

#### POST /documents/ingest_url

Ingest a document from a URL.

**Request Body:**
```json
{
  "url": "https://github.com/user/repo",
  "metadata": {
    "source": "github",
    "tags": ["python", "machine-learning"],
    "filename": "repository"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "document_id": "doc_uuid_456",
  "message": "URL 'https://github.com/user/repo' received and queued for ingestion."
}
```

#### POST /documents/search

Search for documents in the vector store.

**Request Body:**
```json
{
  "query": "machine learning projects",
  "k": 5,
  "filter_metadata": {
    "source": "github",
    "tags": ["python"]
  }
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc_uuid_123",
      "content_snippet": "This project implements a machine learning pipeline...",
      "score": 0.85,
      "metadata": {
        "source": "github",
        "filename": "ml_project.py",
        "tags": ["python", "machine-learning"]
      }
    }
  ],
  "total_results": 10
}
```

### Agent Management

#### GET /agents/{user_id}/state

Get the current conversation state for a user.

**Path Parameters:**
- `user_id`: The user identifier

**Query Parameters:**
- `session_id`: Optional session identifier

**Response:**
```json
{
  "user_id": "user123",
  "session_id": "session456",
  "messages": [
    {
      "role": "user",
      "content": "What are your skills?",
      "timestamp": "2024-01-27T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I have experience with Python, JavaScript...",
      "timestamp": "2024-01-27T10:00:01Z"
    }
  ],
  "current_intent": "direct",
  "tools_used": [],
  "last_updated": "2024-01-27T10:00:01Z"
}
```

#### DELETE /agents/{user_id}/state

Clear the conversation state for a user.

**Path Parameters:**
- `user_id`: The user identifier

**Query Parameters:**
- `session_id`: Optional session identifier

**Response:** 204 No Content

### Metrics

#### GET /metrics

Get application metrics.

**Response:**
```json
[
  {
    "metric_name": "quality_response_accuracy",
    "value": 0.95,
    "timestamp": "2024-01-27T10:00:00Z",
    "labels": {"model": "gpt-3.5-turbo"}
  },
  {
    "metric_name": "performance_avg_response_time",
    "value": 1.2,
    "timestamp": "2024-01-27T10:00:00Z",
    "labels": {"endpoint": "/query"}
  }
]
```

#### GET /metrics/prometheus

Get metrics in Prometheus format.

**Response:** Plain text in Prometheus format
```
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{version="3.13.5"} 1
# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
app_requests_total 100
```

### Security

#### POST /security/detect_pii

Detect PII in text.

**Request Body:**
```json
{
  "text": "My email is john.doe@example.com and my phone is 555-123-4567"
}
```

**Response:**
```json
{
  "text": "My email is john.doe@example.com and my phone is 555-123-4567",
  "pii_entities": [
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 12,
      "end": 32,
      "value": "john.doe@example.com",
      "confidence": 0.95
    },
    {
      "entity_type": "PHONE_NUMBER",
      "start": 45,
      "end": 58,
      "value": "555-123-4567",
      "confidence": 0.90
    }
  ]
}
```

#### POST /security/redact_pii

Redact PII in text.

**Request Body:**
```json
{
  "text": "My email is john.doe@example.com and my phone is 555-123-4567"
}
```

**Response:**
```json
{
  "original_text": "My email is john.doe@example.com and my phone is 555-123-4567",
  "redacted_text": "My email is [EMAIL_ADDRESS] and my phone is [PHONE_NUMBER]",
  "detections": [
    {
      "entity_type": "EMAIL_ADDRESS",
      "start": 12,
      "end": 32,
      "value": "john.doe@example.com",
      "confidence": 0.95
    }
  ]
}
```

#### GET /security/audit_logs

Get audit logs.

**Query Parameters:**
- `event_type`: Filter by event type (optional)
- `user_id`: Filter by user ID (optional)
- `limit`: Maximum number of logs to return (default: 100)

**Response:**
```json
[
  {
    "event_id": "evt_123",
    "event_type": "AUTHENTICATION",
    "severity": "info",
    "message": "User login successful",
    "timestamp": "2024-01-27T10:00:00Z",
    "user_id": "user123",
    "ip_address": "192.168.1.1",
    "details": {
      "login_method": "api_key",
      "session_duration": 3600
    }
  }
]
```

#### POST /security/consent

Record user consent for data processing.

**Request Body:**
```json
{
  "subject_id": "user123",
  "data_categories": ["PERSONAL_DATA", "BEHAVIORAL_DATA"],
  "processing_purposes": ["ANALYTICS", "PERSONALIZATION"]
}
```

**Response:**
```json
{
  "consent_id": "consent_456",
  "subject_id": "user123",
  "data_categories": ["PERSONAL_DATA", "BEHAVIORAL_DATA"],
  "processing_purposes": ["ANALYTICS", "PERSONALIZATION"],
  "consent_given": true,
  "timestamp": "2024-01-27T10:00:00Z",
  "expires_at": "2025-01-27T10:00:00Z"
}
```

#### GET /security/consent/{subject_id}

Get consent records for a subject.

**Path Parameters:**
- `subject_id`: The subject identifier

**Response:**
```json
[
  {
    "consent_id": "consent_456",
    "subject_id": "user123",
    "data_categories": ["PERSONAL_DATA", "BEHAVIORAL_DATA"],
    "processing_purposes": ["ANALYTICS", "PERSONALIZATION"],
    "consent_given": true,
    "timestamp": "2024-01-27T10:00:00Z",
    "expires_at": "2025-01-27T10:00:00Z"
  }
]
```

### Admin

#### POST /admin/command

Execute administrative commands.

**Request Body:**
```json
{
  "command": "reload_config",
  "parameters": {}
}
```

**Available Commands:**
- `reload_config`: Reload configuration
- `purge_data`: Purge data (with scope parameter)
- `restart_service`: Restart the service

**Response:**
```json
{
  "status": "success",
  "message": "Configuration reloaded successfully.",
  "details": {
    "new_settings_version": "1.0.0"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: 100 requests per hour"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Default**: 100 requests per hour per IP address
- **Headers**: Rate limit information is included in response headers:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## WebSocket Support

For real-time communication, the API supports WebSocket connections:

### WebSocket Endpoint
```
ws://localhost:8000/ws
```

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};
```

### Message Format
```json
{
  "type": "query",
  "data": {
    "query": "What are your skills?",
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

## SDKs and Libraries

### Python SDK
```python
from portfolio_agent import PortfolioAgent

client = PortfolioAgent(api_key="your-api-key")

# Send a query
response = client.query("What are your skills?")
print(response.response)

# Upload a document
result = client.upload_document("path/to/document.pdf")
print(result.document_id)
```

### JavaScript SDK
```javascript
import { PortfolioAgent } from 'portfolio-agent-sdk';

const client = new PortfolioAgent({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:8000/api/v1'
});

// Send a query
const response = await client.query('What are your skills?');
console.log(response.response);

// Upload a document
const result = await client.uploadDocument('path/to/document.pdf');
console.log(result.document_id);
```

## Examples

### Complete Workflow Example

```python
import requests

# 1. Check health
response = requests.get('http://localhost:8000/api/v1/health')
print(response.json())

# 2. Upload a document
with open('resume.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/api/v1/documents/upload', files=files)
    print(response.json())

# 3. Search documents
search_data = {
    'query': 'Python experience',
    'k': 5
}
response = requests.post('http://localhost:8000/api/v1/documents/search', json=search_data)
print(response.json())

# 4. Send a query
query_data = {
    'query': 'What are your main technical skills?',
    'user_id': 'user123',
    'session_id': 'session456'
}
response = requests.post('http://localhost:8000/api/v1/query', json=query_data)
print(response.json())
```

## Changelog

### Version 1.0.0
- Initial API release
- Basic query and document management endpoints
- Security and audit logging
- Admin commands
- Metrics and monitoring

## Support

For API support and questions:
- Check the main documentation
- Review the examples
- Contact the development team
