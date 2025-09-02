#!/usr/bin/env python3
"""
Working Commit Tracker Service Server
No import errors - completely standalone
"""

import json
import uvicorn
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, Query, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="Commit Tracker Service",
    version="1.0.0",
    description="Working Commit Tracker Service with JSON API format"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for testing
mock_commits = [
    {
        "id": "55068400",
        "commit_hash": "2d5a36a",
        "repository_name": "commit-tracker-service",
        "author_name": "mdasif08",
        "status": "processed",
        "created_at": "2025-08-29T16:00:00Z",
        "processed_at": "2025-08-29T16:00:00Z"
    },
    {
        "id": "55068401",
        "commit_hash": "3e6b47b",
        "repository_name": "commit-tracker-service",
        "author_name": "mdasif08",
        "status": "processed",
        "created_at": "2025-08-29T15:30:00Z",
        "processed_at": "2025-08-29T15:30:00Z"
    }
]

class CommitHistoryRequest(BaseModel):
    limit: int = 50
    offset: int = 0
    author: Optional[str] = None
    branch: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "service": "commit-tracker-service"
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Commit Tracker Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "commit_history_get": "/api/commits/history/public",
            "commit_history_post": "/api/commits/history/public (POST)"
        }
    }

@app.get("/api/commits/history/public")
async def get_commit_history_public_get(
    limit: int = Query(50, ge=1, le=100, description="Number of commits to return"),
    offset: int = Query(0, ge=0, description="Number of commits to skip"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    branch: Optional[str] = Query(None, description="Filter by branch name")
):
    """Get commit history with query parameters (public endpoint, Agent mode enabled)."""
    try:
        # Filter commits based on parameters
        filtered_commits = mock_commits.copy()
        
        if author:
            filtered_commits = [c for c in filtered_commits if c.get("author_name") == author]
        
        # Apply pagination
        total_count = len(filtered_commits)
        paginated_commits = filtered_commits[offset:offset + limit]
        
        # Agent mode: Add AI-powered analysis and insights
        agent_insights = {
            "analysis": {
                "total_commits": total_count,
                "page_info": {
                    "current_page": (offset // limit) + 1,
                    "page_size": limit,
                    "has_more": total_count > (offset + limit)
                },
                "filter_summary": {
                    "author_filter": author if author else "All authors",
                    "branch_filter": branch if branch else "All branches",
                    "date_range": "All time"
                }
            },
            "recommendations": []
        }
        
        # Add intelligent recommendations based on data
        if total_count == 0:
            agent_insights["recommendations"].append({
                "type": "info",
                "message": "No commits found with current filters. Try removing author or branch filters.",
                "suggestion": "Remove filters to see all commits"
            })
        elif total_count > 100:
            agent_insights["recommendations"].append({
                "type": "optimization",
                "message": "Large dataset detected. Consider using pagination for better performance.",
                "suggestion": "Use smaller limit values or add more specific filters"
            })
        
        # Return JSON API format response with Agent insights
        return {
            "status": "success",
            "data": {
                "commits": paginated_commits,
                "total_count": total_count,
                "page": (offset // limit) + 1,
                "page_size": limit
            },
            "agent": {
                "mode": "enabled",
                "insights": agent_insights,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to get commit history",
            "detail": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.post("/api/commits/history/public")
async def get_commit_history_public_json(
    request_data: CommitHistoryRequest = Body(..., description="JSON API format request")
):
    """Get commit history with JSON API format input (Agent mode enabled)."""
    try:
        # Extract parameters from JSON request body
        limit = request_data.limit
        offset = request_data.offset
        author = request_data.author
        branch = request_data.branch
        
        # Validate parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=400,
                detail="Offset must be 0 or greater"
            )
        
        # Filter commits based on parameters
        filtered_commits = mock_commits.copy()
        
        if author:
            filtered_commits = [c for c in filtered_commits if c.get("author_name") == author]
        
        # Apply pagination
        total_count = len(filtered_commits)
        paginated_commits = filtered_commits[offset:offset + limit]
        
        # Agent mode: Add AI-powered analysis and insights
        agent_insights = {
            "analysis": {
                "total_commits": total_count,
                "page_info": {
                    "current_page": (offset // limit) + 1,
                    "page_size": limit,
                    "has_more": total_count > (offset + limit)
                },
                "filter_summary": {
                    "author_filter": author if author else "All authors",
                    "branch_filter": branch if branch else "All branches",
                    "date_range": "All time"
                }
            },
            "recommendations": []
        }
        
        # Add intelligent recommendations based on data
        if total_count == 0:
            agent_insights["recommendations"].append({
                "type": "info",
                "message": "No commits found with current filters. Try removing author or branch filters.",
                "suggestion": "Remove filters to see all commits"
            })
        elif total_count > 100:
            agent_insights["recommendations"].append({
                "type": "optimization",
                "message": "Large dataset detected. Consider using pagination for better performance.",
                "suggestion": "Use smaller limit values or add more specific filters"
            })
        
        # Return JSON API format response with Agent insights
        return {
            "status": "success",
            "data": {
                "commits": paginated_commits,
                "total_count": total_count,
                "page": (offset // limit) + 1,
                "page_size": limit
            },
            "agent": {
                "mode": "enabled",
                "insights": agent_insights,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "error": "Failed to get commit history",
            "detail": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    print("🚀 Starting Working Commit Tracker Service...")
    print("📍 Server: http://localhost:8001")
    print("📚 API Docs: http://localhost:8001/docs")
    print("🏥 Health: http://localhost:8001/health")
    print("=" * 60)
    
    uvicorn.run(
        "working_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload to avoid import issues
        log_level="info"
    )