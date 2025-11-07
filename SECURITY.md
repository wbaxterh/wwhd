# Security

## Authentication Architecture

### JWT Configuration

```yaml
jwt:
  algorithm: RS256
  access_token_ttl: 3600  # 1 hour
  refresh_token_ttl: 604800  # 7 days
  issuer: wwhd
  audience: wwhd-users
  key_rotation: 30 days
```

### Token Claims

```json
{
  "sub": "user_123",
  "email": "user@example.com",
  "username": "herman_fan",
  "role": "user",
  "iat": 1706198400,
  "exp": 1706202000,
  "iss": "wwhd",
  "aud": "wwhd-users",
  "jti": "token_unique_id"
}
```

## Role-Based Access Control (RBAC)

### Roles & Permissions

| Role | Permissions |
|------|------------|
| viewer | Read chat history, view public content |
| user | Chat, manage own sessions, view usage |
| admin | All user permissions + document management, user management, system config |

### Permission Matrix

| Endpoint | Viewer | User | Admin |
|----------|--------|------|-------|
| GET /health | ✅ | ✅ | ✅ |
| POST /chat | ❌ | ✅ | ✅ |
| GET /me | ❌ | ✅ | ✅ |
| POST /admin/* | ❌ | ❌ | ✅ |

## Rate Limiting

```python
RATE_LIMITS = {
    "anonymous": {
        "requests_per_minute": 10,
        "tokens_per_day": 1000
    },
    "user": {
        "requests_per_minute": 60,
        "tokens_per_day": 100000
    },
    "admin": {
        "requests_per_minute": 600,
        "tokens_per_day": "unlimited"
    }
}
```

## CORS Policy

```python
CORS_CONFIG = {
    "allowed_origins": [
        "https://wwhd.ai",
        "https://app.wwhd.ai",
        "http://localhost:3000"  # Dev only
    ],
    "allowed_methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    "allowed_headers": ["Authorization", "Content-Type"],
    "expose_headers": ["X-RateLimit-*"],
    "allow_credentials": True,
    "max_age": 86400
}
```

## Input Validation

### Sanitization Rules

```python
def sanitize_user_input(text: str) -> str:
    # Remove HTML/script tags
    text = bleach.clean(text, tags=[], strip=True)

    # Limit length
    text = text[:10000]

    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize whitespace
    text = ' '.join(text.split())

    return text
```

## Secrets Management

### Environment Variables

```yaml
secrets:
  storage: AWS Secrets Manager
  rotation: 90 days
  access_control: IAM roles

required_secrets:
  - JWT_SECRET
  - OPENAI_API_KEY
  - QDRANT_API_KEY
  - DATABASE_URL
```

## Safety Guardrails

### Content Filtering

```python
SAFETY_RULES = {
    "block_patterns": [
        r"medical diagnosis",
        r"legal advice",
        r"self-harm",
        r"violence"
    ],
    "require_disclaimer": [
        "health",
        "investment",
        "medical",
        "legal"
    ]
}
```

### Response Moderation

```python
async def moderate_response(content: str) -> dict:
    violations = {
        "harmful": False,
        "medical": False,
        "legal": False,
        "financial": False
    }

    # Check for violations
    for category, patterns in SAFETY_PATTERNS.items():
        if any(re.search(p, content, re.I) for p in patterns):
            violations[category] = True

    return violations
```

## Data Privacy

### PII Handling

```yaml
pii_policy:
  detection: automated scanning
  storage: encrypted at rest
  retention: 90 days
  deletion: hard delete + audit log

excluded_from_logs:
  - password
  - api_key
  - credit_card
  - ssn
```

### Audit Logging

```python
@dataclass
class AuditLog:
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    ip_address: str
    user_agent: str
    result: str
    metadata: dict
```

## Encryption

### Data at Rest

```yaml
encryption_at_rest:
  database: AES-256
  s3_buckets: SSE-S3
  qdrant: TLS + encryption
  backups: AES-256
```

### Data in Transit

```yaml
encryption_in_transit:
  api: TLS 1.3
  internal: mTLS
  websocket: WSS
  database: SSL/TLS
```

## Security Headers

```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}
```

## Vulnerability Management

### Dependency Scanning

```yaml
scanning:
  schedule: daily
  tools:
    - safety (Python)
    - npm audit (Node.js)
    - trivy (containers)

severity_thresholds:
  critical: block deployment
  high: alert + 7 day fix
  medium: alert + 30 day fix
  low: track only
```

## Incident Response

### Severity Levels

| Level | Response Time | Escalation |
|-------|--------------|------------|
| Critical | 15 minutes | CTO + Security |
| High | 1 hour | Engineering Lead |
| Medium | 4 hours | On-call Engineer |
| Low | 24 hours | Backlog |

### Response Procedures

1. **Detection**: Automated alerts via CloudWatch
2. **Containment**: Isolate affected systems
3. **Investigation**: Review logs and traces
4. **Remediation**: Deploy fixes
5. **Recovery**: Restore normal operations
6. **Post-mortem**: Document lessons learned

## Acceptance Criteria

- ✅ JWT authentication implemented
- ✅ RBAC enforced on all endpoints
- ✅ Rate limiting per user/role
- ✅ Input sanitization on all user inputs
- ✅ Safety checks on AI responses
- ✅ PII excluded from logs
- ✅ TLS 1.3 for all connections
- ✅ Security headers on all responses