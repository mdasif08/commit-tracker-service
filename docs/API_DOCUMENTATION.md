# Commit Tracker Service - Complete API Documentation

## 📋 Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [Server Information](#server-information)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Testing Guide](#testing-guide)
6. [JSON Data Files](#json-data-files)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- Git repository with commits
- Required dependencies (see `requirements.txt`)

### Installation & Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd commit-tracker-service

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your configuration

# Start the server
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

---

## 🖥️ Server Information

- **Base URL**: `http://localhost:8001`
- **API Documentation**: `http://localhost:8001/docs` (Swagger UI)
- **Health Check**: `http://localhost:8001/health`
- **Alternative Port**: `http://localhost:8000` (if configured)

---

## 🔐 Authentication

Most endpoints require Bearer token authentication.

### Get Access Token
```bash
curl -X POST "http://localhost:8001/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token
```bash
# Add to all authenticated requests
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -X GET "http://localhost:8001/api/commits"
```

---

## 📡 API Endpoints

### 1. Health Check
```bash
GET /health
```
**Purpose**: Check service health and status  
**Authentication**: Not required  
**Response**: Service health information

### 2. Root Endpoint
```bash
GET /
```
**Purpose**: Get service information  
**Authentication**: Not required  
**Response**: Service details and version

### 3. Git Status
```bash
GET /api/git/status
```
**Purpose**: Get current git repository status  
**Authentication**: Not required  
**Response**: Repository information

### 4. Get Commits (Paginated)
```bash
GET /api/commits?page=1&limit=20
```
**Purpose**: Retrieve paginated list of commits  
**Authentication**: Optional  
**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `repository`: Filter by repository
- `author`: Filter by author
- `status`: Filter by status

### 5. Create Commit
```bash
POST /api/commits
```
**Purpose**: Create a new commit record  
**Authentication**: Required (Bearer token)  
**Content-Type**: `application/json`  
**Body**: Commit data (see JSON examples below)

### 6. Search Commits
```bash
GET /api/commits/search?q=search_term&limit=20
```
**Purpose**: Search commits using full-text search  
**Authentication**: Required (Bearer token)  
**Query Parameters**:
- `q`: Search query (required)
- `limit`: Maximum results (default: 20)
- `repository`: Filter by repository
- `author`: Filter by author

### 7. Webhook Commit
```bash
POST /api/commits/webhook
```
**Purpose**: Process GitHub webhook push events  
**Authentication**: Required (Bearer token)  
**Content-Type**: `application/json`  
**Headers**: 
- `X-GitHub-Event: push`
- `X-Hub-Signature-256: sha256=...`

### 8. Local Commit
```bash
POST /api/commits/local
```
**Purpose**: Track commits from local git repository  
**Authentication**: Required (Bearer token)  
**Content-Type**: `application/json`  
**Body**: Local commit data

---

## 🧪 Testing Guide

### Quick Test
```bash
# Test health endpoint
curl -X GET "http://localhost:8001/health"

# Test authentication
curl -X POST "http://localhost:8001/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### Comprehensive Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_curl_endpoints.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Using JSON Files for Testing
The service includes JSON files in the `data/` directory for easy API testing:

```bash
# Create commit using JSON file
curl -X POST "http://localhost:8001/api/commits" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @data/create_commit.json

# Test webhook with JSON
curl -X POST "http://localhost:8001/api/commits/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @data/webhook_commit.json

# Test local commit with JSON
curl -X POST "http://localhost:8001/api/commits/local" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @data/local_commit.json
```

---

## 📁 JSON Data Files

### Available Files in `data/` Directory

#### **For Testing (Simple Format)**
- `create_commit.json` - Create commit endpoint
- `webhook_commit.json` - Webhook endpoint  
- `local_commit.json` - Local commit endpoint

#### **For Documentation (Comprehensive Format)**
- `authentication_request.json` - Complete auth documentation
- `commit_create_request.json` - Create commit API docs
- `webhook_payload.json` - Webhook API docs
- `local_commit_request.json` - Local commit API docs
- `commit_search_request.json` - Search API docs
- `commit_list_request.json` - List commits API docs

### JSON File Structure Examples

#### Create Commit
```json
{
  "commit_hash": "84cb98d0b530536e0dd96271f7e7ed1909c24eeb",
  "repository_name": "commit-tracker-service",
  "author_name": "mdasif08",
  "author_email": "mohammadasif24680@gmail.com",
  "commit_message": "Clean up test files - automatic sync working",
  "commit_date": "2025-08-26T15:56:43+05:30",
  "source_type": "LOCAL",
  "branch_name": "main",
  "files_changed": ["scripts/auto_sync_commit.py", "src/database.py"],
  "lines_added": 139,
  "lines_deleted": 14,
  "parent_commits": ["754fb66"],
  "status": "PROCESSED"
}
```

#### Webhook Payload
```json
{
  "event_type": "push",
  "repository": {
    "full_name": "mdasif08/True_Microservice",
    "name": "True_Microservice"
  },
  "ref": "refs/heads/main",
  "before": "754fb66",
  "after": "84cb98d0b530536e0dd96271f7e7ed1909c24eeb",
  "commits": [...]
}
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8001

# Kill the process or use different port
python -m uvicorn src.main:app --port 8002
```

#### 2. Authentication Errors
- Ensure username/password are correct
- Check if token is expired
- Verify Bearer token format

#### 3. JSON Parsing Errors
- Validate JSON syntax
- Check required fields
- Ensure proper Content-Type header

#### 4. Database Connection Issues
- Verify database configuration in `.env`
- Check if database service is running
- Review database logs

### Test Results Summary

**Current Status**: ✅ All endpoints working  
**Last Test**: August 27, 2025  
**Results**: 9/9 tests passing

#### Working Endpoints
- ✅ Health Check
- ✅ Root Endpoint  
- ✅ Git Status
- ✅ Get Commits (Paginated)
- ✅ Authentication
- ✅ Create Commit with JSON
- ✅ Search Commits with Auth
- ✅ Webhook Commit with JSON
- ✅ Local Commit with JSON

---

## 📚 Additional Resources

- **Source Code**: `src/` directory
- **Tests**: `tests/` directory
- **Configuration**: `config/` directory
- **Docker**: `docker-compose.yml` and `Dockerfile`
- **Environment**: `env.example` and `.env`

---

## 🤝 Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Run quality checks: `python fix_quality.py`

---

*Last Updated: August 27, 2025*
