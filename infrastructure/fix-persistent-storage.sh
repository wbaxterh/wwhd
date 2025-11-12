#!/bin/bash
# Fix for persistent database storage in production
# This script sets up EFS for persistent SQLite storage

set -e

echo "🔧 Fixing persistent storage for WWHD production deployment..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-west-2"

echo "🏗️ Setting up EFS for persistent storage..."

# Create EFS file system
EFS_ID=$(aws efs create-file-system \
    --performance-mode generalPurpose \
    --throughput-mode provisioned \
    --provisioned-throughput-in-mibps 10 \
    --tags Key=Name,Value=wwhd-data \
    --query FileSystemId \
    --output text \
    --region $REGION)

echo "📁 Created EFS: $EFS_ID"

# Wait for EFS to be available
echo "⏳ Waiting for EFS to be available..."
aws efs wait file-system-available --file-system-id $EFS_ID --region $REGION

# Get default VPC and subnets (assuming existing ECS setup)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $REGION)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].SubnetId" --output text --region $REGION)

echo "🌐 Using VPC: $VPC_ID"

# Create security group for EFS
SG_ID=$(aws ec2 create-security-group \
    --group-name wwhd-efs-sg \
    --description "Security group for WWHD EFS access" \
    --vpc-id $VPC_ID \
    --query GroupId \
    --output text \
    --region $REGION)

echo "🔒 Created security group: $SG_ID"

# Add NFS access rule
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 2049 \
    --cidr 10.0.0.0/8 \
    --region $REGION

echo "🔗 Added NFS access rule"

# Create mount targets for each subnet
for SUBNET_ID in $SUBNET_IDS; do
    echo "📌 Creating mount target in subnet: $SUBNET_ID"
    aws efs create-mount-target \
        --file-system-id $EFS_ID \
        --subnet-id $SUBNET_ID \
        --security-groups $SG_ID \
        --region $REGION || true  # Continue if already exists
done

# Create access point for the application
ACCESS_POINT_ID=$(aws efs create-access-point \
    --file-system-id $EFS_ID \
    --posix-user Uid=1000,Gid=1000 \
    --root-directory Path=/wwhd-data,CreationInfo='{OwnerUid=1000,OwnerGid=1000,Permissions=755}' \
    --tags Key=Name,Value=wwhd-access-point \
    --query AccessPointId \
    --output text \
    --region $REGION)

echo "🎯 Created access point: $ACCESS_POINT_ID"

echo "✅ EFS setup complete!"
echo ""
echo "🔧 Next steps to fix the production deployment:"
echo ""
echo "1. Update your ECS task definition with these values:"
echo "   - EFS File System ID: $EFS_ID"
echo "   - Access Point ID: $ACCESS_POINT_ID"
echo "   - Security Group ID: $SG_ID"
echo ""
echo "2. Mount EFS at /data in the container"
echo "3. Set SQLITE_PATH=/data/wwhd.db"
echo ""
echo "📋 Updated task definition template:"
echo "   Replace fs-XXXXXXXXX with: $EFS_ID"
echo "   Replace fsap-XXXXXXXXX with: $ACCESS_POINT_ID"
echo "   Replace ACCOUNT_ID with: $ACCOUNT_ID"
echo ""
echo "🚀 Deploy the updated task definition to fix data persistence!"