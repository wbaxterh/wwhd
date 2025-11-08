# Infra Change 001: ECS Fargate + Qdrant Deployment Setup

**Date**: 2025-11-07
**Author**: Claude Code
**Status**: In Progress
**Environment**: Production (us-west-2)

## Overview

Initial deployment setup for W.W.H.D. backend infrastructure using ECS Fargate with self-hosted Qdrant vector database and SQLite for relational data.

## Architecture Decision

**Previous State**: App Runner deployment attempts (failed due to authentication issues)
**New State**: ECS Fargate with dual-container task (FastAPI + Qdrant)

**Rationale**:
- App Runner had persistent IAM/ECR authentication issues
- ECS Fargate provides better control over multi-container deployments
- SQLite + Qdrant combination reduces complexity and cost vs RDS + Qdrant Cloud

## Infrastructure Components Created

### 1. ECS Cluster
```bash
Cluster Name: wwhd-cluster
Capacity Provider: FARGATE
Region: us-west-2
ARN: arn:aws:ecs:us-west-2:018025611404:cluster/wwhd-cluster
```

### 2. Elastic File System (EFS)
```bash
File System ID: fs-00b8168893587fd61
Performance Mode: generalPurpose
Access Point ID: fsap-09b001e50000005e4
Purpose: Persistent storage for SQLite database and Qdrant vector data
Path Structure:
  /wwhd-data/wwhd.db     # SQLite database
  /wwhd-data/qdrant/     # Qdrant storage
```

### 3. Network Security
```bash
VPC ID: vpc-7b44bd03
Subnets: subnet-677d281e, subnet-5498bc0e, subnet-18ddaa53

ECS Security Group: sg-0a75b2c312d17f654
- Inbound: Port 8000 (HTTP from anywhere)
- Inbound: Port 6333 (Qdrant inter-container)
- Outbound: All traffic

EFS Security Group: sg-08c58d51b55de0ed5
- Inbound: Port 2049 (NFS from ECS security group)
```

### 4. IAM Roles
```bash
Execution Role: wwhd-dev-ecs-execution-role
- AmazonECSTaskExecutionRolePolicy
- AmazonElasticFileSystemClientFullAccess

Task Role: wwhd-dev-ecs-task-role
- Custom policy for Secrets Manager access
- Access to wwhd-dev/* secrets
```

### 5. ECS Task Definition
```bash
Family: wwhd-backend
Revision: 1
CPU: 1024 (1 vCPU total)
Memory: 2048 MB (2 GB total)

Containers:
  fastapi:
    Image: 018025611404.dkr.ecr.us-west-2.amazonaws.com/wwhd-dev-backend:latest
    CPU: 768, Memory: 1536
    Port: 8000
    Environment:
      - APP_ENV=production
      - QDRANT_URL=http://localhost:6333
      - SQLITE_PATH=/data/wwhd.db
      - LOG_LEVEL=INFO
    Secrets:
      - OPENAI_API_KEY (from Secrets Manager)
      - JWT_SECRET (from Secrets Manager)
    Health Check: curl http://localhost:8000/health

  qdrant:
    Image: qdrant/qdrant:v1.7.4
    CPU: 256, Memory: 512
    Port: 6333
    Environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=INFO
    Health Check: curl http://localhost:6333/health

Shared Volume:
  - EFS mount at /data (fastapi) and /qdrant/storage (qdrant)
```

## Commands Executed

```bash
# 1. Create ECS cluster
aws ecs create-cluster --cluster-name wwhd-cluster --capacity-providers FARGATE

# 2. Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/wwhd-backend"

# 3. Create EFS file system
aws efs create-file-system --creation-token wwhd-data-$(date +%s) --performance-mode generalPurpose

# 4. Create security groups
aws ec2 create-security-group --group-name wwhd-ecs-sg --description "WWHD ECS tasks"
aws ec2 create-security-group --group-name wwhd-efs-sg --description "WWHD EFS"

# 5. Configure security group rules
aws ec2 authorize-security-group-ingress --group-id sg-0a75b2c312d17f654 --protocol tcp --port 8000 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-0a75b2c312d17f654 --protocol tcp --port 6333 --source-group sg-0a75b2c312d17f654
aws ec2 authorize-security-group-ingress --group-id sg-08c58d51b55de0ed5 --protocol tcp --port 2049 --source-group sg-0a75b2c312d17f654

# 6. Create EFS mount targets (in 3 subnets)
aws efs create-mount-target --file-system-id fs-00b8168893587fd61 --subnet-id subnet-677d281e --security-groups sg-08c58d51b55de0ed5
aws efs create-mount-target --file-system-id fs-00b8168893587fd61 --subnet-id subnet-5498bc0e --security-groups sg-08c58d51b55de0ed5
aws efs create-mount-target --file-system-id fs-00b8168893587fd61 --subnet-id subnet-18ddaa53 --security-groups sg-08c58d51b55de0ed5

# 7. Create EFS access point
aws efs create-access-point --file-system-id fs-00b8168893587fd61 --posix-user Uid=1000,Gid=1000 --root-directory Path=/wwhd-data,CreationInfo='{OwnerUid=1000,OwnerGid=1000,Permissions=755}'

# 8. Attach policies to IAM roles
aws iam attach-role-policy --role-name wwhd-dev-ecs-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam attach-role-policy --role-name wwhd-dev-ecs-execution-role --policy-arn arn:aws:iam::aws:policy/AmazonElasticFileSystemClientFullAccess

# 9. Register task definition
aws ecs register-task-definition --cli-input-json file://infrastructure/ecs/task-definition.json
```

## Files Created/Modified

```
├── .github/workflows/deploy-backend.yml    # GitHub Actions workflow
├── infrastructure/
│   ├── ecs/
│   │   └── task-definition.json            # ECS task definition
│   └── scripts/
│       └── setup-ecs.sh                   # Complete setup script
├── PLATFORM-INFRA.md                      # Updated architecture docs
└── InfraChanges/
    └── infra-change-001.md                # This document
```

## Status

### ✅ Completed
- ECS cluster creation
- EFS file system with access points
- Security groups and networking
- IAM roles and policies
- Task definition registration
- CloudWatch log group

### 🚧 In Progress
- Application Load Balancer creation
- ECS service deployment
- Testing and validation

### ⏭️ Next Steps
1. Create Application Load Balancer with target group
2. Create ECS service to deploy task definition
3. Test health endpoints and verify Qdrant connectivity
4. Set up GitHub Actions secrets for CI/CD

## Cost Impact

**New Monthly Costs:**
- ECS Fargate: ~$40/month (1 vCPU, 2GB, always-on)
- EFS: ~$3/month (10GB storage, minimal throughput)
- ALB: ~$25/month (when created)
- **Total**: ~$68/month

**Cost Savings:**
- Eliminated App Runner attempts: $0 (was failing)
- Avoided RDS PostgreSQL: -$30/month
- Avoided Qdrant Cloud: -$100/month

## Rollback Plan

If deployment fails:
1. Delete ECS service: `aws ecs delete-service`
2. Delete task definition: Manual cleanup via console
3. Delete EFS file system: `aws efs delete-file-system`
4. Delete security groups: `aws ec2 delete-security-group`
5. Revert to local development setup

## Testing Checklist

- [ ] ECS service starts successfully
- [ ] Health check endpoints respond (FastAPI and Qdrant)
- [ ] EFS volume mounts correctly
- [ ] SQLite database creation works
- [ ] Qdrant API accessible at localhost:6333
- [ ] Secrets Manager integration works
- [ ] CloudWatch logging active
- [ ] Load balancer routes traffic correctly

## Post-Deployment Tasks

1. Update DNS/domain configuration
2. Set up SSL/TLS certificates
3. Configure GitHub Actions secrets
4. Create monitoring dashboards
5. Set up backup procedures for EFS
6. Document API endpoints and usage