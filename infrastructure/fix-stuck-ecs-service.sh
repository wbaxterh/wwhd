#!/bin/bash
# Fix ECS service stuck in unstable state

set -e

CLUSTER_NAME="wwhd-cluster"
SERVICE_NAME="wwhd-backend"
REGION="us-west-2"

echo "🚑 Fixing stuck ECS service: $SERVICE_NAME"
echo "============================================"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

echo "🔍 Checking current service status..."
SERVICE_STATUS=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].status' \
    --output text 2>/dev/null || echo "NOT_FOUND")

echo "Current service status: $SERVICE_STATUS"

if [ "$SERVICE_STATUS" = "NOT_FOUND" ]; then
    echo "❌ Service not found. Please check cluster and service names."
    exit 1
fi

echo ""
echo "📊 Current service state:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{
        Status: status,
        RunningCount: runningCount,
        PendingCount: pendingCount,
        DesiredCount: desiredCount
    }' \
    --output table

echo ""
echo "🔧 Applying fixes..."

# Step 1: Force new deployment to unstick tasks
echo "1️⃣  Forcing new deployment..."
aws ecs update-service \
    --cluster $CLUSTER_NAME \
    --service $SERVICE_NAME \
    --force-new-deployment \
    --region $REGION > /dev/null

echo "✅ Force deployment initiated"

# Step 2: Wait a bit then check
echo "⏳ Waiting 30 seconds for deployment to start..."
sleep 30

# Step 3: Check if still stuck, try scaling to 0 then back
CURRENT_COUNT=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].runningCount' \
    --output text)

DESIRED_COUNT=$(aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].desiredCount' \
    --output text)

echo "Current running: $CURRENT_COUNT, Desired: $DESIRED_COUNT"

if [ "$CURRENT_COUNT" = "0" ] && [ "$DESIRED_COUNT" != "0" ]; then
    echo "2️⃣  Service stuck with 0 running tasks. Cycling desired count..."

    # Scale to 0
    echo "   Scaling to 0..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --desired-count 0 \
        --region $REGION > /dev/null

    # Wait
    echo "   Waiting 15 seconds..."
    sleep 15

    # Scale back up
    echo "   Scaling back to $DESIRED_COUNT..."
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --desired-count $DESIRED_COUNT \
        --region $REGION > /dev/null

    echo "✅ Service cycling complete"
fi

echo ""
echo "⏳ Waiting for service to stabilize (this may take 2-5 minutes)..."

# Wait for service stability with timeout
aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --cli-read-timeout 300 \
    --cli-connect-timeout 60 || {
    echo "⚠️  Service didn't stabilize within timeout, but continuing..."
}

echo ""
echo "📊 Final service state:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $REGION \
    --query 'services[0].{
        Status: status,
        RunningCount: runningCount,
        DesiredCount: desiredCount,
        TaskDefinition: taskDefinition
    }' \
    --output table

echo ""
echo "🌐 Testing service endpoint..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
    http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/ || echo "❌ Service not responding"

echo ""
echo "✅ Service recovery attempted!"
echo ""
echo "💡 If service is still stuck, consider:"
echo "   1. Check CloudWatch logs for container errors"
echo "   2. Verify task definition is valid"
echo "   3. Check ALB health checks"
echo "   4. As last resort, delete and recreate the service"