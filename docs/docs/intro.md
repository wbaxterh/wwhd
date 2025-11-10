---
sidebar_position: 1
---

# W.W.H.D. API Documentation

Welcome to the **W.W.H.D.** (What Would Herman Do?) API documentation. This is a multi-agent Shaolin/TCM companion system powered by LangChain/LangGraph orchestration and RAG (Retrieval-Augmented Generation).

## What is W.W.H.D.?

W.W.H.D. is an AI-powered chat system that provides wisdom and guidance in the style of Herman Siu, combining traditional Chinese medicine, Shaolin philosophy, and practical life advice. The system uses multiple specialized agents that work together to provide thoughtful, well-researched responses.

## Architecture Overview

### Multi-Agent System
- **RouterAgent**: Classifies user intent and routes to appropriate specialists
- **LibrarianAgent**: Retrieves relevant knowledge from vector database
- **InterpreterAgent**: Generates responses in Herman's authentic voice
- **SafetyAgent**: Applies content moderation and safety guardrails

### Technology Stack
- **Backend**: FastAPI with LangChain/LangGraph orchestration
- **Vector Database**: Qdrant with namespaced collections
- **Chat History**: SQLite with ACID compliance
- **Authentication**: JWT-based user management
- **Deployment**: AWS ECS Fargate with Application Load Balancer

## Live API

The W.W.H.D. backend is deployed and accessible at:
- **Base URL**: `http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com`
- **Health Check**: [/health](http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/health)
- **Interactive Docs**: `/docs` (disabled in production)

## Getting Started

1. **Register a user account** using the `/api/v1/auth/register` endpoint
2. **Get an authentication token** using the `/api/v1/auth/token` endpoint
3. **Send chat messages** using the `/api/v1/chat/chat` endpoint
4. **Stream responses** using the `/api/v1/chat/stream` endpoint (optional)

## Quick Example

```bash
# 1. Register user
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "SecurePass123!", "name": "Test User"}'

# 2. Get token
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePass123!"

# 3. Send chat message
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"content": "What advice would Herman give about finding balance in life?", "chat_id": null}'
```

## Response Features

Every response includes:
- **Herman's authentic voice** and personality
- **Source citations** from the knowledge base with timestamps
- **Agent routing information** showing which specialists were involved
- **Token usage tracking** for cost monitoring
- **Safety guardrails** with automatic disclaimers for medical/financial advice

## Navigation

- **[Authentication](./authentication)** - User registration and JWT tokens
- **[Chat API](./chat-api)** - Core messaging endpoints
- **[Examples](./examples)** - Request/response examples
- **[Setup](./setup)** - Development and deployment guides
