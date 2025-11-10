---
sidebar_position: 3
---

# Chat API

The Chat API is the core of W.W.H.D., handling message exchanges with Herman's AI agents. All endpoints require authentication.

## Send Message

### POST `/api/v1/chat/chat`

Send a message to Herman and receive a thoughtful response.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "string",
  "chat_id": number | null
}
```

**Response:**
```json
{
  "id": 2,
  "role": "assistant",
  "content": "Herman's response with wisdom and guidance...",
  "agent_used": "RouterAgent -> LibrarianAgent -> InterpreterAgent -> SafetyAgent",
  "routing_reason": "Intent classified as 'relationships' with 85% confidence",
  "sources": [
    {
      "title": "The Art of Balance",
      "url": "https://example.com/balance-guide",
      "timestamp": "2025-11-10T15:23:03Z"
    }
  ],
  "prompt_tokens": 245,
  "completion_tokens": 156,
  "total_tokens": 401,
  "response_time_ms": 1450,
  "created_at": "2025-11-10T15:23:03"
}
```

## Stream Response (Coming Soon)

### POST `/api/v1/chat/stream`

Stream Herman's response in real-time as tokens are generated.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
Accept: text/stream
```

**Response:** Server-Sent Events stream

```
data: {"type": "token", "content": "Finding"}
data: {"type": "token", "content": " balance"}
data: {"type": "token", "content": " in"}
data: {"type": "token", "content": " life..."}
data: {"type": "done", "sources": [...], "tokens": {...}}
```

## Chat Management

### GET `/api/v1/chat/chats`

List all chat conversations for the authenticated user.

**Response:**
```json
{
  "chats": [
    {
      "id": 1,
      "title": "Life Balance Discussion",
      "created_at": "2025-11-10T15:00:00",
      "updated_at": "2025-11-10T15:30:00",
      "message_count": 4
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### GET `/api/v1/chat/chats/{chat_id}/messages`

Get all messages in a specific chat conversation.

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What advice would Herman give about finding balance?",
      "created_at": "2025-11-10T15:20:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Finding balance is like walking the Middle Path...",
      "agent_used": "RouterAgent -> InterpreterAgent",
      "sources": [...],
      "created_at": "2025-11-10T15:20:03"
    }
  ],
  "total": 2,
  "chat_id": 1
}
```

## Agent Processing Flow

Every message goes through Herman's multi-agent system:

1. **RouterAgent** - Classifies intent and selects namespaces
   - Analyzes: relationships, money, business, feng_shui, diet_food, exercise_martial_arts, meditation, general
   - Confidence threshold: 0.7

2. **LibrarianAgent** - Retrieves relevant knowledge
   - Searches Qdrant vector database
   - Filters by selected namespaces
   - Returns top chunks with scores > 0.7

3. **InterpreterAgent** - Generates authentic response
   - Uses Herman's voice and personality
   - Integrates retrieved knowledge naturally
   - Includes practical, actionable advice

4. **SafetyAgent** - Applies guardrails
   - Content moderation and filtering
   - Auto-adds medical/financial disclaimers
   - Tone adjustment for respectful communication

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | number | Unique message ID |
| `role` | string | Always "assistant" for Herman's responses |
| `content` | string | Herman's response text |
| `agent_used` | string | Chain of agents that processed the message |
| `routing_reason` | string | Why this routing was chosen |
| `sources` | array | Knowledge base sources with citations |
| `prompt_tokens` | number | Input tokens used |
| `completion_tokens` | number | Output tokens generated |
| `total_tokens` | number | Total tokens for billing |
| `response_time_ms` | number | Processing time in milliseconds |
| `created_at` | string | ISO timestamp |

## Source Citations

Herman always provides sources for his wisdom:

```json
{
  "sources": [
    {
      "title": "The Way of the Shaolin Warrior",
      "url": "https://example.com/shaolin-wisdom",
      "timestamp": "2023-05-15T10:30:00Z",
      "relevance_score": 0.89,
      "excerpt": "Balance is found not in perfection, but in harmonious movement..."
    }
  ]
}
```

## Error Handling

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 422 Validation Error
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

### 500 Server Error
```json
{
  "id": null,
  "role": "assistant",
  "content": "I apologize, but I encountered an error processing your request. Please try again.",
  "agent_used": "",
  "routing_reason": null,
  "sources": [],
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "response_time_ms": 500,
  "created_at": "2025-11-10T15:23:03"
}
```

## Rate Limiting

- **Per User**: 100 requests per hour
- **Global**: 1000 requests per hour
- **Token Limit**: 50,000 tokens per user per day

## Best Practices

1. **Provide Context**: Include relevant background in your questions
2. **Be Specific**: Ask focused questions for better responses
3. **Use Chat Threads**: Continue conversations in the same chat_id
4. **Handle Errors**: Always check for error responses
5. **Respect Limits**: Monitor token usage for cost control

## Sample Integration

```javascript
class WWHDClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async sendMessage(content, chatId = null) {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        chat_id: chatId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    return response.json();
  }
}

// Usage
const client = new WWHDClient('http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com', 'your-token');
const response = await client.sendMessage('What would Herman say about morning routines?');
console.log(response.content);
```