# WWHD Backend Deployment Guide

## Fresh Deployment Strategy

The backend is now configured for fresh deployments with empty databases. All data seeding and syncing has been removed from the automatic deployment process to ensure clean, predictable deployments.

## Post-Deployment Setup

### 1. Create Bulk Import User

After deployment, create the bulk import user for remote data import:

```bash
# SSH into the ECS container or run locally against production database
python create_bulk_import_user.py
```

This creates:
- Username: `bulk_import`
- Password: `bulk123`
- Admin privileges for document upload

### 2. Import Data Remotely

Use the API-based bulk import script to populate the knowledge base:

```bash
python api_bulk_import.py \
  --pdf-folder /path/to/pdfs \
  --metadata-file /path/to/metadata.json \
  --namespace general \
  --api-url https://api.weshuber.com \
  --api-token [optional, will authenticate automatically]
```

This approach:
- ✅ Works for both local and production environments
- ✅ Uses existing API endpoints for consistency
- ✅ Handles authentication and error recovery
- ✅ Provides detailed logging and progress tracking
- ✅ Supports resuming failed imports

## Database State

### Fresh Deployment Includes:
- ✅ Empty SQLite database with schema
- ✅ Fresh Qdrant vector database
- ✅ Basic test user (`testuser` / `testpass123`)
- ✅ No seeded documents or content

### Removed from Deployment:
- ❌ Automatic knowledge base seeding
- ❌ Qdrant to SQLite syncing
- ❌ Bulk import user creation
- ❌ Pre-populated documents

## Files Cleaned Up

The following troubleshooting and development files have been removed:
- `bulk_import.py` (replaced by `api_bulk_import.py`)
- `migrate_youtube_urls.py` (one-time script, no longer needed)
- `seed_knowledge_base.py` (automatic seeding removed)
- `create_test_user.py` (consolidated into startup)
- `*debug*.py`, `*test*.py`, `*check*.py` debug scripts
- Log files: `*.txt`, `*log*` files
- Unused task definition files

## Production Workflow

1. **Deploy**: Push code → GitHub Actions deploys fresh backend
2. **Prepare**: Run `create_bulk_import_user.py` to create import user
3. **Import**: Run `api_bulk_import.py` to populate knowledge base
4. **Verify**: Test chat functionality with imported documents

This ensures consistent, clean deployments with full control over data population.