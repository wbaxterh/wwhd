# Backend Deployment Guide

## Overview
The backend is automatically deployed to AWS ECS using GitHub Actions whenever changes are pushed to the master branch or manually triggered via workflow dispatch.

## Architecture
- **Platform:** AWS ECS Fargate
- **Container Registry:** Amazon ECR
- **Load Balancer:** Application Load Balancer
- **Database:** SQLite on EFS + Qdrant Vector DB
- **API Framework:** FastAPI
- **Runtime:** Python 3.13 with Uvicorn

## GitHub Actions Workflow

### Trigger Conditions
- Push to `master` branch with changes in `backend/**` directory
- Manual workflow dispatch with environment selection

### Deployment Process

#### 1. Build & Test Phase
```yaml
# Tests Docker container locally before pushing
- Builds Docker image
- Starts container with test configuration
- Verifies health endpoint responds
- Ensures container doesn't crash on startup
```

#### 2. ECR Push Phase
```yaml
# Builds and pushes to Amazon ECR
- Builds multi-platform image (linux/amd64)
- Tags with commit SHA and 'latest'
- Pushes to ECR repository: wwhd-dev-backend
```

#### 3. Zero-Downtime Deployment Strategy
The workflow implements a special deployment strategy to handle Qdrant database locks:

1. **Stops existing tasks** to release database locks
2. **Waits for complete shutdown**
3. **Deploys new version**
4. **Ensures single task running** to prevent lock conflicts

```bash
# This prevents "database is locked" errors during deployment
aws ecs update-service --desired-count 0  # Stop old version
aws ecs wait services-stable              # Wait for shutdown
aws ecs deploy-task-definition            # Deploy new version
aws ecs update-service --desired-count 1  # Start single task
```

#### 4. Health Verification
```yaml
# Comprehensive health checks post-deployment
- Basic health endpoint check (/health)
- RAG system connectivity test
- Qdrant database verification
- Load balancer routing confirmation
```

#### 5. User Creation
Automatically creates production users:
- `testuser` / `testpass123` (created on startup)
- `bulk_import` / `bulk123` (for API data import)

### Rollback Strategy
If deployment fails, automatic rollback occurs:
1. Identifies previous stable task definition
2. Stops failed deployment
3. Deploys previous version
4. Verifies health of rolled-back service

## Database Persistence Strategy

### Current Implementation
The backend uses two database systems with EFS persistence:

1. **SQLite Database** (`/data/app.db`)
   - Document metadata
   - User accounts
   - Authentication data
   - Mounted on EFS for persistence

2. **Qdrant Vector Database** (`/database/`)
   - Document embeddings
   - Semantic search index
   - Runs as sidecar container
   - Data persisted on separate EFS volume

### Data Management

#### Fresh Deployment Approach
The current strategy deploys with empty databases and uses API-based bulk import:

```bash
# After deployment, import data using:
python api_bulk_import.py \
  --pdf-folder /path/to/pdfs \
  --metadata-file /path/to/metadata.json \
  --api-url https://api.weshuber.com \
  --namespace general
```

#### Why This Approach?
- ✅ Clean, predictable deployments
- ✅ No automatic seeding that might fail
- ✅ Full control over data population
- ✅ Works for both local and production
- ✅ Uses existing API endpoints for consistency

### ⚠️ Important Database Considerations

#### Qdrant Lock Issues
Qdrant uses file-based locking that can cause deployment failures if not handled properly:
- Only one Qdrant instance can access the database at a time
- The deployment workflow stops existing tasks before deploying new ones
- This prevents "database is locked" errors

#### EFS Volumes
Two separate EFS file systems are used:
- **wwhd-database** (fs-0421d6926b3c7056d): Qdrant vector data
- **wwhd-data** (fs-00b8168893587fd61): SQLite and application data

## Environment Variables

### Required Secrets (GitHub Secrets)
- `AWS_ROLE_ARN`: IAM role for AWS operations
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `JWT_SECRET`: Secret for JWT token signing

### Configuration Variables (GitHub Variables)
- `MODEL_CHAT`: Chat model (default: gpt-4o-mini)
- `MODEL_EMBED`: Embedding model (default: text-embedding-3-small)
- `CORS_ORIGINS`: Allowed CORS origins (default: ["https://wwhd.weshuber.com", "https://api.weshuber.com"])

### Runtime Environment
```bash
OPENAI_API_KEY=<from-secret>
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-small
ENABLE_OPENAI=true
QDRANT_URL=http://localhost:6333
DATABASE_URL=sqlite:////data/app.db
SQLITE_PATH=/data/wwhd_v3.db
APP_ENV=production
LOG_LEVEL=INFO
JWT_SECRET=<from-secret>
CORS_ORIGINS=["https://wwhd.weshuber.com", "https://api.weshuber.com"]
```

## Task Definition

The ECS task runs two containers:

### 1. FastAPI Container
- **Image:** Built and pushed to ECR
- **Port:** 8000
- **Memory:** 2048 MB
- **CPU:** 1024 units
- **Health Check:** `/health` endpoint

### 2. Qdrant Container
- **Image:** qdrant/qdrant:latest
- **Port:** 6333 (internal only)
- **Memory:** 2048 MB
- **CPU:** 1024 units
- **Data Volume:** /database mounted to EFS

## API Endpoints

### Public Endpoints
- `https://api.weshuber.com/health` - Health check
- `https://api.weshuber.com/docs` - API documentation
- `https://api.weshuber.com/api/v1/auth/register` - User registration
- `https://api.weshuber.com/api/v1/auth/token` - Authentication

### Protected Endpoints
All other endpoints require JWT authentication token.

## Monitoring

### Health Checks
- **Target Group:** Checks `/health` every 30 seconds
- **ECS Service:** Monitors task health and replaces unhealthy tasks
- **GitHub Actions:** Verifies deployment health post-deployment

### Logs
- **CloudWatch Log Group:** `/ecs/wwhd-backend`
- **Log Streams:**
  - `fastapi/*` - Application logs
  - `qdrant/*` - Vector database logs

## Troubleshooting

### Common Issues

#### 1. Database Lock Errors
**Problem:** "database is locked" errors during deployment
**Solution:** Deployment workflow handles this by stopping tasks before deploying

#### 2. Health Check Failures
**Problem:** Service fails health checks after deployment
**Solution:** Check CloudWatch logs for startup errors

#### 3. Memory Issues
**Problem:** Container runs out of memory
**Solution:** Increase task definition memory allocation

#### 4. CORS Errors
**Problem:** Frontend can't connect to API
**Solution:** Update CORS_ORIGINS in GitHub Variables

## Manual Operations

### Force Restart Service
```bash
aws ecs update-service \
  --cluster wwhd-cluster \
  --service wwhd-backend \
  --force-new-deployment
```

### Scale Service
```bash
# Scale to 0 (stop)
aws ecs update-service \
  --cluster wwhd-cluster \
  --service wwhd-backend \
  --desired-count 0

# Scale to 1 (start)
aws ecs update-service \
  --cluster wwhd-cluster \
  --service wwhd-backend \
  --desired-count 1
```

### Clear Databases
```bash
# Create and run cleanup task
aws ecs run-task \
  --cluster wwhd-cluster \
  --task-definition wwhd-cleanup:1 \
  --launch-type FARGATE \
  --network-configuration '...'
```

## Future Improvements

### 🔄 Database Persistence (To Revisit)
Current approach uses fresh deployment with API-based import. Consider:
- Implementing database migrations
- Backup and restore strategies
- Blue-green deployment with database sync
- Persistent Qdrant collections across deployments

### 📊 Monitoring Enhancements
- Add CloudWatch alarms for service health
- Implement distributed tracing
- Add performance metrics dashboard

### 🔐 Security Improvements
- Rotate JWT secrets automatically
- Implement API rate limiting
- Add WAF rules for additional protection

---

**Last Updated:** 2025-11-30
**Deployment URL:** https://api.weshuber.com
**Health Check:** https://api.weshuber.com/health