# Commit Tracker Service - CLI API Guide

## Server Information
- **Base URL**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/api/docs` (when DEBUG=True)
- **Health Check**: `http://localhost:8000/health`

## Quick Start

### 1. Start the Server
```bash
# Navigate to commit-tracker-service directory
cd commit-tracker-service

# Start the server
PYTHONPATH=. python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### 2. Test the API
```bash
# Test health endpoint
curl -X GET "http://localhost:8000/health"

# Or use the test script
python test_api.py

# Or run comprehensive tests with JSON files
python test_api_with_json.py
```

## Authentication
Most endpoints require authentication. First, get an access token:

```bash
# Get access token
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Response will be:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "token_type": "bearer"
# }
```

## Using JSON Files for Testing

The service includes JSON files in the `data/` directory for easy API testing:

### Available JSON Files
- `data/auth_token.json` - Authentication token request
- `data/create_commit.json` - Create a new commit record
- `data/track_webhook_commit.json` - Track GitHub webhook commits
- `data/track_local_commit.json` - Track local git commits

### Example Usage with JSON Files
```bash
# Create a commit using JSON file
curl -X POST "http://localhost:8000/api/commits" \
  -H "Content-Type: application/json" \
  -d @data/create_commit.json

# Track webhook commit with authentication
curl -X POST "http://localhost:8000/api/commits/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d @data/track_webhook_commit.json

# Track local commit with authentication
curl -X POST "http://localhost:8000/api/commits/local" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d @data/track_local_commit.json
```

### Run Comprehensive Tests
```bash
# Test all endpoints using JSON files
python test_api_with_json.py
```

## Basic Health & Status Endpoints

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

### 2. Root Endpoint
```bash
curl -X GET "http://localhost:8000/"
```

### 3. Git Status
```bash
curl -X GET "http://localhost:8000/api/git/status"
```

### 4. Recent Commits
```bash
curl -X GET "http://localhost:8000/api/git/commits/recent?count=5"
```

## Commit Management Endpoints

### 1. Get All Commits (with pagination)
```bash
# Get first page with 20 items
curl -X GET "http://localhost:8000/api/commits?page=1&limit=20"

# Filter by repository
curl -X GET "http://localhost:8000/api/commits?repository=commit-tracker-service"

# Filter by author
curl -X GET "http://localhost:8000/api/commits?author=your-email@example.com"

# Filter by status
curl -X GET "http://localhost:8000/api/commits?status=PROCESSED"
```

### 2. Get Specific Commit (metadata only)
```bash
curl -X GET "http://localhost:8000/api/commits/{commit_id}"
```

### 3. Get Commit with Diff Content
```bash
curl -X GET "http://localhost:8000/api/commits/{commit_id}/diff"
```

### 4. Get Commit Analysis
```bash
curl -X GET "http://localhost:8000/api/commits/{commit_id}/analysis"
```

### 5. Get Commit Files
```bash
curl -X GET "http://localhost:8000/api/commits/{commit_id}/files"
```

### 6. Get Commit Summary
```bash
curl -X GET "http://localhost:8000/api/commits/{commit_id}/summary"
```

### 7. Get File Analysis
```bash
curl -X GET "http://localhost:8000/api/files/{file_id}"
```

## Search Endpoints

### 1. Full-text Search
```bash
curl -X GET "http://localhost:8000/api/commits/search?q=your_search_term&limit=20"
```

## Git Information Endpoints

### 1. Get Commit Info by Hash
```bash
curl -X GET "http://localhost:8000/api/git/commits/{commit_hash}"
```

## Advanced Usage Examples

### 1. Create a New Commit Record
```bash
curl -X POST "http://localhost:8000/api/commits" \
  -H "Content-Type: application/json" \
  -d '{
    "commit_hash": "abc123def456",
    "repository_name": "my-repo",
    "author_name": "John Doe",
    "author_email": "john@example.com",
    "commit_message": "Add new feature",
    "commit_date": "2024-01-15T10:30:00Z",
    "source_type": "LOCAL",
    "branch_name": "main",
    "files_changed": ["src/main.py", "tests/test_main.py"],
    "lines_added": 50,
    "lines_deleted": 10,
    "parent_commits": [],
    "status": "PROCESSED"
  }'
```

### 2. Track Local Commit
```bash
curl -X POST "http://localhost:8000/api/commits/local" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "commit_hash": "abc123def456",
    "repository_path": "/path/to/repo",
    "branch_name": "main"
  }'
```

### 3. Track Webhook Commit
```bash
curl -X POST "http://localhost:8000/api/commits/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "event_type": "push",
    "repository": {
      "full_name": "user/repo",
      "name": "repo"
    },
    "commits": [
      {
        "id": "abc123def456",
        "message": "Add new feature",
        "author": {
          "name": "John Doe",
          "email": "john@example.com"
        },
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ]
  }'
```

## Authentication Examples

### Using Access Token
```bash
# Store token in variable
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Use token in requests
curl -X GET "http://localhost:8000/api/commits" \
  -H "Authorization: Bearer $TOKEN"
```

### Using Environment Variable
```bash
# Set token as environment variable
export API_TOKEN="your_access_token_here"

# Use in requests
curl -X GET "http://localhost:8000/api/commits" \
  -H "Authorization: Bearer $API_TOKEN"
```

## Response Examples

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "database_status": "healthy"
}
```

### Commits Response
```json
{
  "commits": [
    {
      "id": "1",
      "commit_hash": "abc123def456",
      "repository_name": "commit-tracker-service",
      "author_name": "John Doe",
      "author_email": "john@example.com",
      "commit_message": "Initial commit",
      "commit_date": "2024-01-15T10:30:00Z",
      "source_type": "LOCAL",
      "branch_name": "main",
      "files_changed": ["src/main.py"],
      "lines_added": 100,
      "lines_deleted": 0,
      "status": "PROCESSED"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

### Analysis Response
```json
{
  "commit_id": "1",
  "analysis": {
    "security_analysis": {
      "risk_level": "LOW",
      "issues": [],
      "recommendations": []
    },
    "quality_analysis": {
      "quality_score": 95,
      "issues": [],
      "complexity": "LOW"
    },
    "summary": {
      "total_files": 1,
      "languages": ["Python"],
      "overall_impact": "MINOR"
    }
  },
  "processing_time": 0.123,
  "timestamp": 1705312200.0
}
```

## Error Handling

### Common Error Responses
```json
{
  "error": "Commit not found",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req-123"
}
```

### Authentication Error
```json
{
  "detail": "Not authenticated"
}
```

## Useful Shell Scripts

### 1. Quick Health Check
```bash
#!/bin/bash
curl -s "http://localhost:8000/health" | jq '.'
```

### 2. Get Recent Commits
```bash
#!/bin/bash
curl -s "http://localhost:8003/api/commits?limit=5" | jq '.commits[] | {hash: .commit_hash, message: .commit_message, author: .author_name}'
```

### 3. Search Commits
```bash
#!/bin/bash
SEARCH_TERM="$1"
curl -s "http://localhost:8003/api/commits/search?q=$SEARCH_TERM&limit=10" | jq '.results[] | {hash: .commit_hash, message: .commit_message}'
```

## Tips for CLI Usage

1. **Use `jq` for JSON formatting**: Install `jq` to pretty-print JSON responses
2. **Store tokens**: Save your access token in an environment variable
3. **Use aliases**: Create shell aliases for common commands
4. **Check status codes**: Use `-w "%{http_code}"` to see HTTP status codes
5. **Verbose output**: Use `-v` flag for detailed request/response information

## Troubleshooting

### Server Not Running
```bash
# Check if server is running
curl -s http://localhost:8003/health || echo "Server not running"

# Start server
PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Authentication Issues
```bash
# Check if token is valid
curl -X GET "http://localhost:8003/api/commits" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -w "%{http_code}"
```

### Database Connection Issues
```bash
# Check database health
curl -s "http://localhost:8003/health" | jq '.database_status'
```
