# MVP Implementation Plan - W.W.H.D.

## Architecture Overview

### Current Infrastructure (✅ Deployed)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALB Load Balancer                        │
│              wwhd-alb-xxx.elb.amazonaws.com                │
└─────────────────────────┬───────────────────────────────────┘
                         │
┌─────────────────────────▼───────────────────────────────────┐
│                 ECS Fargate Task                           │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐│
│  │   FastAPI Container │  │     Qdrant Container            ││
│  │                     │  │                                 ││
│  │ • LangChain/Graph   │  │ • Vector embeddings             ││
│  │ • Orchestrator      │  │ • Namespaced collections:       ││
│  │ • Specialist Agents │  │   - relationships               ││
│  │ • Tools per agent   │  │   - money                       ││
│  │ • Chat API          │  │   - feng_shui                   ││
│  │                     │  │   - tcm_herbs                   ││
│  └─────────────────────┘  └─────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────┘
                         │
┌─────────────────────────▼───────────────────────────────────┐
│                    EFS Storage                              │
│  /data/wwhd.db (SQLite) + /qdrant/storage (Vectors)       │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Orchestration** | LangGraph | Stateful multi-agent workflows with routing |
| **LLM Framework** | LangChain | Model invocation and tool management |
| **LLMs** | OpenAI / OpenRouter | Flexible model selection |
| **Vector DB** | Qdrant | Namespaced collections for agent-specific knowledge |
| **Chat History** | SQLite on EFS | Fast queries (1-2ms), ACID compliance |
| **Backend API** | FastAPI | Async, WebSocket support for streaming |
| **Infrastructure** | ECS Fargate + EFS | Managed containers with persistent storage |
| **CI/CD** | GitHub Actions | 3-minute push-to-deploy pipeline |

### Storage Decision: SQLite on EFS

| Option | Latency | Consistency | Cost | Complexity |
|--------|---------|-------------|------|------------|
| **EFS (Selected)** | ~1-2ms | ACID | ~$3/month | Simple |
| S3 | ~50-200ms | Eventually consistent | ~$1/month | Complex |

**Why EFS:**
- Fast reads for chat history queries
- ACID compliance for session integrity
- Shared access across multiple ECS tasks
- Auto-scaling with data growth

## Multi-Repository Strategy

```
📁 wwhd/ (Backend - This repo)
├── backend/
│   ├── agents/                 # LangGraph agent implementations
│   │   ├── orchestrator.py     # Main routing agent
│   │   ├── tcm_specialist.py   # Traditional Chinese Medicine
│   │   ├── relationship.py     # Relationship counseling
│   │   ├── money.py           # Financial wisdom
│   │   └── feng_shui.py       # Feng Shui guidance
│   ├── api/                    # FastAPI endpoints
│   │   ├── chat.py            # Chat completion endpoint
│   │   ├── websocket.py       # Streaming responses
│   │   └── health.py          # Health checks
│   ├── rag/                    # Qdrant integration
│   │   ├── embeddings.py      # Document embedding
│   │   ├── retrieval.py       # Vector search
│   │   └── namespaces.py      # Collection management
│   ├── models/                 # Data models
│   │   ├── chat.py            # SQLAlchemy chat history
│   │   └── schemas.py         # Pydantic schemas
│   └── tools/                  # Agent-specific tools
│       ├── herb_lookup.py
│       ├── compatibility.py
│       └── meridian_analysis.py

📁 wwhd-frontend/ (Web UI - Separate repo)
├── components/                 # React components
├── lib/                       # API clients
└── amplify.yml               # AWS Amplify deployment

📁 wwhd-mobile/ (Mobile App - Separate repo)
├── src/                       # React Native
└── shared/                    # Shared logic with web
```

## Implementation Phases

### Phase 1: Core Backend Infrastructure (Week 1)
- [x] ECS Fargate deployment with FastAPI + Qdrant
- [x] CI/CD pipeline with GitHub Actions
- [ ] SQLAlchemy models for chat history
- [ ] Qdrant namespace setup for each agent
- [ ] Base LangGraph orchestrator agent
- [ ] Environment configuration for API keys

### Phase 2: Agent Implementation (Week 2)
- [ ] Orchestrator agent with routing logic
- [ ] TCM Specialist agent with herb knowledge base
- [ ] Relationship Specialist with communication tools
- [ ] Money/Finance agent with practical wisdom
- [ ] Feng Shui agent with spatial harmony guidance
- [ ] System prompts for each agent personality

### Phase 3: RAG Pipeline (Week 3)
- [ ] Document ingestion pipeline
- [ ] Embedding generation with OpenAI/OpenRouter
- [ ] Vector storage in Qdrant with namespaces
- [ ] Retrieval optimization with metadata filtering
- [ ] Citation formatting for source attribution

### Phase 4: API Development (Week 4)
- [ ] Chat completion endpoint with streaming
- [ ] WebSocket support for real-time responses
- [ ] Token usage tracking and billing
- [ ] Rate limiting and authentication
- [ ] Admin endpoints for document upload

### Phase 5: Frontend Integration (Week 5)
- [ ] Deploy Next.js app to AWS Amplify
- [ ] Integrate assistant-ui components
- [ ] Connect to backend WebSocket API
- [ ] Implement chat history UI
- [ ] Add document upload interface

### Phase 6: Mobile App (Week 6)
- [ ] React Native setup with shared components
- [ ] API client abstraction layer
- [ ] Push notifications for async responses
- [ ] App store deployment preparation

## Agent Architecture

### Orchestrator Agent
```python
class OrchestratorAgent:
    """Routes queries to appropriate specialist agents"""

    def analyze_intent(self, query: str) -> List[str]:
        # Determine which agents to involve
        pass

    def route_query(self, query: str, context: dict) -> str:
        # Execute routing logic
        pass
```

### Specialist Agent Template
```python
class SpecialistAgent:
    system_prompt: str = "You are an expert in..."
    tools: List[Tool] = [...]
    namespace: str = "agent_specific_namespace"

    def process(self, query: str, context: dict) -> str:
        # 1. Retrieve relevant documents from namespace
        # 2. Apply tools if needed
        # 3. Generate response with citations
        pass
```

### Tool Integration
Each agent has access to specific tools:

| Agent | Tools |
|-------|-------|
| **TCM Specialist** | herb_lookup, meridian_analysis, syndrome_differentiation |
| **Relationship** | compatibility_check, communication_advice, conflict_resolution |
| **Money/Finance** | budget_calculator, investment_wisdom, prosperity_mindset |
| **Feng Shui** | bagua_map, element_balance, space_optimization |

## Development Workflow

### Local Development
```bash
# Clone repository
git clone https://github.com/wbaxterh/wwhd.git
cd wwhd

# Set up environment
cp .env.example .env
# Add your API keys to .env (never commit this file)

# Install dependencies
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000
```

### Deployment (Automated)
```bash
# Make changes
git add .
git commit -m "feat: Add new agent capability"
git push origin master

# GitHub Actions automatically:
# 1. Builds Docker image
# 2. Pushes to ECR
# 3. Updates ECS service
# 4. Validates health checks
# ✅ Live in 3 minutes
```

## Performance Targets

- **Response Latency**: < 3 seconds for simple queries
- **RAG Retrieval**: < 500ms for vector search
- **Token Efficiency**: < 2000 tokens per response average
- **Concurrent Users**: 100+ simultaneous connections
- **Uptime**: 99.9% availability

## Security Considerations

- **API Keys**: Stored in AWS Secrets Manager, never in code
- **Authentication**: JWT tokens for user sessions
- **Rate Limiting**: 100 requests/minute per user
- **Data Encryption**: TLS for transit, EFS encryption at rest
- **Input Validation**: Pydantic schemas for all endpoints
- **Prompt Injection**: Safety filters on user inputs

## Cost Estimates (Monthly)

| Service | Cost |
|---------|------|
| ECS Fargate (1 vCPU, 2GB) | ~$40 |
| EFS Storage (10GB) | ~$3 |
| ALB | ~$25 |
| ECR | ~$1 |
| Secrets Manager | ~$1 |
| **Total Infrastructure** | **~$70** |
| OpenAI API (estimated) | ~$50-200 |
| **Total with API costs** | **~$120-270** |

## Success Metrics

- ✅ RAG returns 2+ cited sources by default
- ✅ Response includes source block with title + timestamp
- ✅ Latency p50 < 3s with small models
- ✅ Router accuracy ≥80% to correct specialist
- ✅ Admin can upload docs in < 3 clicks
- ✅ Token usage tracked per message
- ✅ Clean deployment with push to master

## Next Steps

1. **Immediate**: Set up .env file with API keys
2. **Today**: Implement base orchestrator agent
3. **This Week**: Complete Phase 1 infrastructure
4. **Next Week**: Begin specialist agent development
5. **Month 1**: MVP with all core features
6. **Month 2**: Frontend and mobile apps deployed