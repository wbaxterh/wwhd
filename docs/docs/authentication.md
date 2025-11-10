---
sidebar_position: 2
---

# Authentication

W.W.H.D. uses JWT (JSON Web Token) based authentication for secure API access. All chat endpoints require a valid bearer token.

## User Registration

### POST `/api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "name": "string"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-10T14:33:27"
}
```

**Example:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "herman_fan",
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "name": "Herman Fan"
  }'
```

## Get Access Token

### POST `/api/v1/auth/token`

Obtain a JWT access token for API authentication.

**Request Body (form-encoded):**
```
username=testuser&password=SecurePassword123!
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Example:**
```bash
curl -X POST http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=herman_fan&password=SecurePassword123!"
```

## Using the Token

Include the access token in the `Authorization` header for all authenticated requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Details

- **Type**: Bearer token
- **Expiry**: 24 hours (86400 seconds)
- **Claims**: Includes user_id, username, is_admin
- **Algorithm**: HS256

## Password Requirements

- Minimum 8 characters
- Must contain at least one uppercase letter
- Must contain at least one lowercase letter
- Must contain at least one number
- Must contain at least one special character

## Error Responses

### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "123"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid username or password"
}
```

### 409 Conflict
```json
{
  "detail": "Username or email already exists"
}
```

## Security Notes

- Passwords are hashed using bcrypt
- Tokens are signed with a secure secret
- HTTPS is recommended for production use
- Tokens should be stored securely on the client side
- Refresh tokens are not currently implemented (tokens expire after 24 hours)