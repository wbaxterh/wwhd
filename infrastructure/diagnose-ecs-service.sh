#!/bin/bash
# Diagnose ECS service stuck in unstable state

set -e

CLUSTER_NAME="wwhd-cluster"
SERVICE_NAME="wwhd-backend"  # or "wwhd-service" - check which one exists
REGION="us-west-2"

echo "🔍 Diagnosing ECS service: $SERVICE_NAME in cluster: $CLUSTER_NAME"
echo "=================================================="

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "📋 ECS Service Status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{
        ServiceName: serviceName,
        Status: status,
        RunningCount: runningCount,
        PendingCount: pendingCount,
        DesiredCount: desiredCount,
        TaskDefinition: taskDefinition,
        LastUpdate: updatedAt
    }' \
    --output table || echo "❌ Service not found or error accessing service"

echo ""
echo "📋 Recent Service Events (last 10):"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].events[:10].{
        Time: createdAt,
        Message: message
    }' \
    --output table || echo "❌ Could not fetch service events"

echo ""
echo "📋 Running Tasks:"
TASK_ARNS=$(aws ecs list-tasks \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --region $REGION \
    --query 'taskArns[]' \
    --output text)

if [ ! -z "$TASK_ARNS" ]; then
    aws ecs describe-tasks \
        --cluster $CLUSTER_NAME \
        --tasks $TASK_ARNS \
        --region $REGION \
        --query 'tasks[].{
            TaskArn: taskArn,
            LastStatus: lastStatus,
            DesiredStatus: desiredStatus,
            HealthStatus: healthStatus,
            CreatedAt: createdAt,
            StoppedReason: stoppedReason
        }' \
        --output table
else
    echo "❌ No running tasks found"
fi

echo ""
echo "🏥 Task Health Check Status:"
if [ ! -z "$TASK_ARNS" ]; then
    for task_arn in $TASK_ARNS; do
        echo "Task: $task_arn"
        aws ecs describe-tasks \
            --cluster $CLUSTER_NAME \
            --tasks $task_arn \
            --region $REGION \
            --query 'tasks[0].containers[0].{
                Name: name,
                LastStatus: lastStatus,
                HealthStatus: healthStatus,
                ExitCode: exitCode,
                Reason: reason
            }' \
            --output table
        echo ""
    done
fi

echo ""
echo "💡 Recommendations:"
echo "1. If tasks are stuck in PENDING: Check capacity/resources"
echo "2. If tasks keep failing: Check CloudWatch logs for errors"
echo "3. If service is DRAINING: Stop and restart the service"
echo "4. If completely stuck: Consider deleting and recreating the service"
echo ""
echo "🔧 Quick Fixes:"
echo "Force new deployment: aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $REGION"
echo "Scale to 0 then back: aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --desired-count 0 --region $REGION"
echo "Delete service: aws ecs delete-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force --region $REGION"