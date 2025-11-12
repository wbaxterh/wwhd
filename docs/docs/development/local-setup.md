---
sidebar_position: 1
---

# Local Development Setup

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Documentation site |
| Docker | 24+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Git | 2.40+ | Version control |
| AWS CLI | 2.13+ | AWS service interaction |

### Recommended Tools

- **VS Code** with Python and Docker extensions
- **Postman** for API testing
- **TablePlus** for database inspection
- **k9s** for Kubernetes management (future)

## Repository Setup

### 1. Clone the Repository

```bash
# Clone the main backend repository
git clone https://github.com/wbaxterh/wwhd.git
cd wwhd

# Initialize submodules if any
git submodule update --init --recursive
```

### 2. Environment Configuration

Create `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

**Required Environment Variables:**

```env
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite:///./data/app.db

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_for_local

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
MODEL_CHAT=gpt-4o-mini
MODEL_EMBED=text-embedding-3-small
ENABLE_OPENAI=true

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# CORS
ALLOW_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Optional Services
REDIS_URL=redis://localhost:6379
ENABLE_CACHE=false
ENABLE_MONITORING=false
```

## Python Development Environment

### 1. Virtual Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Dependencies

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

### 3. Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run hooks on all files (first time)
pre-commit run --all-files
```

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88", "--extend-ignore=E203"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Docker Development

### 1. Docker Compose Setup

**`docker-compose.yml`:**

```yaml
version: '3.8'

services:
  fastapi:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: wwhd-api
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./data:/data
    environment:
      - APP_ENV=development
      - DATABASE_URL=sqlite:////data/app.db
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - qdrant
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  qdrant:
    image: qdrant/qdrant:latest
    container_name: wwhd-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334

  redis:
    image: redis:alpine
    container_name: wwhd-redis
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data

  # Optional: Database UI
  adminer:
    image: adminer
    container_name: wwhd-adminer
    ports:
      - "8080:8080"
    environment:
      - ADMINER_DEFAULT_SERVER=sqlite
```

### 2. Development Dockerfile

**`backend/Dockerfile.dev`:**

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development server with hot reload
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Running with Docker Compose

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f fastapi

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Running Locally Without Docker

### 1. Start Qdrant

```bash
# Using Docker for Qdrant only
docker run -p 6333:6333 -p 6334:6334 \
  -v ./data/qdrant:/qdrant/storage \
  qdrant/qdrant
```

### 2. Start FastAPI

```bash
# Navigate to backend directory
cd backend

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the Python module
python -m uvicorn main:app --reload
```

### 3. Initialize Database

```bash
# Run database migrations
cd backend
python scripts/init_db.py

# Create test user (optional)
python scripts/create_test_user.py
```

## Testing

### 1. Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "unit"
```

### 2. Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -m "integration"

# Test with real OpenAI API (expensive!)
ENABLE_OPENAI=true pytest tests/integration/test_chat_flow.py
```

### 3. Load Testing

```bash
# Using locust
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
```

**`tests/load/locustfile.py`:**

```python
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/token",
            data={"username": "test", "password": "test123"})
        self.token = response.json()["access_token"]

    @task(3)
    def send_message(self):
        self.client.post("/api/v1/chat/chat",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"content": "Hello Herman", "chat_id": None})

    @task(1)
    def check_health(self):
        self.client.get("/health")
```

## Debugging

### 1. VS Code Configuration

**`.vscode/launch.json`:**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "APP_ENV": "development",
        "LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### 2. Logging Configuration

```python
# backend/config/logging.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configure application logging."""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log"),
        ],
    )

    # Set third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
```

### 3. Database Inspection

```bash
# Using SQLite CLI
sqlite3 data/app.db

# Common commands
.tables                    # List all tables
.schema users             # Show table schema
SELECT * FROM users;      # Query data
.exit                     # Exit

# Using Python
python
>>> from backend.database import SessionLocal, User
>>> db = SessionLocal()
>>> users = db.query(User).all()
>>> for user in users:
...     print(user.username, user.email)
```

## API Testing

### 1. Using Postman

Import the collection from `docs/static/WWHD.postman_collection.json`

### 2. Using curl

```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"dev","email":"dev@test.com","password":"DevPass123","name":"Developer"}'

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dev&password=DevPass123" | jq -r .access_token)

# Send chat message
curl -X POST http://localhost:8000/api/v1/chat/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello Herman","chat_id":null}'
```

### 3. Using Python Requests

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Register user
response = requests.post(f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": "pydev",
        "email": "pydev@test.com",
        "password": "PyDev123",
        "name": "Python Developer"
    })
print(response.json())

# Get token
response = requests.post(f"{BASE_URL}/api/v1/auth/token",
    data={"username": "pydev", "password": "PyDev123"})
token = response.json()["access_token"]

# Chat
response = requests.post(f"{BASE_URL}/api/v1/chat/chat",
    headers={"Authorization": f"Bearer {token}"},
    json={"content": "What is meditation?", "chat_id": None})
print(response.json())
```

## Common Issues & Solutions

### Issue: Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

### Issue: SQLite Database Locked

```bash
# Close all database connections
# Restart the application
# Use WAL mode for SQLite
```

```python
# In database configuration
engine = create_engine(
    "sqlite:///./data/app.db",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=True,
)

# Enable WAL mode
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
```

### Issue: OpenAI API Key Invalid

```bash
# Verify key is set
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: Qdrant Connection Failed

```bash
# Check Qdrant is running
docker ps | grep qdrant

# Test connection
curl http://localhost:6333/health

# Check logs
docker logs wwhd-qdrant
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
# Write tests
# Run tests locally
pytest

# Commit changes
git add .
git commit -m "feat: Add your feature"

# Push to GitHub
git push origin feature/your-feature

# Create Pull Request
```

### 2. Code Quality Checks

```bash
# Format code
black backend/
isort backend/

# Lint code
flake8 backend/
mypy backend/

# Security check
bandit -r backend/
safety check

# Run all checks
make lint
```

### 3. Documentation

```bash
# Generate API documentation
cd backend
python -m mkdocs serve

# Update OpenAPI schema
python scripts/export_openapi.py
```

---

*For deployment instructions, see [Deployment Guide](../deployment/aws-infrastructure)*