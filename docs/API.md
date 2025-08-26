# Commit Tracker Service API Documentation

## Overview

The Commit Tracker Service is a microservice that tracks commits from both GitHub webhooks and local Git repositories. It provides APIs for tracking commits, retrieving commit history, and generating metrics.

## Base URL

```
http://localhost:8001
```

## Authentication

Currently, the service does not require authentication. In production, consider implementing API key authentication or JWT tokens.

## Endpoints

### Health Check

#### GET /health

Check the health status of the service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "1.0.0",
  "database_status": "healthy"
}
```

### Metrics

#### GET /metrics

Get Prometheus metrics (if enabled).

**Response:** Prometheus metrics format

### Commit Tracking

#### POST /api/commits/webhook

Track commits from GitHub webhook service.

**Request Body:**
```json
{
  "event_type": "push",
  "repository": {
    "full_name": "owner/repo"
  },
  "commits": [
    {
      "id": "commit_hash",
      "author": {
        "name": "Author Name",
        "email": "author@example.com"
      },
      "message": "Commit message",
      "timestamp": "2023-01-01T00:00:00Z",
      "modified": ["file1.py"],
      "added": ["file2.py"],
      "removed": [],
      "stats": {
        "additions": 10,
        "deletions": 5
      },
      "parents": ["parent_hash"]
    }
  ],
  "sender": {"login": "username"},
  "ref": "refs/heads/main",
  "before": "before_hash",
  "after": "after_hash",
  "created": false,
  "compare": "https://github.com/owner/repo/compare/before...after"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tracked 1 commits from webhook",
  "commits": [
    {
      "id": "uuid",
      "commit_hash": "commit_hash",
      "repository_name": "owner/repo",
      "status": "processed",
      "created_at": "2023-01-01T00:00:00Z",
      "processed_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /api/commits/local

Track commits from local Git repository.

**Request Body:**
```json
{
  "commit_hash": "commit_hash",
  "repository_path": "/path/to/repo",
  "author_name": "Author Name",
  "author_email": "author@example.com",
  "commit_message": "Commit message",
  "commit_date": "2023-01-01T00:00:00Z",
  "branch_name": "main",
  "files_changed": ["file1.py", "file2.py"],
  "lines_added": 10,
  "lines_deleted": 5,
  "parent_commits": ["parent_hash"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Local commit tracked successfully",
  "commit": {
    "id": "uuid",
    "commit_hash": "commit_hash",
    "repository_name": "repo",
    "status": "processed",
    "created_at": "2023-01-01T00:00:00Z",
    "processed_at": "2023-01-01T00:00:00Z"
  }
}
```

### Commit History

#### GET /api/commits/{repository_name}

Get commit history for a repository.

**Parameters:**
- `page` (query): Page number (default: 1)
- `page_size` (query): Page size (default: 50, max: 100)

**Response:**
```json
{
  "repository_name": "owner/repo",
  "commits": [
    {
      "id": "uuid",
      "commit_hash": "commit_hash",
      "repository_name": "owner/repo",
      "status": "processed",
      "created_at": "2023-01-01T00:00:00Z",
      "processed_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total_count": 100,
  "page": 1,
  "page_size": 50
}
```

#### GET /api/commits/{repository_name}/metrics

Get commit metrics and statistics for a repository.

**Response:**
```json
{
  "repository_name": "owner/repo",
  "total_commits": 100,
  "commits_today": 5,
  "commits_this_week": 20,
  "commits_this_month": 80,
  "average_commits_per_day": 3.5,
  "most_active_author": "Author Name",
  "most_active_branch": "main",
  "last_commit_date": "2023-01-01T00:00:00Z"
}
```

### Git Utilities

#### GET /api/git/status

Get current Git repository status.

**Response:**
```json
{
  "repository_name": "repo",
  "current_branch": "main",
  "uncommitted_changes": ["file1.py", "file2.py"]
}
```

#### GET /api/git/commits/recent

Get recent commits from local repository.

**Parameters:**
- `count` (query): Number of commits to retrieve (default: 10, max: 50)

**Response:**
```json
{
  "commits": [
    {
      "hash": "commit_hash",
      "author_name": "Author Name",
      "author_email": "author@example.com",
      "commit_date": "2023-01-01T00:00:00Z",
      "message": "Commit message",
      "parent_hashes": ["parent_hash"]
    }
  ]
}
```

#### GET /api/git/commits/{commit_hash}

Get detailed information for a specific commit.

**Response:**
```json
{
  "hash": "commit_hash",
  "author_name": "Author Name",
  "author_email": "author@example.com",
  "commit_date": "2023-01-01T00:00:00Z",
  "message": "Commit message",
  "parent_hashes": ["parent_hash"],
  "files_changed": ["file1.py", "file2.py"],
  "lines_added": 10,
  "lines_deleted": 5,
  "stats": {
    "total_files": 2,
    "total_lines": 15
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Validation error",
  "detail": "Field 'commit_hash' is required",
  "timestamp": "2023-01-01T00:00:00Z",
  "request_id": "uuid"
}
```

### 404 Not Found
```json
{
  "error": "Repository not found",
  "timestamp": "2023-01-01T00:00:00Z",
  "request_id": "uuid"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Database connection failed",
  "timestamp": "2023-01-01T00:00:00Z",
  "request_id": "uuid"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Monitoring

The service exposes Prometheus metrics at `/metrics` endpoint. Key metrics include:

- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: HTTP request latency
- `commit_events_total`: Total commit events by source type and status

## Examples

### Track Webhook Commit

```bash
curl -X POST http://localhost:8001/api/commits/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "push",
    "repository": {"full_name": "test/repo"},
    "commits": [{
      "id": "abc123",
      "author": {"name": "Test Author", "email": "test@example.com"},
      "message": "Test commit",
      "timestamp": "2023-01-01T00:00:00Z"
    }],
    "sender": {"login": "testuser"},
    "ref": "refs/heads/main",
    "before": "before123",
    "after": "after456"
  }'
```

### Get Commit History

```bash
curl http://localhost:8001/api/commits/test/repo?page=1&page_size=10
```

### Get Commit Metrics

```bash
curl http://localhost:8001/api/commits/test/repo/metrics
```
