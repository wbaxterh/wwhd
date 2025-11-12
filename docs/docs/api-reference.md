---
sidebar_position: 8
---

# API Reference

Complete documentation for all W.W.H.D. API endpoints with examples and Postman collection.

## Base URL
```
http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com
```

## Authentication

All chat endpoints require JWT Bearer token authentication. Obtain tokens through the authentication endpoints.

### Headers
```
Content-Type: application/json
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Health Check

### GET /health
Check API server health status.

**Request:**
```bash
curl http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-11T23:53:59.758377Z",
  "version": "0.1.0",
  "environment": "production"
}
```

---

## Authentication Endpoints

### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "YourPassword123",
  "name": "Your Display Name"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

**curl Example:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "name": "Test User"
  }'
```

**Success Response (201):**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-11T23:54:38"
}
```

**Error Response (422) - Validation Error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters"
    }
  ]
}
```

**Error Response (400) - User Exists:**
```json
{
  "detail": "Username or email already registered"
}
```

### POST /api/v1/auth/token
Authenticate user and get JWT access token.

**Request Body (Form-encoded):**
```
username=your_username&password=your_password
```

**curl Example:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123"
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Error Response (401):**
```json
{
  "detail": "Incorrect username or password"
}
```

---

## Chat Endpoints

### POST /api/v1/chat/chat
Send a message to Herman and get a response.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "content": "Your message to Herman",
  "chat_id": null
}
```

**Parameters:**
- `content` (string, required): The message content to send
- `chat_id` (string|null, required): Chat session ID, use `null` for new conversations

**curl Example:**
```bash
# First get a token
TOKEN=$(curl -s -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123" | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# Then send chat message
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "content": "Hello Herman, how are you?",
    "chat_id": null
  }'
```

**Success Response (200) - Current Live Response:**
```json
{
  "id": 2,
  "role": "assistant",
  "content": "I understand you're looking for guidance, but I'm not able to provide advice on that topic. If you're struggling with difficult thoughts, please reach out to a mental health professional or crisis helpline for support.",
  "agent_used": "general",
  "routing_reason": null,
  "sources": [],
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "response_time_ms": 11554,
  "created_at": "2025-11-11T23:55:17"
}
```

> **Note**: This is the actual response from our live system (tested Nov 11, 2025). The system is currently operational with OpenAI integration working and proper safety measures in place.

**Response Fields:**
- `id`: Unique message ID
- `role`: Always "assistant" for Herman's responses
- `content`: Herman's response message
- `agent_used`: Which agent processed the request (general, meditation, relationship, etc.)
- `routing_reason`: Why this agent was chosen (may be null)
- `sources`: Knowledge base sources used (array of source documents)
- `prompt_tokens`: OpenAI tokens used in the prompt
- `completion_tokens`: OpenAI tokens used in the response
- `total_tokens`: Total OpenAI tokens used
- `response_time_ms`: Processing time in milliseconds
- `created_at`: Timestamp of the response

**Error Response (401) - Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

**Error Response (422) - Missing Content:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "content"],
      "msg": "Field required"
    }
  ]
}
```

---

## Agent System

Herman uses a multi-agent system to route conversations to specialized handlers:

### Available Agents
- **general**: Default agent for general conversation
- **meditation**: Handles mindfulness and meditation-related questions
- **relationship**: Processes relationship advice and interpersonal questions
- **safety**: Filters and handles sensitive content appropriately

### Agent Routing
The system automatically routes messages to the appropriate agent based on content analysis. Users don't need to specify which agent to use.

---

## Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 200 | Success | Request processed successfully |
| 201 | Created | User registration successful |
| 400 | Bad Request | Duplicate username/email |
| 401 | Unauthorized | Invalid or expired token |
| 422 | Validation Error | Missing fields, invalid format |
| 500 | Server Error | Internal processing error |

---

## Rate Limits

Currently no rate limits are enforced, but this may change in production. Monitor your usage for optimal performance.

---

## Testing Tools

### Quick Test Script
```bash
#!/bin/bash
# Complete API test workflow

BASE_URL="http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com"

echo "1. Testing health check..."
curl -s "$BASE_URL/health" | jq

echo -e "\n2. Registering user..."
curl -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "apitest",
    "email": "apitest@example.com",
    "password": "ApiTest123",
    "name": "API Test User"
  }' | jq

echo -e "\n3. Getting token..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=apitest&password=ApiTest123" | \
  jq -r .access_token)

echo "Token: $TOKEN"

echo -e "\n4. Testing chat..."
curl -X POST "$BASE_URL/api/v1/chat/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "content": "Hello Herman!",
    "chat_id": null
  }' | jq
```

### JavaScript Example
```javascript
class WHHDClient {
  constructor(baseUrl = 'http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com') {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async register(username, email, password, name) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, name })
    });
    return await response.json();
  }

  async authenticate(username, password) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=${username}&password=${password}`
    });
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }

  async chat(content, chatId = null) {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify({ content, chat_id: chatId })
    });
    return await response.json();
  }
}

// Usage example
const client = new WHHDClient();
await client.authenticate('testuser', 'TestPass123');
const response = await client.chat('Hello Herman!');
console.log(response.content);
```

---

## Postman Collection

Download the complete Postman collection with pre-configured requests:

[Download WWHD.postman_collection.json](./WWHD.postman_collection.json)

### Import Instructions
1. Open Postman
2. Click "Import" button
3. Select the downloaded JSON file
4. Collection will be added with all endpoints configured
5. Set the `{{baseUrl}}` variable to `http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com`
6. Use the authentication endpoint to get a token, then copy to the Authorization header for chat requests

---

## Support

For API issues, check the [Troubleshooting Guide](./troubleshooting) or review [Working Sessions](./working-sessions) for detailed problem resolution examples.