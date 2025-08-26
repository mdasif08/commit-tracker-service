import time
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    OAuth2PasswordRequestForm,
)
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime, timezone, timedelta
import asyncio
import json
from typing import Optional

from .config import settings
from .models import (
    WebhookPayload,
    LocalCommitData,
    CommitHistoryResponse,
    CommitMetrics,
    HealthCheckResponse,
    ErrorResponse,
    Token,
    User,
)
from .services.commit_service import commit_service
from .services.auth_service import auth_service
from .database import get_db_service, close_db_service
from .utils.git_utils import git_utils
from .utils.pattern_analyzer import pattern_analyzer
import hashlib

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency")
COMMIT_COUNT = Counter(
    "commit_events_total", "Total commit events", ["source_type", "status"]
)

# Startup time for uptime calculation
STARTUP_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Commit Tracker Service", version=settings.APP_VERSION)

    # Initialize database service
    try:
        await get_db_service()
        logger.info("Database service initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database service", error=str(e))
        raise

    yield

    # Cleanup database connections gracefully
    try:
        await close_db_service()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
    except asyncio.CancelledError:
        # Handle graceful shutdown
        logger.info("Application shutdown requested")

    logger.info("Shutting down Commit Tracker Service")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Commit Tracker Service - Independent Microservice",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # Allow all hosts for testing
)


# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics."""
    start_time = time.time()

    response = await call_next(request)

    # Record metrics
    duration = time.time() - start_time
    REQUEST_LATENCY.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.url.path, status=response.status_code
    ).inc()

    return response


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    try:
        db_service = await get_db_service()
        db_status = "healthy" if await db_service.health_check() else "unhealthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "error"

    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.APP_VERSION,
        database_status=db_status,
    )


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.ENABLE_METRICS:
        raise HTTPException(status_code=404, detail="Metrics disabled")

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Authentication dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    """Dependency to get current authenticated user."""
    return auth_service.get_current_user(credentials)


# Authentication endpoint
@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get access token."""
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Webhook commit tracking endpoint
@app.post("/api/commits/webhook")
async def track_webhook_commit(
    webhook_payload: WebhookPayload, current_user: User = Depends(get_current_user)
):
    """Track commits from GitHub webhook service."""
    try:
        logger.info(
            "Received webhook commit data",
            event_type=webhook_payload.event_type,
            repository=webhook_payload.repository.get("full_name", "unknown"),
            user=current_user.username,
        )

        responses = await commit_service.track_webhook_commit(webhook_payload)

        # Record metrics
        COMMIT_COUNT.labels(source_type="webhook", status="success").inc()

        return {
            "status": "success",
            "message": f"Tracked {len(responses)} commits from webhook",
            "commits": responses,
        }

    except Exception as e:
        logger.error("Failed to track webhook commits", error=str(e))
        COMMIT_COUNT.labels(source_type="webhook", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


# Local commit tracking endpoint
@app.post("/api/commits/local")
async def track_local_commit(
    local_commit: LocalCommitData, current_user: User = Depends(get_current_user)
):
    """Track commits from local git repository."""
    try:
        logger.info(
            "Received local commit data",
            commit_hash=local_commit.commit_hash[:8],
            repository_path=local_commit.repository_path,
            user=current_user.username,
        )

        response = await commit_service.track_local_commit(local_commit)

        # Record metrics
        COMMIT_COUNT.labels(source_type="local", status="success").inc()

        return {
            "status": "success",
            "message": "Local commit tracked successfully",
            "commit": response,
        }

    except Exception as e:
        logger.error("Failed to track local commit", error=str(e))
        COMMIT_COUNT.labels(source_type="local", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


# Get commit history endpoint
@app.get("/api/commits/{repository_name}", response_model=CommitHistoryResponse)
async def get_commit_history(
    repository_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
):
    """Get commit history for a repository."""
    try:
        return await commit_service.get_commit_history(repository_name, page, page_size)
    except Exception as e:
        logger.error(
            "Failed to get commit history", repository=repository_name, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# Get commit metrics endpoint
@app.get("/api/commits/{repository_name}/metrics", response_model=CommitMetrics)
async def get_commit_metrics(
    repository_name: str, current_user: User = Depends(get_current_user)
):
    """Get commit metrics and statistics for a repository."""
    try:
        return await commit_service.get_commit_metrics(repository_name)
    except Exception as e:
        logger.error(
            "Failed to get commit metrics", repository=repository_name, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# Git utilities endpoints
@app.get("/api/git/status")
async def get_git_status():
    """Get current git repository status."""
    try:
        return {
            "repository_name": git_utils.get_repository_name(),
            "current_branch": git_utils.get_current_branch(),
            "uncommitted_changes": git_utils.get_uncommitted_changes(),
        }
    except Exception as e:
        logger.error("Failed to get git status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/commits/recent")
async def get_recent_commits(count: int = Query(10, ge=1, le=50)):
    """Get recent commits from local repository."""
    try:
        return {"commits": git_utils.get_recent_commits(count)}
    except Exception as e:
        logger.error("Failed to get recent commits", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/commits/{commit_hash}")
async def get_commit_info(commit_hash: str):
    """Get detailed information for a specific commit."""
    try:
        commit_info = git_utils.get_commit_info(commit_hash)
        if not commit_info:
            raise HTTPException(status_code=404, detail="Commit not found")
        return commit_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get commit info", commit_hash=commit_hash[:8], error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# NEW: Production-ready API endpoints with diff support
@app.post("/api/commits")
async def create_commit(commit_data: dict):
    """Create a new commit record with diff content."""
    start_time = time.time()
    
    try:
        # Get diff content from git
        diff_data = git_utils.get_commit_diff(commit_data['commit_hash'])
        
        # Generate diff hash for deduplication
        diff_hash = hashlib.sha256(diff_data['diff_content'].encode()).hexdigest()
        
        # Combine commit data with diff
        full_commit_data = {
            **commit_data,
            'diff_content': diff_data['diff_content'],
            'file_diffs': diff_data['file_diffs'],
            'diff_hash': diff_hash
        }
        
        # Store in PostgreSQL database
        db_service = await get_db_service()
        commit_id = await db_service.store_commit_with_diff(full_commit_data)
        
        processing_time = time.time() - start_time
        logger.info("Commit created successfully", 
                   commit_id=commit_id, 
                   processing_time=processing_time)
        
        return {
            "status": "success", 
            "commit_id": commit_id,
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error("Failed to create commit", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits")
async def get_commits(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    repository: Optional[str] = Query(None, description="Filter by repository"),
    author: Optional[str] = Query(None, description="Filter by author"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get commits with pagination and filtering."""
    try:
        db_service = await get_db_service()
        commits = await db_service.get_commits_paginated(
            page=page, 
            limit=limit, 
            repository=repository,
            author=author,
            status=status
        )
        return commits
    except Exception as e:
        logger.error("Failed to get commits", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/{commit_id}")
async def get_commit(commit_id: str):
    """Get commit metadata (fast)."""
    try:
        db_service = await get_db_service()
        commit = await db_service.get_commit_metadata(commit_id)
        if not commit:
            raise HTTPException(status_code=404, detail="Commit not found")
        return commit
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get commit", commit_id=commit_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/{commit_id}/diff")
async def get_commit_diff(commit_id: str):
    """Get commit with diff content (detailed view)."""
    try:
        db_service = await get_db_service()
        commit = await db_service.get_commit_with_diff(commit_id)
        if not commit:
            raise HTTPException(status_code=404, detail="Commit not found")
        return commit
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get commit diff", commit_id=commit_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/{commit_id}/analysis")
async def analyze_commit(commit_id: str):
    """Advanced commit analysis (production ready)."""
    start_time = time.time()
    
    try:
        db_service = await get_db_service()
        commit = await db_service.get_commit_with_diff(commit_id)
        if not commit:
            raise HTTPException(status_code=404, detail="Commit not found")
        
        # Perform comprehensive analysis
        analysis = {
            "security_analysis": pattern_analyzer.analyze_commit_security(
                commit['diff_content'] or '', 
                commit['file_diffs'] or {}
            ),
            "quality_analysis": pattern_analyzer.analyze_code_quality(
                commit['diff_content'] or '', 
                commit['file_diffs'] or {}
            ),
            "summary": pattern_analyzer.generate_summary(commit)
        }
        
        processing_time = time.time() - start_time
        logger.info("Commit analysis completed", 
                   commit_id=commit_id, 
                   processing_time=processing_time)
        
        return {
            "commit_id": commit_id,
            "analysis": analysis,
            "processing_time": processing_time,
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to analyze commit", commit_id=commit_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/search")
async def search_commits(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """Full-text search across commits."""
    try:
        db_service = await get_db_service()
        results = await db_service.search_commits_fulltext(q, limit)
        return {
            "query": q,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error("Search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# NEW: File-level API endpoints
@app.get("/api/commits/{commit_id}/files")
async def get_commit_files(commit_id: str):
    """Get individual file changes for a commit."""
    try:
        db_service = await get_db_service()
        files = await db_service.get_commit_files(commit_id)
        if not files:
            return {"commit_id": commit_id, "files": []}
        return {
            "commit_id": commit_id,
            "files": files,
            "total_files": len(files)
        }
    except Exception as e:
        logger.error("Failed to get commit files", commit_id=commit_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commits/{commit_id}/summary")
async def get_commit_summary(commit_id: str):
    """Get commit summary with file statistics."""
    try:
        db_service = await get_db_service()
        summary = await db_service.get_commit_summary(commit_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Commit not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get commit summary", commit_id=commit_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{file_id}")
async def get_file_analysis(file_id: str):
    """Get detailed analysis for a specific file change."""
    try:
        db_service = await get_db_service()
        file_analysis = await db_service.get_file_analysis(file_id)
        if not file_analysis:
            raise HTTPException(status_code=404, detail="File not found")
        return file_analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file analysis", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        error=exc.detail,
        timestamp=datetime.now(timezone.utc),
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=json.loads(error_response.model_dump_json()),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unhandled exception", error=str(exc), exc_info=True)

    error_response = ErrorResponse(
        error="Internal server error",
        detail=str(exc) if settings.DEBUG else None,
        timestamp=datetime.now(timezone.utc),
        request_id=request.headers.get("X-Request-ID"),
    )

    return JSONResponse(
        status_code=500, content=json.loads(error_response.model_dump_json())
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "uptime": time.time() - STARTUP_TIME,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
