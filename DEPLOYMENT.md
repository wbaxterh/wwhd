# Deployment

## AWS Architecture - 48 Hour MVP

### Option A: App Runner (Recommended for MVP)

```mermaid
graph TB
    subgraph "AWS Cloud"
        R53[Route53]
        CF[CloudFront]
        S3[S3 Static Site]
        AR[App Runner]
        QC[Qdrant Cloud]
        SM[Secrets Manager]
    end

    R53 --> CF
    CF --> S3
    CF --> AR
    AR --> QC
    AR --> SM
```

**Deployment Steps**:

```bash
# Day 1: Infrastructure
1. Set up AWS account
2. Configure Route53 domain
3. Create S3 bucket for frontend
4. Set up CloudFront distribution
5. Launch Qdrant Cloud instance
6. Configure Secrets Manager

# Day 2: Application
1. Build Docker container
2. Deploy to App Runner
3. Deploy frontend to S3
4. Configure environment variables
5. Run smoke tests
6. Enable monitoring
```

### Option B: ECS Fargate (Production-Ready)

```yaml
infrastructure:
  compute:
    type: ECS Fargate
    cpu: 2 vCPU
    memory: 4 GB
    auto_scaling:
      min: 2
      max: 10
      target_cpu: 70%

  load_balancer:
    type: Application Load Balancer
    listeners:
      - port: 443
        protocol: HTTPS
        certificate: ACM

  database:
    development: SQLite on EFS
    production: RDS PostgreSQL

  vector_db:
    option_1: Qdrant Cloud
    option_2: Self-hosted Qdrant on ECS
```

## Infrastructure as Code

### Terraform Configuration

```hcl
# main.tf
provider "aws" {
  region = "us-west-2"
}

# App Runner Service
resource "aws_apprunner_service" "api" {
  service_name = "wwhd-api"

  source_configuration {
    image_repository {
      image_identifier      = "${aws_ecr_repository.api.repository_url}:latest"
      image_repository_type = "ECR"
    }
  }

  instance_configuration {
    cpu               = "1 vCPU"
    memory            = "2 GB"
    instance_role_arn = aws_iam_role.apprunner.arn
  }

  auto_scaling_configuration {
    max_concurrency = 100
    max_size        = 10
    min_size        = 1
  }
}

# S3 for Frontend
resource "aws_s3_bucket" "frontend" {
  bucket = "wwhd-frontend"

  website {
    index_document = "index.html"
    error_document = "404.html"
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3-frontend"
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-frontend"
  }
}
```

## Docker Configuration

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - QDRANT_URL=http://qdrant:6333
    volumes:
      - ./data:/app/data
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  qdrant_storage:
```

## GitHub Actions CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Build and push Docker image
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -t $ECR_REPOSITORY:latest ./backend
          docker push $ECR_REPOSITORY:latest

      - name: Deploy to App Runner
        run: |
          aws apprunner start-deployment --service-arn $APP_RUNNER_ARN

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Deploy to S3
        run: |
          aws s3 sync ./frontend/out s3://$S3_BUCKET --delete
          aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION --paths "/*"
```

## Environment Configuration

### Production Environment Variables

```bash
# API Server
APP_ENV=production
LOG_LEVEL=INFO

# LLM Configuration
OPENAI_API_KEY=${SECRETS_MANAGER:openai_key}
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-small

# Vector Database
QDRANT_URL=https://qdrant.wwhd.ai
QDRANT_API_KEY=${SECRETS_MANAGER:qdrant_key}

# Database
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com/wwhd

# Authentication
JWT_SECRET=${SECRETS_MANAGER:jwt_secret}
JWT_ISSUER=wwhd
JWT_AUDIENCE=wwhd-users

# CORS
ALLOW_ORIGINS=https://wwhd.ai,https://app.wwhd.ai
```

## Monitoring Setup

### CloudWatch Configuration

```yaml
metrics:
  - name: RequestLatency
    namespace: WWHD/API
    dimensions:
      - Environment
      - Endpoint

  - name: TokenUsage
    namespace: WWHD/Usage
    dimensions:
      - User
      - Model

alarms:
  - name: HighLatency
    metric: RequestLatency
    threshold: 5000  # 5 seconds
    comparison: GreaterThanThreshold

  - name: HighErrorRate
    metric: 4xxErrors
    threshold: 10
    comparison: GreaterThanThreshold
```

## Cost Optimization

### Resource Allocation by Environment

| Component | Dev | Staging | Production |
|-----------|-----|---------|------------|
| App Runner | 0.5 vCPU, 1GB | 1 vCPU, 2GB | 2 vCPU, 4GB |
| Qdrant | Shared | Dedicated Small | Dedicated Medium |
| Database | SQLite | RDS t3.small | RDS m5.large |
| CloudFront | Disabled | Enabled | Enabled + WAF |

### Estimated Monthly Costs

```yaml
development:
  total: $50
  breakdown:
    app_runner: $20
    qdrant_cloud: $20
    s3: $5
    other: $5

production:
  total: $500
  breakdown:
    app_runner: $150  # With auto-scaling
    qdrant_cloud: $200
    rds: $100
    cloudfront: $30
    monitoring: $20
```

## Deployment Checklist

### Day 1: Infrastructure

- [ ] AWS account setup
- [ ] IAM roles and policies
- [ ] VPC and networking (if ECS)
- [ ] Secrets Manager configuration
- [ ] S3 buckets creation
- [ ] CloudFront distribution
- [ ] Route53 DNS setup
- [ ] ACM SSL certificates

### Day 2: Application

- [ ] ECR repository setup
- [ ] Docker image build
- [ ] App Runner deployment
- [ ] Environment variables
- [ ] Database migrations
- [ ] Qdrant collections setup
- [ ] Frontend deployment
- [ ] Health check validation
- [ ] Smoke tests
- [ ] Monitoring alerts

## Rollback Strategy

```bash
# App Runner rollback
aws apprunner list-operations --service-arn $SERVICE_ARN
aws apprunner start-deployment --service-arn $SERVICE_ARN --image-identifier $PREVIOUS_IMAGE

# Frontend rollback
aws s3 sync s3://$S3_BUCKET-backup s3://$S3_BUCKET
aws cloudfront create-invalidation --distribution-id $CF_DISTRIBUTION --paths "/*"
```

## Acceptance Criteria

- ✅ Zero-downtime deployments
- ✅ Automated CI/CD pipeline
- ✅ Infrastructure as Code
- ✅ Secrets properly managed
- ✅ Monitoring and alerts configured
- ✅ Backup and rollback procedures
- ✅ Cost tracking enabled
- ✅ Auto-scaling configured