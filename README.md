# What Would Herman Do? (W.W.H.D.)

A calm, reliable chat app where an orchestrator agent routes user questions to focused specialist agents backed by a Qdrant vector knowledge base, returning grounded, cited answers.

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/wwhd.git
cd wwhd

# Copy environment variables
cp .env.example .env
# Configure your keys in .env

# Start all services
make dev

# Access services
# Web UI: http://localhost:3000
# Backend API: http://localhost:8000
# Qdrant UI: http://localhost:6333/dashboard
```

## Repository Structure

```
wwhd/
├── backend/              # FastAPI + LangGraph orchestration
│   ├── agents/          # LangGraph agent implementations
│   ├── api/            # REST endpoints + WebSocket/SSE
│   ├── models/         # SQLAlchemy models
│   ├── rag/            # Qdrant integration
│   └── auth/           # JWT authentication
├── frontend/            # Next.js + assistant-ui
│   ├── components/     # React components
│   └── lib/           # API clients
├── mobile/              # React Native placeholder
├── admin/               # Admin console (Next.js)
├── migrations/          # SQL migrations
├── scripts/            # Deployment & data scripts
├── tests/              # Test suites
└── docs/               # Additional documentation
```

## Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-...           # When ENABLE_OPENAI=true
OPENROUTER_API_KEY=sk-or-...    # When ENABLE_OPENROUTER=true
MODEL_CHAT=gpt-4o-mini          # Chat completion model
MODEL_EMBED=text-embedding-3-small # Embedding model
ENABLE_OPENAI=true              # Use OpenAI directly
ENABLE_OPENROUTER=false         # Use OpenRouter broker

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-key-here

# Authentication
JWT_SECRET=generate-secure-secret
JWT_ISSUER=wwhd
JWT_AUDIENCE=wwhd-users

# Database
DATABASE_URL=sqlite:///./data/app.db

# CORS & Security
ALLOW_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
APP_ENV=dev
LOG_LEVEL=INFO
```

## 2-Day Deploy Checklist

### Day 1: Core Infrastructure
- [ ] Set up AWS account & configure IAM
- [ ] Deploy Qdrant Cloud instance (or ECS self-hosted)
- [ ] Configure GitHub repository & Actions
- [ ] Set up App Runner / ECS Fargate for backend
- [ ] Deploy CloudFront + S3 for frontend
- [ ] Configure Route53 domain & SSL

### Day 2: Application & Testing
- [ ] Deploy backend with environment configs
- [ ] Deploy frontend with API endpoints
- [ ] Seed initial RAG namespaces
- [ ] Upload sample documents
- [ ] Test chat flow end-to-end
- [ ] Configure monitoring & alerts

## Live Demo Plan

1. **Public Demo**: https://wwhd-demo.example.com
   - Limited to 100 queries/day
   - Pre-loaded with curated content
   - OpenAI gpt-4o-mini for cost control

2. **Admin Demo**: https://wwhd-demo.example.com/admin
   - Guest credentials: demo@wwhd.ai / ReadOnly123
   - Document upload disabled
   - Read-only namespace browsing

## Core Features

- **Multi-Agent Orchestration**: LangGraph router directs queries to specialized agents
- **RAG with Citations**: Every answer includes sources with timestamps
- **Namespace Isolation**: Content organized by domain (relationships, money, feng_shui, etc.)
- **Token Accounting**: Track usage per user for billing
- **Admin Console**: Upload and manage knowledge base documents
- **Safety Guardrails**: No medical diagnosis, respectful tone enforcement

## Development Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Admin Console
cd admin
npm install
npm run dev

# Database
alembic upgrade head        # Apply migrations
python scripts/seed_data.py  # Load sample data

# Testing
pytest backend/tests/ -v
npm run test --prefix frontend

# Docker
docker-compose up -d        # Full stack
docker-compose logs -f backend

# Infrastructure Deployment
./infrastructure/scripts/setup-ecs.sh  # Deploy to AWS ECS
```

## Infrastructure Documentation

- **[Platform Architecture](PLATFORM-INFRA.md)** - Complete infrastructure overview
- **[Infrastructure Changes](InfraChanges/)** - Change log for all infrastructure modifications
  - [infra-change-001.md](InfraChanges/infra-change-001.md) - ECS Fargate + Qdrant deployment setup

## Acceptance Criteria

- ✅ RAG returns at least 2 cited chunks by default
- ✅ Answers include "Sources" block with title + URL + timestamp
- ✅ Latency p50 < 5s with small models
- ✅ Router accuracy ≥80% to correct namespace
- ✅ Admin can upload docs and reindex in < 3 clicks
- ✅ Token usage recorded per message and user
- ✅ Clean startup with `make dev`

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Orchestration | LangGraph (Python) | Stateful multi-agent workflows |
| LLM | OpenAI / OpenRouter | Flexible model selection |
| Vector DB | Qdrant | Production-ready, namespace support |
| Backend | FastAPI | Async, streaming, WebSocket support |
| Database | SQLite → PostgreSQL | Simple start, clear migration path |
| Auth | JWT | Stateless, role-based |
| Frontend | Next.js + assistant-ui | Production chat UI patterns |
| Mobile | React Native | Code sharing with web |
| Deploy | AWS (App Runner/ECS) | Managed containers, quick setup |

## Getting Help

- [Architecture Overview](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Contributing Guide](./CONTRIBUTING.md)

## License

MIT - See LICENSE file

## Support

- Issues: https://github.com/your-org/wwhd/issues
- Discord: https://discord.gg/wwhd
- Email: support@wwhd.ai