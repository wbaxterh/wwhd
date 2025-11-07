# API Specification

## Base Configuration

```yaml
api:
  version: v1
  base_url: https://api.wwhd.ai
  timeout: 30s
  max_request_size: 10MB
  rate_limits:
    anonymous: 10/min
    authenticated: 60/min
    admin: unlimited
```

## Authentication Endpoints

### POST /auth/signup

**Description**: Create new user account

**Request**:
```json
{
  "email": "user@example.com",
  "username": "herman_fan",
  "password": "SecurePassword123!"
}
```

**Response (201)**:
```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "username": "herman_fan",
    "role": "user",
    "created_at": "2024-01-20T10:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  }
}
```

### POST /auth/login

**Description**: Authenticate user

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200)**:
```json
{
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 3600
  },
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "herman_fan",
    "role": "user"
  }
}
```

### POST /auth/refresh

**Description**: Refresh access token

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

### POST /auth/logout

**Description**: Invalidate refresh token

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200)**:
```json
{
  "message": "Logged out successfully"
}
```

## User Endpoints

### GET /me

**Description**: Get current user profile

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200)**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "herman_fan",
  "role": "user",
  "settings": {
    "preferred_model": "gpt-4o-mini",
    "theme": "dark",
    "notifications": true
  },
  "usage": {
    "tokens_used_today": 5420,
    "tokens_limit_daily": 100000,
    "estimated_cost_today": 0.0542
  },
  "created_at": "2024-01-20T10:30:00Z",
  "last_login": "2024-01-25T14:20:00Z"
}
```

### PATCH /me

**Description**: Update user settings

**Request**:
```json
{
  "settings": {
    "theme": "light",
    "notifications": false
  }
}
```

**Response (200)**:
```json
{
  "message": "Settings updated",
  "settings": {
    "preferred_model": "gpt-4o-mini",
    "theme": "light",
    "notifications": false
  }
}
```

## Chat Endpoints

### POST /chat (SSE Streaming)

**Description**: Send message and receive streaming response

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: text/event-stream
```

**Request**:
```json
{
  "message": "What does Herman say about building wealth?",
  "session_id": "456e7890-...",  // Optional, creates new if not provided
  "preferred_agent": "money",  // Optional hint
  "stream": true
}
```

**SSE Response Stream**:
```
event: start
data: {"session_id": "456e7890-...", "message_id": "789abc..."}

event: token
data: {"content": "According"}

event: token
data: {"content": " to"}

event: token
data: {"content": " Herman"}

event: citation
data: {"citations": [{"title": "Herman on Wealth", "url": "https://...", "timestamp": "00:15:30"}]}

event: metadata
data: {"tokens_used": 450, "namespaces": ["money", "business"], "processing_time": 2.3}

event: done
data: {"message_id": "789abc...", "complete": true}
```

### POST /chat (WebSocket Alternative)

**Description**: WebSocket connection for bidirectional chat

**Connection**: `wss://api.wwhd.ai/ws/chat`

**Authentication**:
```json
{
  "type": "auth",
  "token": "<access_token>"
}
```

**Message Format**:
```json
{
  "type": "message",
  "content": "What about real estate investing?",
  "session_id": "456e7890-..."
}
```

**Response Format**:
```json
{
  "type": "token",
  "content": "Real"
}
```

### GET /chat/sessions

**Description**: List user's chat sessions

**Query Parameters**:
- `limit` (int): Max results (default: 20)
- `offset` (int): Pagination offset
- `active` (bool): Filter active sessions only

**Response (200)**:
```json
{
  "sessions": [
    {
      "id": "456e7890-...",
      "title": "Building Wealth Discussion",
      "created_at": "2024-01-25T10:00:00Z",
      "last_activity": "2024-01-25T10:30:00Z",
      "message_count": 12,
      "is_active": true
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### GET /chat/sessions/:id/messages

**Description**: Get messages for a session

**Response (200)**:
```json
{
  "session_id": "456e7890-...",
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "How do I start investing?",
      "created_at": "2024-01-25T10:00:00Z"
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "Herman teaches that wealth building starts with...",
      "citations": [
        {
          "title": "Herman's Investment Guide",
          "url": "https://youtube.com/watch?v=...",
          "timestamp": "00:05:20"
        }
      ],
      "created_at": "2024-01-25T10:00:05Z",
      "tokens": {
        "prompt": 150,
        "completion": 320
      }
    }
  ]
}
```

### DELETE /chat/sessions/:id

**Description**: Delete a chat session

**Response (200)**:
```json
{
  "message": "Session deleted",
  "id": "456e7890-..."
}
```

## Admin Endpoints

### POST /admin/documents/upload

**Description**: Upload document for processing

**Headers**:
```
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**Request**:
```
POST /admin/documents/upload
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="herman_transcript.txt"
Content-Type: text/plain

[file contents]
------WebKitFormBoundary
Content-Disposition: form-data; name="namespace"

money
------WebKitFormBoundary
Content-Disposition: form-data; name="metadata"

{"source_url": "https://youtube.com/..." , "source_title": "Herman on Wealth"}
------WebKitFormBoundary--
```

**Response (201)**:
```json
{
  "document_id": "doc_123",
  "status": "pending",
  "filename": "herman_transcript.txt",
  "file_size": 45678,
  "namespace": "money",
  "created_at": "2024-01-25T15:00:00Z"
}
```

### POST /admin/documents/:id/index

**Description**: Process and index document

**Request**:
```json
{
  "chunk_size": 1500,
  "chunk_overlap": 200,
  "force_reindex": false
}
```

**Response (200)**:
```json
{
  "document_id": "doc_123",
  "status": "processing",
  "estimated_time": 30,
  "job_id": "job_456"
}
```

### GET /admin/documents/:id/status

**Description**: Check document processing status

**Response (200)**:
```json
{
  "document_id": "doc_123",
  "status": "indexed",
  "chunks_created": 25,
  "tokens_processed": 8500,
  "processing_time": 28.5,
  "indexed_at": "2024-01-25T15:01:00Z"
}
```

### GET /admin/documents

**Description**: List documents

**Query Parameters**:
- `namespace` (string): Filter by namespace
- `status` (string): Filter by status
- `limit` (int): Results per page
- `offset` (int): Pagination offset

**Response (200)**:
```json
{
  "documents": [
    {
      "id": "doc_123",
      "title": "Herman on Wealth Building",
      "namespace": "money",
      "source_platform": "youtube",
      "status": "indexed",
      "chunk_count": 25,
      "token_count": 8500,
      "created_at": "2024-01-25T15:00:00Z",
      "indexed_at": "2024-01-25T15:01:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### DELETE /admin/documents/:id

**Description**: Delete document and its chunks

**Response (200)**:
```json
{
  "message": "Document deleted",
  "chunks_removed": 25,
  "vectors_deleted": 25
}
```

### POST /admin/namespaces/:name/reindex

**Description**: Reindex entire namespace

**Response (202)**:
```json
{
  "namespace": "money",
  "job_id": "reindex_789",
  "documents_queued": 42,
  "estimated_time": 300
}
```

### GET /admin/stats

**Description**: Get system statistics

**Response (200)**:
```json
{
  "users": {
    "total": 1250,
    "active_today": 342,
    "new_this_week": 89
  },
  "usage": {
    "tokens_today": 2500000,
    "estimated_cost_today": 25.00,
    "messages_today": 8500
  },
  "content": {
    "total_documents": 450,
    "total_chunks": 12500,
    "namespaces": [
      {"name": "money", "documents": 85, "chunks": 2500},
      {"name": "relationships", "documents": 62, "chunks": 1800}
    ]
  },
  "performance": {
    "avg_response_time": 2.3,
    "p95_response_time": 4.8,
    "router_accuracy": 0.83
  }
}
```

## Health & Monitoring

### GET /health

**Description**: Basic health check

**Response (200)**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-25T16:00:00Z"
}
```

### GET /health/detailed

**Description**: Detailed health status

**Response (200)**:
```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "qdrant": {
      "status": "healthy",
      "collections": 8,
      "total_points": 12500
    },
    "openai": {
      "status": "healthy",
      "latency_ms": 120
    },
    "redis": {
      "status": "healthy",
      "memory_used_mb": 45
    }
  },
  "metrics": {
    "uptime_seconds": 864000,
    "requests_per_second": 12.5,
    "active_connections": 45
  }
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2024-01-25T16:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid request parameters |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Temporary outage |

## Rate Limiting

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706198400
```

**429 Response**:
```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "retry_after": 30
  }
}
```

## CORS Configuration

```yaml
cors:
  allowed_origins:
    - https://wwhd.ai
    - https://app.wwhd.ai
    - http://localhost:3000  # Development
  allowed_methods:
    - GET
    - POST
    - PATCH
    - DELETE
    - OPTIONS
  allowed_headers:
    - Authorization
    - Content-Type
    - X-Request-ID
  expose_headers:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining
    - X-RateLimit-Reset
  max_age: 86400
```

## OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: W.W.H.D. API
  version: 1.0.0
  description: Multi-agent Shaolin/TCM companion with RAG
servers:
  - url: https://api.wwhd.ai/v1
    description: Production
  - url: http://localhost:8000/v1
    description: Development
security:
  - bearerAuth: []
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Acceptance Criteria

- ✅ All endpoints return consistent JSON format
- ✅ Authentication required for protected routes
- ✅ Rate limiting enforced per user/IP
- ✅ SSE streaming for chat responses
- ✅ File upload limited to 10MB
- ✅ Proper CORS headers for web clients
- ✅ Request ID tracking for debugging
- ✅ OpenAPI documentation generated