#!/bin/bash
set -e

# Configuration
CLUSTER_NAME="wwhd-cluster"
SERVICE_NAME="wwhd-backend"
REGION="us-west-2"
ACCOUNT_ID="018025611404"

echo "🚀 Setting up ECS infrastructure for WWHD..."

# Create ECS cluster
echo "📦 Creating ECS cluster: $CLUSTER_NAME"
aws ecs create-cluster \
    --cluster-name $CLUSTER_NAME \
    --capacity-providers FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region $REGION

# Create CloudWatch log group
echo "📝 Creating CloudWatch log group"
aws logs create-log-group \
    --log-group-name "/ecs/wwhd-backend" \
    --region $REGION 2>/dev/null || echo "Log group already exists"

# Create EFS file system for persistent storage
echo "💾 Creating EFS file system"
EFS_ID=$(aws efs create-file-system \
    --creation-token wwhd-data-$(date +%s) \
    --performance-mode generalPurpose \
    --enable-backup \
    --tags Key=Name,Value=wwhd-data \
    --region $REGION \
    --query 'FileSystemId' --output text)

echo "EFS File System ID: $EFS_ID"

# Get default VPC and subnets
echo "🌐 Getting VPC information"
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' --output text \
    --region $REGION)

SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query 'Subnets[*].SubnetId' --output text \
    --region $REGION)

echo "VPC ID: $VPC_ID"
echo "Subnet IDs: $SUBNET_IDS"

# Create security group for EFS
echo "🔒 Creating EFS security group"
EFS_SG_ID=$(aws ec2 create-security-group \
    --group-name wwhd-efs-sg \
    --description "Security group for WWHD EFS" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

# Create security group for ECS tasks
echo "🔒 Creating ECS security group"
ECS_SG_ID=$(aws ec2 create-security-group \
    --group-name wwhd-ecs-sg \
    --description "Security group for WWHD ECS tasks" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

# Configure security group rules
echo "⚙️ Configuring security group rules"

# ECS security group - allow HTTP and HTTPS outbound, ALB inbound
aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG_ID \
    --protocol tcp \
    --port 8000 \
    --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG_ID \
    --protocol tcp \
    --port 6333 \
    --source-group $ECS_SG_ID \
    --region $REGION

# EFS security group - allow NFS from ECS
aws ec2 authorize-security-group-ingress \
    --group-id $EFS_SG_ID \
    --protocol tcp \
    --port 2049 \
    --source-group $ECS_SG_ID \
    --region $REGION

# Create EFS mount targets
echo "🗂️ Creating EFS mount targets"
for subnet in $SUBNET_IDS; do
    aws efs create-mount-target \
        --file-system-id $EFS_ID \
        --subnet-id $subnet \
        --security-groups $EFS_SG_ID \
        --region $REGION 2>/dev/null || echo "Mount target for $subnet already exists"
done

# Create EFS access point
echo "🎯 Creating EFS access point"
ACCESS_POINT_ID=$(aws efs create-access-point \
    --file-system-id $EFS_ID \
    --posix-user Uid=1000,Gid=1000 \
    --root-directory Path=/wwhd-data,CreationInfo='{OwnerUid=1000,OwnerGid=1000,Permissions=755}' \
    --tags Key=Name,Value=wwhd-access-point \
    --region $REGION \
    --query 'AccessPointId' --output text)

echo "EFS Access Point ID: $ACCESS_POINT_ID"

# Create IAM execution role for ECS
echo "👤 Creating ECS execution role"
aws iam create-role \
    --role-name wwhd-dev-ecs-execution-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' 2>/dev/null || echo "Execution role already exists"

aws iam attach-role-policy \
    --role-name wwhd-dev-ecs-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

aws iam attach-role-policy \
    --role-name wwhd-dev-ecs-execution-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonElasticFileSystemClientFullAccess

# Create IAM task role for ECS
echo "👤 Creating ECS task role"
aws iam create-role \
    --role-name wwhd-dev-ecs-task-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ecs-tasks.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }' 2>/dev/null || echo "Task role already exists"

# Add policy for accessing secrets
aws iam put-role-policy \
    --role-name wwhd-dev-ecs-task-role \
    --policy-name SecretsManagerAccess \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue"
                ],
                "Resource": "arn:aws:secretsmanager:'$REGION':'$ACCOUNT_ID':secret:wwhd-dev/*"
            }
        ]
    }'

# Update task definition template with real values
echo "📄 Updating task definition template"
sed -i.bak \
    -e "s/fs-PLACEHOLDER/$EFS_ID/g" \
    -e "s/fsap-PLACEHOLDER/$ACCESS_POINT_ID/g" \
    infrastructure/ecs/task-definition.json

# Register task definition
echo "📋 Registering task definition"
aws ecs register-task-definition \
    --cli-input-json file://infrastructure/ecs/task-definition.json \
    --region $REGION

# Create Application Load Balancer
echo "⚖️ Creating Application Load Balancer"
ALB_ARN=$(aws elbv2 create-load-balancer \
    --name wwhd-alb \
    --subnets $SUBNET_IDS \
    --security-groups $ECS_SG_ID \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
    --name wwhd-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 5 \
    --region $REGION \
    --query 'TargetGroups[0].TargetGroupArn' --output text)

# Create ALB listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $REGION

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns $ALB_ARN \
    --region $REGION \
    --query 'LoadBalancers[0].DNSName' --output text)

# Create ECS service
echo "🏃 Creating ECS service"
aws ecs create-service \
    --cluster $CLUSTER_NAME \
    --service-name $SERVICE_NAME \
    --task-definition wwhd-backend:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" \
    --load-balancers targetGroupArn=$TG_ARN,containerName=fastapi,containerPort=8000 \
    --region $REGION

echo "✅ ECS setup complete!"
echo ""
echo "📊 Summary:"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo "  EFS ID: $EFS_ID"
echo "  ALB URL: http://$ALB_DNS"
echo "  ECS Security Group: $ECS_SG_ID"
echo "  EFS Security Group: $EFS_SG_ID"
echo ""
echo "🔗 Your API will be available at: http://$ALB_DNS/health"
echo ""
echo "⏳ Wait 2-3 minutes for the service to start, then test:"
echo "  curl http://$ALB_DNS/health"