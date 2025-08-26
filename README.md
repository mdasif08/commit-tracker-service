# Commit Tracker Service

An independent microservice for tracking commits from both GitHub webhooks and local Git repositories.

## Overview

The Commit Tracker Service is designed to be a standalone microservice that can track commits from multiple sources:

1. **GitHub Webhooks** - Receives commit data from the GitHub Webhook Service
2. **Local Git Repositories** - Monitors and tracks commits from local development environments

## Features

- **Dual Input Sources**: Handles both webhook and local commit data
- **PostgreSQL Database**: Stores commit history and metadata with diff content
- **RESTful API**: Complete API for commit tracking and retrieval
- **Git Integration**: Built-in Git utilities for local repository monitoring
- **Diff Content Storage**: Stores actual code changes for detailed analysis
- **Pattern Analysis**: Advanced security and code quality analysis without AI
- **Full-Text Search**: Search across commit messages and diff content
- **Metrics & Monitoring**: Prometheus metrics and health checks
- **Docker Support**: Full containerization with Docker and Docker Compose
- **JWT Authentication**: Secure API access with JWT tokens
- **CI/CD Pipeline**: Automated testing, building, and deployment

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ GitHub Webhook  │───▶│ Commit Tracker   │───▶│ PostgreSQL      │
│ Service         │    │ Service          │    │ Database        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Local Git Repo   │
                       │ Monitoring       │
                       └──────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Git (for local repository monitoring)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd commit-tracker-service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Run with Docker Compose (recommended):**
   ```bash
   docker-compose up -d
   ```

5. **Or run locally:**
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
   ```

## Authentication

The service uses JWT (JSON Web Tokens) for authentication. All API endpoints (except health checks and authentication) require a valid JWT token.

### Getting an Access Token

```bash
curl -X POST "http://localhost:8001/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### Using the Token

```bash
curl -X GET "http://localhost:8001/api/commits/test-repo" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Default Users

- **Username**: `admin`, **Password**: `admin123`
- **Username**: `developer`, **Password**: `dev123`

## API Endpoints

### Authentication

- `POST /api/auth/token` - Get JWT access token

### Health & Monitoring

- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /` - Service information

### Commit Tracking (Requires Authentication)

- `POST /api/commits/webhook` - Track commits from GitHub webhook
- `POST /api/commits/local` - Track commits from local repository
- `POST /api/commits` - Create commit record with diff content

### Commit History (Requires Authentication)

- `GET /api/commits/{repository_name}` - Get commit history
- `GET /api/commits/{repository_name}/metrics` - Get commit metrics
- `GET /api/commits` - Get commits with pagination and filtering
- `GET /api/commits/{commit_id}` - Get commit metadata (fast)
- `GET /api/commits/{commit_id}/diff` - Get commit with diff content (detailed)
- `GET /api/commits/{commit_id}/analysis` - Get advanced commit analysis
- `GET /api/commits/{commit_id}/files` - Get individual file changes for a commit
- `GET /api/commits/{commit_id}/summary` - Get commit summary with file statistics
- `GET /api/commits/search` - Full-text search across commits

### File-Level Analysis (Requires Authentication)

- `GET /api/files/{file_id}` - Get detailed analysis for a specific file change

### Git Utilities (Requires Authentication)

- `GET /api/git/status` - Get current Git repository status
- `GET /api/git/commits/recent` - Get recent commits
- `GET /api/git/commits/{commit_hash}` - Get specific commit details

## CI/CD Pipeline

The service includes a comprehensive CI/CD pipeline using GitHub Actions:

### Pipeline Stages

1. **Test**: Runs unit tests with coverage requirements
2. **Security**: Scans for vulnerabilities
3. **Build**: Creates Docker images
4. **Deploy Staging**: Deploys to staging environment
5. **Deploy Production**: Deploys to production environment

### Running the Pipeline

The pipeline automatically triggers on:
- Push to `main` or `develop` branches
- Pull requests to `main` branch

### Manual Deployment

```bash
# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production
./scripts/deploy.sh production
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8001` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/commit_tracker` |
| `GIT_REPO_PATH` | Local Git repository path | `.` |
| `WEBHOOK_SECRET` | Webhook secret for validation | `your-webhook-secret` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` |

### Database Schema

The service uses PostgreSQL with the following main table (enhanced with diff content):

```sql
CREATE TABLE commits (
    id UUID PRIMARY KEY,
    commit_hash VARCHAR(40) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    commit_message TEXT NOT NULL,
    commit_date TIMESTAMP NOT NULL,
    source_type VARCHAR(20) NOT NULL, -- 'webhook' or 'local'
    branch_name VARCHAR(255),
    files_changed JSONB,
    lines_added INTEGER,
    lines_deleted INTEGER,
    parent_commits JSONB,
    status VARCHAR(20) NOT NULL,
    metadata JSONB,
    
    -- NEW: Diff content columns for production-ready analysis
    diff_content TEXT,        -- Actual diff output
    file_diffs JSONB,         -- Structured diff data per file
    diff_hash VARCHAR(64),    -- For deduplication
    
    created_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL,
    
    -- Search optimization for full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            coalesce(commit_message, '') || ' ' || 
            coalesce(author_name, '') || ' ' || 
            coalesce(diff_content, '')
        )
    ) STORED
);
```

### New Features

#### Diff Content Storage
- **diff_content**: Stores the actual git diff output showing code changes
- **file_diffs**: Structured JSON data with per-file change details
- **diff_hash**: SHA256 hash for deduplication and caching

#### Pattern Analysis
- **Security Analysis**: Detects SQL injection, password exposure, authentication bypass
- **Code Quality**: Identifies hardcoded values, poor error handling, missing documentation
- **Performance**: Analyzes complexity, nested loops, long functions

#### Full-Text Search
- Search across commit messages, author names, and diff content
- PostgreSQL full-text search with ranking
- Fast search performance with GIN indexes

## Integration with Other Services

### GitHub Webhook Service

The Commit Tracker Service receives webhook data from the GitHub Webhook Service:

```bash
curl -X POST http://localhost:8001/api/commits/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "push",
    "repository": {"full_name": "user/repo"},
    "commits": [...],
    "ref": "refs/heads/main"
  }'
```

### Local Git Integration

Track local commits:

```bash
curl -X POST http://localhost:8001/api/commits/local \
  -H "Content-Type: application/json" \
  -d '{
    "commit_hash": "abc123...",
    "author_name": "John Doe",
    "author_email": "john@example.com",
    "commit_message": "Add new feature",
    "commit_date": "2024-01-01T12:00:00Z",
    "branch_name": "main",
    "files_changed": ["src/main.py"],
    "lines_added": 10,
    "lines_deleted": 2,
    "parent_commits": ["def456..."],
    "repository_path": "/path/to/repo"
  }'
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
isort src/
```

### Linting

```bash
flake8 src/
```

## Docker

### Build Image

```bash
docker build -t commit-tracker-service .
```

### Run Container

```bash
docker run -p 8001:8001 commit-tracker-service
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f commit-tracker-service

# Stop services
docker-compose down
```

## Usage Examples

### Create Commit with Diff Content

```bash
curl -X POST "http://localhost:8001/api/commits" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "commit_hash": "abc123def456",
    "repository_name": "my-project",
    "author_name": "John Doe",
    "author_email": "john@example.com",
    "commit_message": "Fix security vulnerability",
    "commit_date": "2024-01-15T10:30:00Z",
    "source_type": "webhook",
    "branch_name": "main"
  }'
```

### Get Commit Analysis

```bash
curl -X GET "http://localhost:8001/api/commits/{commit_id}/analysis" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Search Commits

```bash
curl -X GET "http://localhost:8001/api/commits/search?q=password&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Commits with Pagination

```bash
curl -X GET "http://localhost:8001/api/commits?page=1&limit=20&author=John" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring

### Health Check

```bash
curl http://localhost:8001/health
```

### Metrics

```bash
curl http://localhost:8001/metrics
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` in environment variables
   - Ensure database exists and user has permissions

2. **Git Repository Error**
   - Verify Git repository exists at specified path
   - Check Git installation and permissions

3. **Port Already in Use**
   - Change `PORT` in environment variables
   - Check if another service is using port 8001

### Logs

View application logs:

```bash
# Docker
docker-compose logs commit-tracker-service

# Local
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
