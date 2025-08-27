# API Test Data Files

This directory contains JSON files for testing the Commit Tracker Service API endpoints.

## Files Overview

### 1. `auth_token.json`
- **Purpose**: Authentication token request
- **Endpoint**: `POST /api/auth/token`
- **Usage**: Get JWT access token for authenticated endpoints

### 2. `create_commit.json`
- **Purpose**: Create a new commit record
- **Endpoint**: `POST /api/commits`
- **Usage**: Add a new commit to the database

### 3. `track_webhook_commit.json`
- **Purpose**: Track commits from GitHub webhook
- **Endpoint**: `POST /api/commits/webhook`
- **Usage**: Process GitHub webhook events

### 4. `track_local_commit.json`
- **Purpose**: Track commits from local git repository
- **Endpoint**: `POST /api/commits/local`
- **Usage**: Process local git commits

## How to Use

### Method 1: Using curl with JSON files

```bash
# 1. Get authentication token
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# 2. Create a commit (using JSON file)
curl -X POST "http://localhost:8000/api/commits" \
  -H "Content-Type: application/json" \
  -d @create_commit.json

# 3. Track webhook commit (with authentication)
curl -X POST "http://localhost:8000/api/commits/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d @track_webhook_commit.json

# 4. Track local commit (with authentication)
curl -X POST "http://localhost:8000/api/commits/local" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d @track_local_commit.json
```

### Method 2: Using the Python test script

```bash
# Run the comprehensive test script
python test_api_with_json.py
```

### Method 3: Manual curl commands

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Get commits (paginated)
curl -X GET "http://localhost:8000/api/commits?page=1&limit=10"

# Search commits (requires authentication)
curl -X GET "http://localhost:8000/api/commits/search?q=authentication&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get git status
curl -X GET "http://localhost:8000/api/git/status"
```

## File Structure

Each JSON file contains:
- `description`: What the file is for
- `curl_command`: Example curl command using the file
- `request_data`: The actual data to send in the request
- `expected_response`: Expected response format (for reference)

## Authentication

Most endpoints require authentication. Follow these steps:

1. **Get token**: Use `auth_token.json` to get an access token
2. **Use token**: Include the token in the `Authorization` header:
   ```
   Authorization: Bearer YOUR_TOKEN_HERE
   ```

## Troubleshooting

1. **Server not running**: Make sure the server is running on port 8000
2. **Authentication failed**: Check username/password in `auth_token.json`
3. **File not found**: Ensure you're in the correct directory when running curl
4. **Permission denied**: Make sure the JSON files are readable

## Quick Start

```bash
# 1. Start the server
PYTHONPATH=. python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# 2. In another terminal, run the test script
python test_api_with_json.py
```
