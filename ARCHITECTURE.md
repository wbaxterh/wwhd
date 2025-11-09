# Architecture

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Next.js Web App]
        Mobile[React Native App]
        Admin[Admin Console]
    end

    subgraph "API Gateway"
        FastAPI[FastAPI Server]
        Auth[JWT Auth Middleware]
    end

    subgraph "Orchestration Layer"
        LG[LangGraph Orchestrator]
        Router[RouterAgent]
        Librarian[LibrarianAgent]
        Interpreter[InterpreterAgent]
        Safety[SafetyAgent]
    end

    subgraph "Data Layer"
        Qdrant[(Qdrant Vector DB)]
        SQLite[(SQLite DB)]
        EFS[EFS Storage]
    end

    subgraph "LLM Services"
        OpenAI[OpenAI API]
        OpenRouter[OpenRouter API]
    end

    Web --> FastAPI
    Mobile --> FastAPI
    Admin --> FastAPI
    FastAPI --> Auth
    Auth --> LG
    LG --> Router
    Router --> Librarian
    Librarian --> Qdrant
    Librarian --> Interpreter
    Interpreter --> Safety
    Router --> OpenAI
    Router --> OpenRouter
    Librarian --> OpenAI
    Librarian --> OpenRouter
    FastAPI --> SQLite
    Admin --> EFS
```

## Component Architecture

### Backend Services

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Server | FastAPI 0.100+ | REST endpoints, WebSocket/SSE streaming |
| Agent Orchestrator | LangGraph 0.1+ | Multi-agent state machine |
| Vector Store | Qdrant 1.7+ | RAG retrieval with namespaces |
| Database | SQLite 3.35+ | Chat history, users, token accounting |
| Cache | Redis (optional) | Session cache, rate limiting |
| Queue | Celery (optional) | Document processing jobs |

### Multi-Repository Structure

| Repository | Technology | Deployment | Purpose |
|------------|------------|------------|---------||
| **wwhd** (Backend) | FastAPI + LangGraph | ECS Fargate | API server, agent orchestration |
| **wwhd-frontend** | Next.js 14 + assistant-ui | AWS Amplify | Web chat interface |
| **wwhd-mobile** (Future) | React Native 0.72+ | Expo + App Store | Mobile chat client |

## Sequence Diagrams

### Chat Flow

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web UI
    participant API as FastAPI
    participant LG as LangGraph
    participant R as RouterAgent
    participant L as LibrarianAgent
    participant I as InterpreterAgent
    participant S as SafetyAgent
    participant Q as Qdrant
    participant DB as SQLite

    U->>W: Type message
    W->>API: POST /chat (SSE)
    API->>DB: Create session/message
    API->>LG: Process message

    LG->>R: Classify intent
    R->>R: Determine namespace(s)

    alt RAG Required
        R->>L: Retrieve context
        L->>Q: Vector search
        Q-->>L: Top-k chunks
        L->>L: Rerank (optional)
    end

    R->>I: Generate response
    I->>S: Safety check
    S-->>I: Approved/Modified

    loop Streaming
        I-->>API: Token chunk
        API-->>W: SSE event
        W-->>U: Display token
    end

    API->>DB: Save complete response
    API->>DB: Update token usage
    API-->>W: Citations + sources
    W-->>U: Display sources
```

### Document Ingestion Flow

```mermaid
sequenceDiagram
    participant A as Admin
    participant UI as Admin UI
    participant API as FastAPI
    participant S3 as S3 Storage
    participant P as Processor
    participant E as Embedder
    participant Q as Qdrant
    participant DB as SQLite

    A->>UI: Upload document
    UI->>API: POST /admin/docs/upload
    API->>S3: Store raw file
    API->>DB: Create document record
    API-->>UI: doc_id

    UI->>API: POST /admin/docs/{id}/index
    API->>P: Parse document
    P->>P: Extract text/metadata
    P->>P: Chunk (1-2k chars)

    loop Each chunk
        P->>E: Generate embedding
        E->>OpenAI: Embed text
        OpenAI-->>E: Vector
        E->>Q: Upsert with metadata
    end

    API->>DB: Update doc status
    API-->>UI: Index complete
```

## Data Flow

```mermaid
graph LR
    subgraph "Ingestion Pipeline"
        Raw[Raw Docs] --> Parse[Parser]
        Parse --> Chunk[Chunker]
        Chunk --> Embed[Embedder]
        Embed --> Vector[(Qdrant)]
    end

    subgraph "Query Pipeline"
        Query[User Query] --> Encode[Encode Query]
        Encode --> Search[Vector Search]
        Vector --> Search
        Search --> Rerank[Reranker]
        Rerank --> Context[Context]
    end

    subgraph "Response Pipeline"
        Context --> Generate[LLM Generate]
        Generate --> Safety[Safety Check]
        Safety --> Stream[Stream Response]
    end
```

## LangGraph State Schema

```python
from typing import TypedDict, List, Optional, Literal
from datetime import datetime

class ConversationState(TypedDict):
    # Message context
    user_id: str
    session_id: str
    message_id: str
    user_message: str
    timestamp: datetime

    # Routing
    intent: Optional[str]
    confidence: float
    selected_namespaces: List[str]
    selected_agents: List[str]

    # RAG context
    retrieved_chunks: List[dict]  # {text, metadata, score}
    reranked_chunks: Optional[List[dict]]

    # Generation
    system_prompt: str
    safety_flags: List[str]
    response_tokens: List[str]
    final_response: str
    citations: List[dict]  # {source_title, url, timestamp}

    # Accounting
    prompt_tokens: int
    completion_tokens: int
    embedding_tokens: int
    total_cost: float

    # Control flow
    current_node: str
    next_node: Optional[str]
    error: Optional[str]
    status: Literal["processing", "streaming", "complete", "error"]
```

## Network Architecture

### Multi-Repository Architecture

```mermaid
graph TB
    subgraph "Frontend Repository: wwhd-frontend"
        NextJS[Next.js Chat UI]
        Amplify[AWS Amplify Deployment]
    end

    subgraph "Backend Repository: wwhd (this repo)"
        FastAPI[FastAPI + LangGraph]
        ECS[ECS Fargate Deployment]
    end

    subgraph "Mobile Repository: wwhd-mobile (future)"
        RN[React Native App]
        Expo[Expo Deployment]
    end

    NextJS --> Amplify
    FastAPI --> ECS
    RN --> Expo

    NextJS -.->|API Calls| FastAPI
    RN -.->|API Calls| FastAPI
```

### ECS Fargate Deployment (Current Implementation)

```mermaid
graph TB
    subgraph "Internet"
        Users[Users]
    end

    subgraph "AWS Cloud"
        subgraph "Frontend (Separate Repo)"
            Amplify[AWS Amplify<br/>Next.js Frontend]
        end

        subgraph "Backend (This Repo)"
            ALB[Application Load Balancer]
            subgraph "ECS Fargate"
                FastAPI[FastAPI Container]
                Qdrant[Qdrant Container]
            end
            EFS[EFS Persistent Storage]
        end
    end

    Users --> Amplify
    Users --> ALB
    ALB --> FastAPI
    FastAPI --> Qdrant
    FastAPI --> EFS
    Qdrant --> EFS
    Amplify -.->|API Calls| ALB
```

## Scaling Considerations

### Horizontal Scaling Points

1. **API Server**: Multiple FastAPI instances behind ALB
2. **LangGraph Workers**: Separate worker pool for agent execution
3. **Qdrant**: Cluster mode with replicas
4. **Database**: Read replicas for query load

### Vertical Scaling Points

1. **Model Selection**: gpt-4o-mini → gpt-4o → claude-3
2. **Embedding Dimensions**: 1536 → 3072 dimensions
3. **Chunk Size**: 1000 → 2000 → 4000 tokens
4. **Cache Layer**: Add Redis for session state

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Chat Latency (p50) | < 5s | - |
| Chat Latency (p95) | < 10s | - |
| Document Index Time | < 30s/MB | - |
| Concurrent Users | 100 | - |
| Requests/second | 50 | - |
| Uptime | 99.9% | - |

## Security Architecture

### Defense in Depth

```mermaid
graph TB
    subgraph "Layer 1: Network"
        WAF[AWS WAF]
        DDoS[AWS Shield]
    end

    subgraph "Layer 2: Application"
        CORS[CORS Policy]
        Rate[Rate Limiting]
        Auth[JWT Authentication]
    end

    subgraph "Layer 3: Data"
        RBAC[Role-Based Access]
        Encrypt[Encryption at Rest]
        Audit[Audit Logging]
    end

    subgraph "Layer 4: Runtime"
        Safety[Safety Agent]
        Validate[Input Validation]
        Escape[Output Escaping]
    end
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant API as Protected API

    U->>F: Login credentials
    F->>A: POST /auth/login
    A->>A: Validate credentials
    A-->>F: JWT tokens
    F->>F: Store tokens

    F->>API: Request + Bearer token
    API->>API: Validate JWT
    API-->>F: Protected resource

    Note over F,API: Token expires
    F->>A: POST /auth/refresh
    A-->>F: New tokens
```

## Monitoring Architecture

### Observability Stack

| Component | Purpose | Tool Options |
|-----------|---------|--------------|
| Metrics | Performance tracking | CloudWatch, Datadog |
| Logs | Centralized logging | CloudWatch Logs, ELK |
| Traces | Distributed tracing | X-Ray, Jaeger |
| APM | Application monitoring | New Relic, AppDynamics |
| Synthetic | Uptime monitoring | Pingdom, StatusCake |

### Key Metrics

```yaml
Infrastructure:
  - CPU utilization
  - Memory usage
  - Network I/O
  - Disk I/O

Application:
  - Request rate
  - Error rate
  - Response time (p50, p95, p99)
  - Active sessions

Business:
  - Daily active users
  - Messages per user
  - Token usage per user
  - Namespace hit rates
  - Citation click-through rate

AI/ML:
  - Router accuracy
  - Retrieval precision@k
  - Response quality scores
  - Safety intervention rate
```

## Disaster Recovery

### Backup Strategy

| Component | Frequency | Retention | Recovery Time |
|-----------|-----------|-----------|---------------|
| Database | Daily | 30 days | < 1 hour |
| Qdrant | Daily | 7 days | < 2 hours |
| Documents | Real-time | Indefinite | Immediate |
| Config | On change | Indefinite | < 30 min |

### Failure Scenarios

1. **LLM Service Outage**: Fallback to alternate provider (OpenAI ↔ OpenRouter)
2. **Qdrant Failure**: Serve from cache, degraded experience warning
3. **Database Corruption**: Restore from backup, replay from event log
4. **Region Failure**: Multi-region standby (future)

## Cost Optimization

### Resource Allocation

```yaml
Development:
  Backend: 1 vCPU, 2 GB RAM
  Qdrant: 1 vCPU, 2 GB RAM
  Database: db.t3.micro

Staging:
  Backend: 2 vCPU, 4 GB RAM
  Qdrant: 2 vCPU, 4 GB RAM
  Database: db.t3.small

Production:
  Backend: 4 vCPU, 8 GB RAM (auto-scale 2-10)
  Qdrant: 4 vCPU, 16 GB RAM (cluster)
  Database: db.m5.large (with read replica)
```

### Cost Controls

1. **Token Limits**: Max tokens per request, daily user limits
2. **Caching**: Aggressive caching of embeddings and common queries
3. **Model Selection**: Use smaller models for classification/routing
4. **Batch Processing**: Group embedding requests
5. **Spot Instances**: Use for non-critical workloads

## Acceptance Criteria

- ✅ System handles 50 concurrent users
- ✅ Auto-scales based on load
- ✅ Failover completes in < 60 seconds
- ✅ All components containerized
- ✅ Infrastructure as Code (ECS setup scripts)
- ✅ Zero-downtime deployments
- ✅ Monitoring alerts configured