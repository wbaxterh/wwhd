---
sidebar_position: 4
---

# Request/Response Examples

This page provides real-world examples of interacting with the W.W.H.D. API, including the actual responses you can expect from Herman's agents.

## Complete Flow Example

Here's a complete authentication and chat flow:

### 1. Register User

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "herman_seeker",
    "email": "seeker@example.com",
    "password": "WisdomPath123!",
    "name": "Wisdom Seeker"
  }'
```

**Response:**
```json
{
  "id": 3,
  "email": "seeker@example.com",
  "username": "herman_seeker",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-10T16:45:22"
}
```

### 2. Get Authentication Token

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=herman_seeker&password=WisdomPath123!"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6Imhlcm1hbl9zZWVrZXIiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTczMTM0MDA5Mn0.mY8kSZB2vCfJH0X_P8qN3rLc9Vx4WzBn5A7dK2pH8sE",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 3. Send Chat Message

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6Imhlcm1hbl9zZWVrZXIiLCJpc19hZG1pbiI6ZmFsc2UsImV4cCI6MTczMTM0MDA5Mn0.mY8kSZB2vCfJH0X_P8qN3rLc9Vx4WzBn5A7dK2pH8sE" \
  -d '{
    "content": "What advice would Herman give about finding balance between work and family life?",
    "chat_id": null
  }'
```

**Response (when OpenAI key is configured):**
```json
{
  "id": 5,
  "role": "assistant",
  "content": "Finding balance between work and family is like mastering the art of Tai Chi - it requires constant, mindful adjustment rather than rigid structure.\n\nFrom the Shaolin perspective, true balance comes from understanding that work and family are not opposing forces, but complementary energies that flow together. Think of them as yin and yang - each supporting and defining the other.\n\nHere are some practical steps:\n\n**Set Sacred Boundaries**: Just as a monk has specific times for meditation, establish clear 'family time' that is protected from work intrusions. Your phone can wait, but your child's bedtime story cannot.\n\n**Practice Present Moment Awareness**: When you're at work, be fully at work. When you're with family, be completely present. Half-hearted attention serves neither well.\n\n**Apply the 80/20 Principle**: Focus your work energy on the 20% of tasks that create 80% of your results. This efficiency creates space for what truly matters - your loved ones.\n\n**Remember Your 'Why'**: You work to support your family's wellbeing, not to escape from it. Let this deeper purpose guide your daily choices.\n\nBalance is not a destination you reach, but a practice you cultivate daily with wisdom and compassion.\n\n*[Medical/Legal Disclaimer: This advice is for general guidance only and should not replace professional counseling or legal advice.]*",
  "agent_used": "RouterAgent -> LibrarianAgent -> InterpreterAgent -> SafetyAgent",
  "routing_reason": "Intent classified as 'relationships' and 'general' with 82% confidence. Selected namespaces: relationships, general",
  "sources": [
    {
      "title": "The Middle Path: Balancing Life's Demands",
      "url": "https://wisdom.herman-siu.com/balance-guide",
      "timestamp": "2024-08-15T10:30:00Z",
      "relevance_score": 0.87,
      "excerpt": "True balance comes not from perfect division of time, but from mindful presence..."
    },
    {
      "title": "Shaolin Wisdom for Modern Living",
      "url": "https://shaolin-wisdom.com/modern-applications",
      "timestamp": "2024-06-20T14:22:00Z",
      "relevance_score": 0.81,
      "excerpt": "The monk understands that discipline in one area creates freedom in another..."
    }
  ],
  "prompt_tokens": 267,
  "completion_tokens": 245,
  "total_tokens": 512,
  "response_time_ms": 1850,
  "created_at": "2025-11-10T16:48:15"
}
```

**Response (without OpenAI key - current state):**
```json
{
  "id": 2,
  "role": "assistant",
  "content": "I apologize, but I encountered an error processing your request. Please try again.",
  "agent_used": "",
  "routing_reason": null,
  "sources": [],
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "response_time_ms": 703,
  "created_at": "2025-11-10T15:23:03"
}
```

## Different Topic Examples

### Traditional Chinese Medicine Question

**Request:**
```json
{
  "content": "What herbs would Herman recommend for better sleep and relaxation?",
  "chat_id": null
}
```

**Expected Response:**
```json
{
  "id": 6,
  "role": "assistant",
  "content": "For peaceful sleep and deep relaxation, traditional Chinese medicine offers gentle, time-tested remedies that work with your body's natural rhythms.\n\n**Jujube (Da Zao)**: These sweet red dates calm the shen (spirit) and nourish the blood. I often recommend eating 3-5 dates an hour before bed, or brewing them into a warm tea.\n\n**Schisandra Berry (Wu Wei Zi)**: Known as the 'five-flavor fruit,' it harmonizes all organ systems and reduces stress-related sleep disturbances. Take as a tincture or powder.\n\n**Reishi Mushroom (Ling Zhi)**: Called the 'mushroom of immortality,' it calms the mind without causing drowsiness during the day. Perfect for long-term use.\n\n**Chrysanthemum Tea (Ju Hua)**: Cools excess heat in the liver that often causes restless sleep. Drink warm in the evening.\n\n**Ancient Wisdom**: The Chinese say 'yang enters yin' at sunset. Support this natural transition by dimming lights, avoiding screens, and creating a calm environment.\n\nRemember: quality sleep is not luxury - it's the foundation of health, clear thinking, and emotional balance.\n\n*[Medical Disclaimer: Consult with a qualified TCM practitioner or healthcare provider before starting any herbal regimen, especially if you have medical conditions or take medications.]*",
  "agent_used": "RouterAgent -> LibrarianAgent -> InterpreterAgent -> SafetyAgent",
  "routing_reason": "Intent classified as 'diet_food' and 'meditation' with 91% confidence",
  "sources": [...],
  "prompt_tokens": 234,
  "completion_tokens": 312,
  "total_tokens": 546,
  "response_time_ms": 2100
}
```

### Feng Shui Question

**Request:**
```json
{
  "content": "How can I improve the energy flow in my home office according to feng shui principles?",
  "chat_id": null
}
```

**Expected Response:**
```json
{
  "id": 7,
  "role": "assistant",
  "content": "Creating harmonious chi flow in your workspace is essential for productivity and well-being. Here's how to optimize your home office energy:\n\n**The Command Position**: Place your desk so you can see the door while working, but not directly in line with it. This creates a sense of control and security - fundamental for clear thinking.\n\n**Clear the Clutter**: Stagnant energy follows cluttered spaces. Keep only what serves your current projects visible. Store the rest mindfully.\n\n**Balance the Five Elements**:\n- **Wood** (growth): Add a small plant or wooden desk accessories\n- **Fire** (inspiration): Use warm lighting, avoid harsh fluorescents  \n- **Earth** (stability): Incorporate yellow/brown tones, crystals, or ceramics\n- **Metal** (precision): Include white colors, metal frames, or a small bell\n- **Water** (flow): A small water feature or mirror can activate prosperity\n\n**Direction Matters**: If possible, face your 'success direction' based on your Kua number. East or Southeast often enhance career energy.\n\n**Sacred Space**: Create one corner dedicated to inspiration - perhaps a small altar with meaningful objects, or simply a beautiful image that uplifts your spirit.\n\nRemember: your environment shapes your energy, which shapes your success. Treat your workspace as a temple of productivity.",
  "agent_used": "RouterAgent -> LibrarianAgent -> InterpreterAgent -> SafetyAgent",
  "routing_reason": "Intent classified as 'feng_shui' with 94% confidence",
  "sources": [...],
  "response_time_ms": 1950
}
```

## Error Examples

### Missing Authentication

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello Herman", "chat_id": null}'
```

**Response:**
```json
{
  "detail": "Not authenticated"
}
```

### Invalid Token

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid-token-123" \
  -d '{"content": "Hello Herman", "chat_id": null}'
```

**Response:**
```json
{
  "detail": "Could not validate credentials"
}
```

### Missing Required Field

**Request:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer valid-token" \
  -d '{"chat_id": null}'
```

**Response:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "content"],
      "msg": "Field required",
      "input": {"chat_id": null}
    }
  ]
}
```

## Complete API Documentation

For comprehensive API documentation with detailed Postman collection, see [API Reference](./api-reference).

### Quick Postman Import

Download the complete Postman collection: [WWHD.postman_collection.json](./WWHD.postman_collection.json)

The collection includes:
- Automatic token management
- Pre-configured test scenarios
- Example requests for all endpoints
- Environment variables setup
- Complete workflow testing

## JavaScript/TypeScript Client

```typescript
interface WWHDResponse {
  id: number;
  role: string;
  content: string;
  agent_used: string;
  routing_reason: string | null;
  sources: Array<{
    title: string;
    url: string;
    timestamp: string;
    relevance_score?: number;
    excerpt?: string;
  }>;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  response_time_ms: number;
  created_at: string;
}

class WWHDClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async authenticate(username: string, password: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ username, password }),
    });

    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.status}`);
    }

    const data = await response.json();
    this.token = data.access_token;
    return this.token;
  }

  async sendMessage(content: string, chatId?: number): Promise<WWHDResponse> {
    if (!this.token) {
      throw new Error('Must authenticate first');
    }

    const response = await fetch(`${this.baseUrl}/api/v1/chat/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        chat_id: chatId || null,
      }),
    });

    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }

    return response.json();
  }
}

// Usage example
const client = new WWHDClient('http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com');
await client.authenticate('herman_seeker', 'WisdomPath123!');
const response = await client.sendMessage('What would Herman say about morning meditation?');
console.log(response.content);
```