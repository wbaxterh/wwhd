# Platform Infrastructure

## Overview
This document outlines the actual deployment infrastructure for W.W.H.D. based on practical AWS services and modern deployment patterns.

## Architecture Decision Record

### Frontend: AWS Amplify
- **Service**: AWS Amplify
- **Why**:
  - Native Next.js 14 support with SSR/ISR
  - Automatic builds from GitHub
  - Environment variables management
  - Preview deployments per branch
  - Built-in SSL and custom domains
  - No infrastructure to manage

### Backend: ECS Fargate
- **Service**: Amazon ECS on Fargate
- **Why**:
  - Full WebSocket/SSE support for streaming
  - Auto-scaling for variable loads
  - Persistent connections for LangGraph agents
  - EFS mount for SQLite persistence
  - Better networking control
  - Proven reliability

### Vector Database: Self-hosted Qdrant
- **Service**: Qdrant container on ECS Fargate
- **Why**:
  - Purpose-built for vector similarity search
  - Excellent metadata filtering capabilities
  - Simple HTTP API integration
  - Cost-effective self-hosting (~$15/month vs $100/month managed)
  - No external dependencies

### Storage
- **Documents**: S3
- **Application Data**: SQLite on EFS (shared volume)
- **Vector Data**: Qdrant on EFS (shared volume)
- **Secrets**: AWS Secrets Manager

## Deployment Architecture

```
┌──────────────────────────────────────────────────────┐
│                    GitHub Repository                  │
└──────────────┬───────────────────┬───────────────────┘
               │                   │
               ▼                   ▼
       ┌──────────────┐    ┌──────────────┐
       │   Amplify    │    │     ECR      │
       │  (Frontend)  │    │   (Images)   │
       └──────┬───────┘    └──────┬───────┘
              │                    │
              ▼                    ▼
       ┌──────────────┐    ┌──────────────┐
       │ Next.js App  │───▶│  ECS Fargate │
       │   (SSR)      │    │   (FastAPI)  │
       └──────────────┘    └──────┬───────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ▼                  ▼                  ▼
         ┌────────────┐    ┌────────────┐    ┌────────────┐
         │  Vector DB │    │     S3     │    │  RDS/EFS   │
         │   (TBD)    │    │   (Docs)   │    │   (Data)   │
         └────────────┘    └────────────┘    └────────────┘
```

## Service Configuration

### Amplify (Frontend)
```yaml
framework: Next.js 14
build:
  commands:
    - npm ci
    - npm run build
environment:
  - NEXT_PUBLIC_API_URL: https://api.wwhd.ai
  - NEXT_PUBLIC_WS_URL: wss://api.wwhd.ai
```

### ECS Fargate (Backend + Qdrant)
```yaml
task_definition:
  family: wwhd-backend
  cpu: 1024  # 1 vCPU total
  memory: 2048  # 2 GB total

  containers:
    - name: fastapi
      image: ECR_REPO/wwhd-backend:latest
      cpu: 768
      memory: 1536
      portMappings:
        - containerPort: 8000
      environment:
        - APP_ENV: production
        - QDRANT_URL: http://localhost:6333
        - SQLITE_PATH: /data/wwhd.db
      secrets:
        - OPENAI_API_KEY: from Secrets Manager
        - JWT_SECRET: from Secrets Manager
      mountPoints:
        - sourceVolume: data
          containerPath: /data

    - name: qdrant
      image: qdrant/qdrant:latest
      cpu: 256
      memory: 512
      portMappings:
        - containerPort: 6333
      mountPoints:
        - sourceVolume: data
          containerPath: /qdrant/storage

  volumes:
    - name: data
      efsVolumeConfiguration:
        fileSystemId: EFS_FILE_SYSTEM_ID
```

### Load Balancer
```yaml
alb:
  listeners:
    - port: 443
      protocol: HTTPS
      certificate: ACM

  target_groups:
    - port: 8000
      protocol: HTTP
      health_check: /health
      stickiness: enabled  # For WebSocket
```

## Vector Database Options Analysis

### Option 1: Managed Qdrant Cloud
**Pros:**
- Zero maintenance
- Automatic scaling
- Built-in backups
- Optimized performance

**Cons:**
- External dependency
- Additional cost ($25-100/month)
- Data leaves AWS

### Option 2: PostgreSQL + pgvector
**Pros:**
- Native AWS (RDS)
- Single database for everything
- Cost-effective
- Good for <1M vectors

**Cons:**
- Not as performant as dedicated vector DB
- Limited vector operations

### Option 3: OpenSearch on AWS
**Pros:**
- AWS-native service
- Scales well
- Full-text search + vectors

**Cons:**
- More expensive than RDS
- Overkill for our needs

### Option 4: Self-hosted Qdrant on ECS
**Pros:**
- Full control
- Data stays in AWS
- One-time setup

**Cons:**
- We manage updates
- Need persistent storage
- Another container to manage

### Recommendation: PostgreSQL + pgvector
For our use case with TCM/Shaolin documents:
- Start with RDS PostgreSQL + pgvector
- ~10-50k vectors initially
- Migrate to dedicated solution if needed
- Keeps everything in AWS
- Single database for all data

## Deployment Commands

### Frontend (Amplify)
```bash
# One-time setup (AWS Console is easier)
amplify init
amplify add hosting
amplify push

# GitHub will auto-deploy after setup
```

### Backend (ECS)
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name wwhd-cluster

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-def.json

# Create service
aws ecs create-service \
  --cluster wwhd-cluster \
  --service-name wwhd-backend \
  --task-definition wwhd-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

## Cost Estimates (Monthly)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| Amplify | ~1000 builds, 100GB transfer | $25 |
| ECS Fargate | 1x (1vCPU, 2GB), always on | $40 |
| ALB | 1 load balancer | $25 |
| EFS | 10GB storage, minimal throughput | $3 |
| S3 | 10GB storage, minimal transfer | $5 |
| Secrets Manager | 5 secrets | $2 |
| **Total** | | **~$100/month** |

Compare to:
- App Runner: $50/month (broken)
- RDS + Qdrant Cloud: $130+/month
- Managed services: $200+/month

## Migration Path

1. **Phase 1: Minimal Deployment** (You are here)
   - Health check API on ECS ✅
   - Basic frontend on Amplify

2. **Phase 2: Core Features**
   - Add PostgreSQL + pgvector
   - Implement LangGraph agents
   - Deploy real API endpoints

3. **Phase 3: Production Ready**
   - Add monitoring (CloudWatch)
   - Set up CI/CD (GitHub Actions)
   - Configure auto-scaling

## Why Not Use LangChain's Vector Store?

LangChain provides **interfaces** to vector stores, not the actual database:
- `langchain.vectorstores.Qdrant` - requires Qdrant running
- `langchain.vectorstores.Chroma` - requires Chroma running
- `langchain.vectorstores.PGVector` - requires PostgreSQL

LangChain is the client library; we still need the actual database.

## Decision: SQLite + Self-hosted Qdrant

For W.W.H.D., we're using:
```python
# SQLite for relational data
import sqlite3
db = sqlite3.connect('/data/wwhd.db')

# Qdrant for vectors via LangChain
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")
vector_store = Qdrant(
    client=client,
    collection_name="tcm_documents",
    embeddings=OpenAIEmbeddings()
)
```

This gives us:
- **SQLite**: Zero-config, fast, lightweight for chat/user data
- **Qdrant**: Purpose-built vector search with excellent metadata
- **Cost**: ~$40/month vs $130+ for managed services
- **Simplicity**: No external dependencies, runs in single ECS task
- **Performance**: Optimized for each data type
- **Portability**: Easy backup/restore (just copy EFS volume)