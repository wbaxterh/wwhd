---
sidebar_position: 6
---

# Troubleshooting

This page documents common issues encountered during development and deployment of the W.W.H.D. system, along with their solutions.

## Common Issues

### Authentication & API Issues

#### 401 Unauthorized - "Not authenticated"
**Problem**: Chat API returns 401 even with valid token
```json
{"detail": "Not authenticated"}
```

**Possible Causes**:
- Token has expired (24-hour lifetime)
- JWT_SECRET was changed in deployment
- Token format is incorrect

**Solution**:
```bash
# Get a fresh token
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_user&password=your_password"

# Use the token immediately
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"content": "test message", "chat_id": null}'
```

#### 422 Validation Error - "Field required"
**Problem**: Missing required fields in request
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "content"],
      "msg": "Field required"
    }
  ]
}
```

**Solution**: Ensure all required fields are provided:
```json
{
  "content": "Your message here",  // Required
  "chat_id": null                 // Required (null for new chat)
}
```

#### 422 Validation Error - Registration
**Problem**: Password validation or email format issues
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters"
    }
  ]
}
```

**Solution**: Follow password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### OpenAI Integration Issues

#### Error: "I encountered an error processing your request"
**Problem**: Generic error response with zero tokens
```json
{
  "content": "I apologize, but I encountered an error processing your request. Please try again.",
  "prompt_tokens": 0,
  "completion_tokens": 0
}
```

**Common Causes**:

1. **Invalid OpenAI API Key**
   ```bash
   # Check logs for this error:
   aws logs tail /ecs/wwhd-backend --region us-west-2 | grep "Incorrect API key"
   ```
   **Solution**: Update GitHub Secret `OPENAI_API_KEY` and redeploy

2. **OpenAI Rate Limits**
   ```bash
   # Check for rate limit errors in logs:
   aws logs tail /ecs/wwhd-backend --region us-west-2 | grep "rate_limit"
   ```
   **Solution**: Wait or upgrade OpenAI plan

3. **Model Not Available**
   ```bash
   # Check if model exists:
   curl -H "Authorization: Bearer sk-your-key" https://api.openai.com/v1/models
   ```

### Deployment Issues

#### ECS Environment Variable Conflicts
**Problem**:
```
Error: The secret name must be unique and not shared with any new or existing environment variables set on the container
```

**Root Cause**: AWS ECS doesn't allow same name in both `environment` and `secrets` arrays

**Solution**: Our workflow clears existing environment variables and secrets before setting new ones:
```bash
.containerDefinitions[0].environment = [new_vars] |
.containerDefinitions[0].secrets = []
```

#### Database Data Loss on Deployment
**Problem**: User accounts and chat history disappear after container restarts

**Root Cause**: Database path was misconfigured
- ❌ Wrong: `sqlite:///./data/app.db` (ephemeral container storage)
- ✅ Fixed: `sqlite:////data/app.db` (persistent EFS storage)

**Prevention**: Always use absolute paths for persistent storage:
```yaml
volumes:
  - name: data
    efsVolumeConfiguration:
      fileSystemId: fs-xxxxx

mountPoints:
  - sourceVolume: data
    containerPath: /data

environment:
  - name: DATABASE_URL
    value: sqlite:////data/app.db  # Absolute path to EFS mount
```

#### GitHub Actions Deployment Failures
**Problem**: Deployment workflow fails with AWS permissions errors

**Common Issues**:
1. **AWS Role ARN**: Ensure `AWS_ROLE_ARN` secret is configured
2. **ECS Permissions**: Role needs ECS, ECR, and CloudWatch permissions
3. **Task Definition**: Must exist before first deployment

**Debug Steps**:
```bash
# Check workflow run status
curl -s "https://api.github.com/repos/wbaxterh/wwhd/actions/runs?per_page=1" | jq '.workflow_runs[0]'

# Check ECS service status
aws ecs describe-services --cluster wwhd-cluster --services wwhd-backend --region us-west-2
```

### GitHub Pages Issues

#### 404 Error on Documentation Site
**Problem**: https://wbaxterh.github.io/wwhd/ returns 404

**Causes**:
1. GitHub Pages not enabled in repository settings
2. Workflow doesn't have proper permissions
3. Build artifacts not uploaded correctly

**Solution**:
1. Enable GitHub Pages in repository settings:
   - Go to Settings → Pages
   - Source: "GitHub Actions"
2. Ensure workflow has proper permissions:
   ```yaml
   permissions:
     contents: read
     pages: write
     id-token: write
   ```

### Container Health Issues

#### Container Fails to Start
**Problem**: ECS task keeps restarting, health checks fail

**Debug Process**:
```bash
# 1. Check recent task failures
aws ecs list-tasks --cluster wwhd-cluster --region us-west-2 --desired-status STOPPED

# 2. Get failure reason
TASK_ARN=$(aws ecs list-tasks --cluster wwhd-cluster --region us-west-2 --desired-status STOPPED | jq -r '.taskArns[0]')
aws ecs describe-tasks --cluster wwhd-cluster --tasks $TASK_ARN --region us-west-2 | jq '.tasks[0].stoppedReason'

# 3. Check container logs
aws logs tail /ecs/wwhd-backend --region us-west-2 --since 10m
```

**Common Exit Codes**:
- **Exit Code 1**: Application startup failure (check imports, dependencies)
- **Exit Code 125**: Docker container creation failed
- **Exit Code 143**: Container received SIGTERM (normal shutdown)

### Performance Issues

#### Slow Chat Response Times (>10 seconds)
**Problem**: Chat responses take very long to process

**Investigation**:
```bash
# Check response times in recent chat attempts
curl -w "Time: %{time_total}s\n" -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"content": "test", "chat_id": null}'
```

**Common Causes**:
1. **Cold Start**: First request after deployment takes longer
2. **OpenAI API Latency**: Network issues or API congestion
3. **Vector Search**: Large knowledge base causing slow retrieval
4. **Container Resources**: Insufficient CPU/memory allocation

**Optimization**:
- Use smaller models (`gpt-4o-mini` vs `gpt-4`)
- Implement response caching
- Optimize vector search parameters
- Scale up container resources

## Debug Commands

### Quick Health Check
```bash
# Test full system health
curl http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/health
```

### Authentication Test Flow
```bash
# Register → Authenticate → Chat
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "debug_user", "email": "debug@test.com", "password": "DebugPass123!", "name": "Debug User"}'

TOKEN=$(curl -s -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=debug_user&password=DebugPass123!" | jq -r .access_token)

curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "test message", "chat_id": null}'
```

### Infrastructure Status
```bash
# ECS Service Health
aws ecs describe-services --cluster wwhd-cluster --services wwhd-backend --region us-west-2

# Recent Logs
aws logs tail /ecs/wwhd-backend --region us-west-2 --since 5m

# Task Definition Details
aws ecs describe-task-definition --task-definition wwhd-backend --region us-west-2
```

## Getting Help

If you encounter issues not covered here:

1. **Check Recent Logs**: Always start with CloudWatch logs
2. **Verify Configuration**: Ensure environment variables are set correctly
3. **Test Components**: Isolate the issue (auth vs chat vs OpenAI)
4. **Check Dependencies**: Verify external services (OpenAI API, GitHub Actions)

For persistent issues, check the [Working Sessions](./working-sessions) page for detailed resolution examples.