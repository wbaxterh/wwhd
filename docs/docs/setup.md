---
sidebar_position: 5
---

# Setup & Deployment

This guide covers local development setup, environment configuration, and production deployment for the W.W.H.D. system.

## Prerequisites

- **Node.js** 18+ for frontend development
- **Python** 3.11+ for backend development
- **Docker** for containerization
- **AWS CLI** configured for deployment
- **Git** for version control

## Environment Configuration

### GitHub Secrets Setup

The API requires an OpenAI API key configured as a GitHub Secret:

1. Go to your repository: https://github.com/wbaxterh/wwhd
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following repository secrets:

```
OPENAI_API_KEY=sk-your-actual-openai-key-here
JWT_SECRET=your-super-secure-jwt-secret-32-chars-minimum
```

4. Optionally add repository variables for model configuration:
```
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-small
```

### Local Development Environment

Create a `.env` file in the `backend/` directory:

```bash
# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key-here
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-small
ENABLE_OPENAI=true
ENABLE_OPENROUTER=false

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Authentication
JWT_SECRET=your-local-development-secret-key
JWT_ISSUER=wwhd
JWT_AUDIENCE=wwhd-users

# Database
DATABASE_URL=sqlite:///./data/app.db

# CORS & Security
ALLOW_ORIGINS=http://localhost:3000,http://localhost:3001

# Environment
APP_ENV=development
LOG_LEVEL=INFO
DEBUG_MODE=true
```

## Backend Development

### Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Database Setup

```bash
# Create database and run migrations
alembic upgrade head

# Optional: Seed with sample data
python scripts/seed_data.py
```

### Start Qdrant

Using Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### Run Development Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at:
- **Backend**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Interactive Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Register and Test Chat
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "TestPass123!", "name": "Test User"}'

# Get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=TestPass123!" | jq -r .access_token)

# Send message
curl -X POST http://localhost:8000/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "Hello Herman, tell me about balance in life", "chat_id": null}'
```

## Production Deployment

### Current Architecture

The system is deployed on AWS using:
- **ECS Fargate** for container orchestration
- **Application Load Balancer** for traffic distribution
- **EFS** for persistent storage (SQLite + Qdrant data)
- **ECR** for container registry
- **GitHub Actions** for CI/CD

### Deployment Process

Deployment is fully automated via GitHub Actions:

1. **Push to master** triggers the deployment
2. **Docker image** is built and pushed to ECR
3. **Environment variables** are injected from GitHub Secrets
4. **ECS task** is updated with the new image
5. **Health checks** verify successful deployment

### Manual Deployment Trigger

You can manually trigger a deployment:

1. Go to **Actions** tab in GitHub
2. Select **Deploy Backend to ECS**
3. Click **Run workflow**
4. Select **master** branch and run

### Infrastructure Status

Current production environment:
- **URL**: http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com
- **Health**: http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/health
- **Region**: us-west-2
- **Environment**: production

### Monitoring

Check deployment status:
```bash
# Check ECS service status
aws ecs describe-services --cluster wwhd-cluster --services wwhd-backend --region us-west-2

# View logs
aws logs tail /ecs/wwhd-backend --region us-west-2 --follow

# Check task health
aws ecs list-tasks --cluster wwhd-cluster --service-name wwhd-backend --region us-west-2
```

## Documentation Deployment

### Local Docusaurus Development

```bash
cd docs
npm install
npm start
```

The documentation will be available at http://localhost:3000

### Build Documentation

```bash
cd docs
npm run build
npm run serve  # Test the build locally
```

### Deploy to GitHub Pages

```bash
cd docs
npm run deploy
```

This will build and deploy the documentation to GitHub Pages at:
https://wbaxterh.github.io/wwhd/

## Troubleshooting

### Backend Issues

**OpenAI API Errors:**
- Verify `OPENAI_API_KEY` is correctly set in GitHub Secrets
- Check token usage limits on OpenAI dashboard
- Review logs for specific error messages

**Database Issues:**
- Ensure EFS is mounted correctly in ECS
- Check database permissions and file paths
- Run migrations if schema changes were made

**Qdrant Connection:**
- Verify Qdrant container is running and healthy
- Check network connectivity between containers
- Confirm Qdrant URL configuration

### Deployment Issues

**ECS Task Failures:**
- Check CloudWatch logs: `/ecs/wwhd-backend`
- Verify environment variables are set correctly
- Confirm container health check endpoints

**Docker Build Failures:**
- Review GitHub Actions build logs
- Check Dockerfile syntax and dependencies
- Verify base image availability

### Common Error Messages

**"Not authenticated"**
- JWT token is missing or invalid
- Token may have expired (24-hour lifetime)
- Check Authorization header format

**"I encountered an error"**
- OpenAI API key not configured or invalid
- API rate limits exceeded
- Internal server error - check logs

**"Field required"**
- Missing required fields in request body
- Check JSON syntax and field names
- Refer to API documentation for correct format

## Cost Management

### Infrastructure Costs
- **ECS Fargate**: ~$40/month (1 vCPU, 2GB RAM)
- **EFS Storage**: ~$3/month (10GB)
- **Application Load Balancer**: ~$25/month
- **Total Infrastructure**: ~$70/month

### API Costs
- **OpenAI API**: Variable based on usage
  - gpt-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens
  - text-embedding-3-small: $0.02/1M tokens
- **Estimated**: $50-200/month depending on usage

### Optimization Tips
1. **Use efficient models** (gpt-4o-mini vs gpt-4)
2. **Implement caching** for repeated queries
3. **Monitor token usage** and set limits
4. **Use streaming** for better user experience
5. **Implement rate limiting** to control costs

## Security Considerations

### API Security
- JWT tokens with 24-hour expiration
- bcrypt password hashing
- Input validation with Pydantic
- CORS configuration for allowed origins

### Infrastructure Security
- AWS IAM roles with minimal permissions
- ECS tasks in private subnets
- Load balancer with security groups
- Environment variables in GitHub Secrets

### Best Practices
- Never commit API keys or secrets to git
- Use HTTPS in production (configure ALB with SSL)
- Regular security updates and dependency scanning
- Monitor for unusual API usage patterns
- Implement logging and alerting for security events