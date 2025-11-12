---
sidebar_position: 2
---

# Security Best Practices

## Overview

Security is implemented through a multi-layered defense strategy, combining network security, application-level protections, data encryption, and operational security practices.

## Authentication & Authorization

### JWT Token Security

**Token Configuration:**
```python
JWT_SETTINGS = {
    "algorithm": "HS256",
    "expiry_hours": 24,
    "refresh_token_hours": 168,  # 7 days
    "issuer": "wwhd-api",
    "audience": "wwhd-users"
}
```

**Best Practices:**
- Use strong, randomly generated JWT secrets (256-bit minimum)
- Implement token rotation with refresh tokens
- Set appropriate expiration times
- Include rate limiting on token endpoints
- Log all authentication attempts

### Role-Based Access Control (RBAC)

```python
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

PERMISSIONS = {
    "user": [
        "chat:create",
        "chat:read_own",
        "profile:read_own",
        "profile:update_own"
    ],
    "moderator": [
        "chat:read_all",
        "chat:moderate",
        "users:read",
        "reports:manage"
    ],
    "admin": [
        "users:manage",
        "system:configure",
        "data:export",
        "logs:read"
    ]
}
```

## Input Validation & Sanitization

### Request Validation

```python
from pydantic import BaseModel, validator
import bleach

class ChatMessage(BaseModel):
    content: str
    chat_id: Optional[str] = None

    @validator('content')
    def sanitize_content(cls, v):
        # Remove potentially dangerous HTML/JS
        cleaned = bleach.clean(v, strip=True)

        # Length limits
        if len(cleaned) > 4000:
            raise ValueError("Message too long")

        # Content filtering
        if any(word in cleaned.lower() for word in BLOCKED_WORDS):
            raise ValueError("Message contains inappropriate content")

        return cleaned

    @validator('chat_id')
    def validate_chat_id(cls, v):
        if v and not re.match(r'^[a-f0-9-]{36}$', v):
            raise ValueError("Invalid chat ID format")
        return v
```

### SQL Injection Prevention

```python
# Always use parameterized queries
def get_user_messages(user_id: str, limit: int = 10):
    query = """
        SELECT * FROM messages
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit
    """
    return db.execute(text(query), {
        "user_id": user_id,
        "limit": limit
    })
```

## API Security

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

@app.post("/api/v1/chat/chat")
@limiter.limit("10 per minute")
async def chat_endpoint(request: Request, ...):
    pass

# Different limits for different endpoints
@limiter.limit("5 per minute")  # Stricter for auth
async def login_endpoint():
    pass

@limiter.limit("60 per minute")  # More generous for health
async def health_endpoint():
    pass
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "https://wwhd.ai",
    "https://app.wwhd.ai",
    "http://localhost:3000",  # Dev only
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

### Request Logging & Monitoring

```python
import logging
from typing import Dict
import json

security_logger = logging.getLogger("security")

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Log security-relevant events
    if should_log_request(request):
        log_data = {
            "timestamp": datetime.utcnow(),
            "ip": get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "method": request.method,
            "path": request.url.path,
            "user_id": getattr(request.state, "user_id", None)
        }
        security_logger.info(json.dumps(log_data))

    response = await call_next(request)

    # Log failed authentication attempts
    if response.status_code == 401:
        security_logger.warning(f"Failed auth: {log_data}")

    return response

def should_log_request(request: Request) -> bool:
    """Determine if request should be logged for security."""
    security_paths = ["/auth/", "/admin/", "/api/v1/"]
    return any(path in str(request.url) for path in security_paths)
```

## Data Protection

### Encryption at Rest

**Database Encryption:**
```python
# For SQLite with SQLCipher
DATABASE_URL = "sqlite+sqlcipher://:password@/path/to/database.db"

# For PostgreSQL
DATABASE_CONFIG = {
    "sslmode": "require",
    "sslcert": "/path/to/client-cert.pem",
    "sslkey": "/path/to/client-key.pem",
    "sslrootcert": "/path/to/ca-cert.pem"
}
```

**Field-Level Encryption:**
```python
from cryptography.fernet import Fernet
import os

class EncryptedField:
    def __init__(self):
        self.key = os.environ["FIELD_ENCRYPTION_KEY"].encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, encrypted_value: str) -> str:
        return self.cipher.decrypt(encrypted_value.encode()).decode()

# Example usage for PII
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email_encrypted = Column(String)  # Encrypted email

    @property
    def email(self):
        return encryption.decrypt(self.email_encrypted)

    @email.setter
    def email(self, value):
        self.email_encrypted = encryption.encrypt(value)
```

### PII Detection & Masking

```python
import re
from typing import Dict

PII_PATTERNS = {
    "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
    "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "phone": r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
}

def detect_pii(text: str) -> Dict[str, list]:
    """Detect potential PII in text."""
    detected = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            detected[pii_type] = matches
    return detected

def mask_pii(text: str) -> str:
    """Mask PII in text for logging/display."""
    masked = text
    for pii_type, pattern in PII_PATTERNS.items():
        masked = re.sub(pattern, f"[MASKED_{pii_type.upper()}]", masked)
    return masked
```

## Content Security

### Safety Agent Implementation

```python
class SafetyAgent:
    def __init__(self):
        self.openai_moderation = OpenAIModerationClient()
        self.custom_filters = load_custom_filters()

    async def check_safety(self, content: str) -> SafetyResult:
        """Multi-layer safety checking."""

        # 1. Custom keyword filtering
        custom_result = self.check_custom_filters(content)
        if custom_result.blocked:
            return custom_result

        # 2. OpenAI moderation
        openai_result = await self.openai_moderation.check(content)
        if openai_result.flagged:
            return SafetyResult(
                blocked=True,
                reason="openai_moderation",
                categories=openai_result.categories
            )

        # 3. Context-aware checking
        context_result = self.check_context_appropriateness(content)

        return SafetyResult(
            blocked=False,
            confidence=min(
                custom_result.confidence,
                openai_result.confidence,
                context_result.confidence
            )
        )
```

### Content Filtering Rules

```yaml
content_filters:
  blocked_categories:
    - violence
    - self_harm
    - hate_speech
    - illegal_activities
    - explicit_content

  warning_categories:
    - medical_advice
    - financial_advice
    - legal_advice

  custom_rules:
    - pattern: "(hack|crack|exploit)"
      action: block
      reason: "Security-related content not allowed"

    - pattern: "(depression|suicide|self-harm)"
      action: redirect
      message: "Please contact a mental health professional"
      resources:
        - "National Suicide Prevention Lifeline: 988"
        - "Crisis Text Line: Text HOME to 741741"
```

## Infrastructure Security

### AWS Security Groups

```yaml
# API Security Group
sg-backend-api:
  ingress:
    - protocol: tcp
      from_port: 8000
      to_port: 8000
      source_security_group_id: sg-alb-public
      description: "API traffic from ALB only"

    - protocol: tcp
      from_port: 6333
      to_port: 6333
      self: true
      description: "Qdrant internal communication"

  egress:
    - protocol: tcp
      from_port: 443
      to_port: 443
      cidr_blocks: ["0.0.0.0/0"]
      description: "HTTPS outbound (OpenAI API)"

    - protocol: tcp
      from_port: 53
      to_port: 53
      cidr_blocks: ["0.0.0.0/0"]
      description: "DNS resolution"

# Database Security Group
sg-database:
  ingress:
    - protocol: tcp
      from_port: 2049
      to_port: 2049
      source_security_group_id: sg-backend-api
      description: "EFS access from backend only"
```

### Secrets Management

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "wwhd/production/openai-key" \
  --description "OpenAI API key for production" \
  --secret-string '{"api_key":"sk-..."}'

# Rotate secrets automatically
aws secretsmanager rotate-secret \
  --secret-id "wwhd/production/openai-key" \
  --rotation-rules AutomaticallyAfterDays=30
```

### WAF Rules

```yaml
waf_rules:
  - name: AWSManagedRulesCommonRuleSet
    priority: 1
    action: block

  - name: AWSManagedRulesKnownBadInputsRuleSet
    priority: 2
    action: block

  - name: RateLimitRule
    priority: 100
    action: block
    rate_limit:
      limit: 2000
      window: 5  # minutes

  - name: IPWhitelistRule
    priority: 200
    action: allow
    ip_whitelist:
      - "203.0.113.0/24"  # Office network

  - name: BlockSQLiRule
    priority: 300
    action: block
    sqli_match_statement:
      field_to_match: body
      text_transformations:
        - priority: 0
          type: URL_DECODE
```

## Monitoring & Alerting

### Security Metrics

```python
SECURITY_METRICS = {
    "authentication": [
        "failed_login_attempts",
        "suspicious_login_patterns",
        "token_abuse_attempts"
    ],

    "api_security": [
        "rate_limit_violations",
        "invalid_request_patterns",
        "unauthorized_access_attempts"
    ],

    "content_safety": [
        "safety_agent_interventions",
        "content_violations_by_category",
        "pii_detection_events"
    ]
}
```

### Automated Incident Response

```python
class SecurityIncidentHandler:
    async def handle_incident(self, incident: SecurityIncident):
        """Automated response to security incidents."""

        if incident.severity == "critical":
            # Immediate response
            await self.block_ip(incident.source_ip)
            await self.revoke_user_tokens(incident.user_id)
            await self.notify_security_team(incident)

        elif incident.severity == "high":
            # Elevated monitoring
            await self.increase_monitoring(incident.user_id)
            await self.notify_security_team(incident)

        elif incident.severity == "medium":
            # Log and monitor
            await self.log_incident(incident)
            await self.add_to_watchlist(incident.source_ip)
```

### Security Auditing

```python
class SecurityAuditLogger:
    def log_auth_event(self, event_type: str, user_id: str, details: dict):
        audit_log = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": details.get("ip"),
            "user_agent": details.get("user_agent"),
            "success": details.get("success", False),
            "failure_reason": details.get("failure_reason")
        }

        # Send to centralized logging
        self.security_logger.info(json.dumps(audit_log))

        # Send to SIEM if available
        if self.siem_client:
            self.siem_client.send_event(audit_log)

# Usage examples
audit = SecurityAuditLogger()

# Failed login
audit.log_auth_event("login_failed", "user123", {
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "failure_reason": "invalid_password"
})

# Successful admin action
audit.log_auth_event("admin_action", "admin456", {
    "action": "user_deletion",
    "target": "user789",
    "success": True
})
```

## Compliance & Standards

### Data Retention

```python
DATA_RETENTION_POLICY = {
    "user_messages": {
        "retention_days": 365,
        "anonymization_after_days": 90
    },
    "audit_logs": {
        "retention_days": 2555,  # 7 years
        "archive_after_days": 365
    },
    "error_logs": {
        "retention_days": 90
    },
    "access_logs": {
        "retention_days": 30
    }
}

async def enforce_retention_policy():
    """Automated data retention enforcement."""
    for data_type, policy in DATA_RETENTION_POLICY.items():
        # Delete old data
        cutoff_date = datetime.utcnow() - timedelta(
            days=policy["retention_days"]
        )
        await delete_data_older_than(data_type, cutoff_date)

        # Anonymize if required
        if "anonymization_after_days" in policy:
            anon_date = datetime.utcnow() - timedelta(
                days=policy["anonymization_after_days"]
            )
            await anonymize_data_older_than(data_type, anon_date)
```

### Privacy Protection

```python
class PrivacyManager:
    def anonymize_user_data(self, user_id: str):
        """Anonymize user data while preserving analytics."""

        # Generate anonymous ID
        anon_id = self.generate_anonymous_id(user_id)

        # Update messages
        db.execute("""
            UPDATE messages
            SET user_id = :anon_id,
                content = anonymize_pii(content)
            WHERE user_id = :user_id
        """, {"anon_id": anon_id, "user_id": user_id})

        # Remove PII from user record
        db.execute("""
            UPDATE users
            SET email = '[ANONYMIZED]',
                name = '[ANONYMIZED]',
                anonymized_at = :now
            WHERE id = :user_id
        """, {"user_id": user_id, "now": datetime.utcnow()})

    def export_user_data(self, user_id: str) -> dict:
        """Export all user data for GDPR compliance."""
        return {
            "personal_info": self.get_user_profile(user_id),
            "messages": self.get_user_messages(user_id),
            "activity_log": self.get_user_activity(user_id),
            "preferences": self.get_user_preferences(user_id)
        }
```

## Security Testing

### Penetration Testing Checklist

```yaml
security_tests:
  authentication:
    - JWT token manipulation
    - Session fixation attacks
    - Password brute force attempts
    - Account enumeration

  authorization:
    - Privilege escalation
    - Horizontal access control bypass
    - Admin function access

  injection:
    - SQL injection
    - NoSQL injection
    - Command injection
    - LDAP injection

  api_security:
    - Rate limiting bypass
    - HTTP method tampering
    - Parameter pollution
    - API versioning attacks
```

### Automated Security Scanning

```bash
#!/bin/bash
# security-scan.sh

echo "Running security scans..."

# SAST with Bandit
bandit -r backend/ -f json -o reports/bandit.json

# Dependency vulnerabilities
safety check --json --output reports/safety.json

# Secrets scanning
truffleHog --json backend/ > reports/secrets.json

# Docker image scanning
trivy image wwhd-backend:latest --format json --output reports/trivy.json

# API security testing
newman run tests/security/api-security.postman_collection.json \
  --reporters cli,json --reporter-json-export reports/api-security.json

echo "Security scan complete. Reports in reports/ directory."
```

---

*For monitoring and alerting, see [Monitoring Guide](../operations/monitoring)*