#!/usr/bin/env python3
"""
Simple mock server for testing curl endpoints
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone
import json

app = FastAPI(title="Commit Tracker Service Mock", version="1.0.0")

# Mock data
MOCK_TOKEN = "mock-access-token-12345"
MOCK_COMMITS = [
    {
        "id": "1",
        "commit_hash": "abc123",
        "author": "test@example.com",
        "message": "Initial commit",
        "repository": "test-repo",
        "commit_date": "2024-01-01T00:00:00Z"
    },
    {
        "id": "2", 
        "commit_hash": "def456",
        "author": "test@example.com",
        "message": "Add authentication",
        "repository": "test-repo",
        "commit_date": "2024-01-02T00:00:00Z"
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "1.0.0",
        "database_status": "healthy"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Commit Tracker Service",
        "version": "1.0.0",
        "status": "running",
        "uptime": 123.45
    }

@app.get("/api/git/status")
async def get_git_status():
    """Git status endpoint"""
    return {
        "repository_name": "test-repo",
        "current_branch": "main",
        "uncommitted_changes": []
    }

@app.get("/api/commits")
async def get_commits(page: int = 1, limit: int = 20):
    """Get commits endpoint"""
    return {
        "commits": MOCK_COMMITS[:limit],
        "total": len(MOCK_COMMITS),
        "page": page,
        "limit": limit
    }

@app.post("/api/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authentication endpoint"""
    if form_data.username == "admin" and form_data.password == "admin123":
        return {
            "access_token": MOCK_TOKEN,
            "token_type": "bearer"
        }
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.post("/api/commits")
async def create_commit(commit_data: dict):
    """Create commit endpoint"""
    return {
        "status": "success",
        "commit_id": "new-commit-123",
        "processing_time": 0.1
    }

@app.get("/api/commits/search")
async def search_commits(q: str, limit: int = 20):
    """Search commits endpoint"""
    # Mock search results
    results = [commit for commit in MOCK_COMMITS if q.lower() in commit["message"].lower()]
    return {
        "query": q,
        "results": results[:limit],
        "total": len(results)
    }

@app.post("/api/commits/webhook")
async def track_webhook_commit(webhook_data: dict):
    """Webhook commit endpoint"""
    return {
        "status": "success",
        "message": "Tracked 1 commits from webhook",
        "commits": [{"id": "webhook-commit-123"}]
    }

@app.post("/api/commits/local")
async def track_local_commit(local_data: dict):
    """Local commit endpoint"""
    return {
        "status": "success",
        "message": "Local commit tracked successfully",
        "commit": {"id": "local-commit-123"}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
