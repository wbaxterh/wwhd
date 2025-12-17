# Qdrant File Lock Resolution

## Problem
When using Qdrant with EFS persistent storage on AWS ECS, lock files can persist after task restarts, preventing new instances from starting. This results in tasks being deprovisioned with the error: "Preventing Qdrant file lock conflicts".

## Solution
Run a lock-clearing task before deploying new versions of the backend service.

## Prerequisites
- AWS CLI configured with appropriate permissions
- Access to the ECS cluster and EFS file system
- The following AWS resources should exist:
  - ECS cluster: `wwhd-cluster`
  - EFS file system: `fs-00b8168893587fd61`
  - Security group: `sg-0a75b2c312d17f654`
  - IAM roles: `wwhd-dev-ecs-execution-role`, `wwhd-dev-ecs-task-role`

## Step-by-Step Process

### 1. Create Lock Clearing Task Definition

Create a temporary task definition that mounts the same EFS volume and clears lock files:

```bash
cat > clear-locks-task.json << 'EOF'
{
  "family": "clear-qdrant-locks",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::018025611404:role/wwhd-dev-ecs-execution-role",
  "taskRoleArn": "arn:aws:iam::018025611404:role/wwhd-dev-ecs-task-role",
  "containerDefinitions": [
    {
      "name": "cleaner",
      "image": "alpine:latest",
      "cpu": 256,
      "memory": 512,
      "essential": true,
      "command": [
        "sh", "-c",
        "echo 'Clearing Qdrant lock files...'; find /data -name '*.lock' -type f -delete; find /data -name 'data.mdb.lock' -type f -delete; echo 'Lock files cleared'; sleep 10"
      ],
      "mountPoints": [
        {
          "sourceVolume": "data",
          "containerPath": "/data"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/wwhd-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "cleaner"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-00b8168893587fd61",
        "rootDirectory": "/",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
EOF
```

### 2. Register and Run the Cleaning Task

```bash
# Register the task definition
aws ecs register-task-definition --cli-input-json file://clear-locks-task.json --region us-west-2

# Run the cleaning task
aws ecs run-task \
  --cluster wwhd-cluster \
  --task-definition clear-qdrant-locks:1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-677d281e,subnet-5498bc0e,subnet-18ddaa53],securityGroups=[sg-0a75b2c312d17f654],assignPublicIp=ENABLED}" \
  --region us-west-2
```

### 3. Wait for Completion

Wait 30-60 seconds for the cleaning task to complete. The task will automatically exit after clearing the lock files.

### 4. Start the Main Service

```bash
# Force a new deployment of the backend service
aws ecs update-service \
  --cluster wwhd-cluster \
  --service wwhd-backend \
  --force-new-deployment \
  --desired-count 1 \
  --region us-west-2
```

## When to Use

Run this process when:
- ECS tasks are failing to start with "Preventing Qdrant file lock conflicts"
- After stopping all backend services and before restarting
- Before deploying new versions when you see repeated task failures

## Important Notes

⚠️ **Data Safety**: This process only removes lock files, not your actual data. Your Qdrant collections and documents remain intact.

✅ **Safe Operation**: The cleaning only removes `.lock` and `data.mdb.lock` files, which are regenerated automatically by Qdrant.

🔄 **Automation**: Consider integrating this into your CI/CD pipeline as a pre-deployment step if lock conflicts occur frequently.

## Verification

After running the process:

1. Check that the ECS service has `runningCount: 1`
2. Test the health endpoint: `curl http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/health`
3. Verify your data is intact by making a test query

## Alternative Solutions

For future deployments, consider:
- Using a more robust file locking mechanism
- Implementing graceful shutdown procedures
- Using separate EFS mount points per environment
- Migrating to a managed vector database service