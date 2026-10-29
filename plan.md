# Agentic RAG - Implementation Guide

## Overview

Agentic RAG system with local files + AWS S3 integration.

```
┌─────────────┐
│  Pydantic AI │
└──────┬──────┘
       │
  ┌────▼────┐ ┌──────┐ ┌──────────┐
  │list_files│ │ grep │ │ read_file│
  └────┬────┘ └──┬───┘ └────┬─────┘
       │         │           │
  ┌────▼─────────▼─────────▼────┐
  │    Source Router             │
  │  (local OR S3 OR hybrid)    │
  └──────────┬───────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐        ┌───▼─────┐
│ notes/ │        │ S3 bucket│
└────────┘        └─────────┘
```

## Project Structure

```
agentic-rag/
├── plan.md                      # This file
├── pyproject.toml              # Project config
├── .env.example              # Environment template
│
├── build-tools/               # Learning: step-by-step
├── import-tools/
├── basic-agent/
├── streaming-steps/
├── structured-output/
├── production/
│
├── notes/                     # Local source
│
├── src/
│   ├── config.py            # pydantic-settings config
│   ├── logging.py          # JSON structured logging
│   ├── health.py         # Health checks
│   ├── retry.py          # Retry with backoff
│   │
│   └── tools/
│       ├── local.py        # Thread pool tools
│       ├── local_async.py  # Async tools
│       ├── cache.py       # LRU cache (mtime)
│       ├── s3.py         # boto3 client
│       ├── s3_tools.py    # S3 tools
│       ├── router.py      # Multi-source router
│       └── unified_grep.py
│
└── scripts/
    └── sync_to_s3.py      # Sync utility
```

## Quick Start

### 1. Setup

```bash
# Install dependencies (when pyproject.toml is ready)
# pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure

```bash
# .env file
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=agentic-rag-notes
AWS_DEFAULT_REGION=us-east-1
```

### 3. Test

```bash
# Health checks
python -c "from src.health import run_health_checks; run_health_checks()"

# Local tools
python -c "from src.tools.local import list_files, grep; print(grep('connection'))"

# S3 tools (requires AWS config)
python -c "from src.tools.s3_tools import S3Source; print(S3Source().list_files())"

# Router
python -c "from src.tools.router import router; print(router.list_files())"
```

### 4. Sync to S3

```bash
# Dry run first
python scripts/sync_to_s3.py to-s3 --dry-run

# Actual sync
python scripts/sync_to_s3.py to-s3
```

## Tools

| Tool | File | Description |
|------|------|-------------|
| `list_files` | `src/tools/local.py` | Glob files in local notes/ |
| `grep` | `src/tools/local.py` | Regex search with ThreadPoolExecutor |
| `read_file` | `src/tools/local.py` | Bounded file reads |
| `list_files` | `src/tools/s3_tools.py` | List S3 objects |
| `grep` | `src/tools/s3_tools.py` | Grep S3 files |
| `read_file` | `src/tools/s3_tools.py` | Get S3 object |
| `list_files` | `src/tools/router.py` | Auto-select source |
| `grep` | `src/tools/router.py` | Route to best source |
| `read_file` | `src/tools/router.py` | Route to best source |

## Features Implemented

**Phase 1: Production Patterns**
- ✅ Config via pydantic-settings
- ✅ JSON structured logging
- ✅ Async/await file I/O
- ✅ ThreadPoolExecutor for parallel grep
- ✅ LRU cache with mtime invalidation

**Phase 2: AWS S3 Integration**
- ✅ boto3 session management
- ✅ S3 list_objects, get_object
- ✅ Source router (local/S3/hybrid)
- ✅ Sync script (local ↔ S3)

**Phase 3: Refinements**
- ✅ Unified grep (ripgrep + S3)
- ✅ Health checks
- ✅ Retry with exponential backoff

## Usage Examples

```python
from src.config import settings
from src.tools.router import router

# List files
files = router.list_files()
print(files)

# Grep
hits = router.grep("connection", max_results=10)
print(hits)

# Read file
content = router.read_file("notes/01-engineering-handbook.md", limit=10)
print(content)
```

```python
# Health checks
from src.health import run_health_checks
run_health_checks()
```

```python
# Sync to S3
from scripts.sync_to_s3 import sync_to_s3
result = sync_to_s3(dry_run=True)  # Test first
result = sync_to_s3()  # Actual sync
```

## AWS Credentials

Best practices for AWS credentials:

1. **IAM User** - Create user with S3 permissions
2. **Environment variables** - Set in `.env`
3. **Never commit** - Keep `.env` in `.gitignore`

```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AgenticRAG",
        "Effect": "Allow",
        "Action": [
            "s3:ListBucket",
            "s3:GetObject",
            "s3:PutObject",
            "s3:DeleteObject"
        ],
        "Resource": "arn:aws:s3:::agentic-rag-notes/*"
    }]
}
```