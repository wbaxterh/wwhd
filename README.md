# What Would Herman Do? (W.W.H.D.)

A calm, reliable chat app where an orchestrator agent routes user questions to focused specialist agents backed by a Qdrant vector knowledge base, returning grounded, cited answers.

## Quick Start

### Backend Development (This Repo)
```bash
# Clone backend repository
git clone https://github.com/wbaxterh/wwhd.git
cd wwhd

# Set up backend environment
cd backend
cp .env.example .env
# Edit .env and add your OpenAI API key

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000
```

### Frontend (Separate Repository)
```bash
# Frontend will be deployed via AWS Amplify
# Repository: wwhd-frontend (to be created)
# Live at: https://wwhd.amplifyapp.com
```

### Live Deployment
- **Backend API**: http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com
- **API Docs**: http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/docs
- **Frontend**: Will be deployed to AWS Amplify (separate repo)

## Multi-Repository Structure

### 📁 wwhd/ (Backend - This Repository)
```
wwhd/
├── backend/              # FastAPI + LangGraph orchestration
│   ├── agents/          # LangGraph agent implementations
│   │   ├── orchestrator.py  # Main routing agent
│   │   ├── tcm_specialist.py # Traditional Chinese Medicine
│   │   ├── relationship.py   # Relationship counseling
│   │   ├── money.py         # Financial wisdom
│   │   └── feng_shui.py     # Feng Shui guidance
│   ├── api/            # REST endpoints + WebSocket/SSE
│   ├── models/         # SQLAlchemy models
│   ├── rag/            # Qdrant integration
│   ├── schemas/        # Pydantic schemas
│   └── config.py       # Environment configuration
├── infrastructure/      # AWS ECS deployment
├── .github/workflows/   # CI/CD for backend
└── docs/               # Documentation
```

### 📁 wwhd-frontend/ (Web UI - Separate Repository)
```
wwhd-frontend/
├── components/          # React components
├── lib/                # API clients
├── pages/              # Next.js pages
├── styles/             # CSS/Tailwind
└── amplify.yml         # AWS Amplify deployment
```

### 📁 wwhd-mobile/ (Mobile App - Future Repository)
```
wwhd-mobile/
├── src/                # React Native
├── shared/             # Shared logic with web
└── app.json           # Expo configuration
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

## Deployment Architecture

### ✅ Backend (ECS Fargate) - DEPLOYED
- **Infrastructure**: AWS ECS Fargate with Application Load Balancer
- **Database**: SQLite on EFS for chat history + Qdrant for vectors
- **CI/CD**: GitHub Actions → ECR → ECS (3-minute deployments)
- **API**: http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com
- **Status**: ✅ Live and ready for development

### 🚧 Frontend (AWS Amplify) - PLANNED
- **Repository**: wwhd-frontend (to be created)
- **Technology**: Next.js + assistant-ui
- **Deployment**: AWS Amplify with automatic Git deployments
- **Domain**: https://wwhd.amplifyapp.com
- **Status**: 🚧 Ready to be created

### 📱 Mobile App (React Native) - FUTURE
- **Repository**: wwhd-mobile (future)
- **Technology**: React Native with shared API client
- **Deployment**: Expo + App Store/Play Store
- **Status**: 📱 Planned for Phase 2

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

| Component | Technology | Status | Rationale |
|-----------|------------|--------|-----------|
| **Backend Orchestration** | LangGraph (Python) | ✅ Deployed | Stateful multi-agent workflows |
| **LLM Provider** | OpenAI / OpenRouter | ✅ Configured | Flexible model selection |
| **Vector Database** | Qdrant (Self-hosted) | ✅ Running | Namespace support, cost-effective |
| **Chat Database** | SQLite on EFS | ✅ Running | Fast queries, ACID compliance |
| **Backend API** | FastAPI | ✅ Deployed | Async, streaming, WebSocket support |
| **Authentication** | JWT | ✅ Implemented | Stateless, role-based |
| **Backend Deploy** | ECS Fargate + ALB | ✅ Live | Managed containers, auto-scaling |
| **CI/CD** | GitHub Actions | ✅ Working | 3-minute push-to-deploy |
| **Frontend** | Next.js + assistant-ui | 🚧 Planned | Production chat UI patterns |
| **Frontend Deploy** | AWS Amplify | 🚧 Ready | Git-based deployments |
| **Mobile** | React Native | 📱 Future | Code sharing with web |

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