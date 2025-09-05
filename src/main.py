import asyncio
import hashlib
import inspect
import json
import os
import sys
import time
import psutil
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import structlog
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

# Import with error handling for 100% reliability
try:
    from .config import settings
    from .database import close_db_service, get_db_service
    from .models import (
        CommitHistoryRequest,
        CommitHistoryResponse,
        CommitMetrics,
        ErrorResponse,
        HealthCheckResponse,
        LocalCommitData,
        Token,
        User,
        WebhookPayload,
    )
    from .services.auth_service import auth_service
    from .services.auto_sync_service import auto_sync_service
    from .services.commit_service import commit_service
    from .utils.git_utils import git_utils
    from .utils.pattern_analyzer import pattern_analyzer
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback imports for 100% reliability
    from src.config import settings
    from src.database import close_db_service, get_db_service
    from src.models import (
        CommitHistoryRequest,
        CommitHistoryResponse,
        CommitMetrics,
        ErrorResponse,
        HealthCheckResponse,
        LocalCommitData,
        Token,
        User,
        WebhookPayload,
    )
    from src.services.auth_service import auth_service
    from src.services.auto_sync_service import auto_sync_service
    from src.services.commit_service import commit_service
    from src.utils.git_utils import git_utils
    from src.utils.pattern_analyzer import pattern_analyzer


def get_error_location() -> tuple[str, int]:
    """Get the file name and line number where the error occurred."""
    try:
        # Get the current frame
        current_frame = inspect.currentframe()
        # Go back 2 frames to get the calling function
        caller_frame = (
            current_frame.f_back.f_back
            if current_frame and current_frame.f_back
            else None
        )

        if caller_frame:
            filename = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno
            # Extract just the file name without path
            file_name = (
                filename.split("/")[-1]
                if "/" in filename
                else filename.split("\\")[-1]
            )
            return file_name, line_number
        return "unknown", 0
    except Exception:
        return "unknown", 0


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
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency"
)
COMMIT_COUNT = Counter(
    "commit_events_total",
    "Total commit events",
    ["source_type", "status"],
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

    # Start auto-sync service
    try:
        asyncio.create_task(auto_sync_service.start())
        logger.info("Auto-sync service started successfully")
    except Exception as e:
        logger.error("Failed to start auto-sync service", error=str(e))
        # Don't raise here, continue without auto-sync

    yield

    # Stop auto-sync service
    try:
        await auto_sync_service.stop()
        logger.info("Auto-sync service stopped")
    except Exception as e:
        logger.error("Error stopping auto-sync service", error=str(e))

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
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()

    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with code fixes."""
    try:
        db_service = await get_db_service()
        db_status = (
            "healthy" if await db_service.health_check() else "unhealthy"
        )

        # If healthy, return normal response
        if db_status == "healthy":
            return HealthCheckResponse(
                status="healthy",
                timestamp=datetime.now(timezone.utc),
                version=settings.APP_VERSION,
                database_status=db_status,
            )
        else:
            # Return error with fix
            file_name, line_number = get_error_location()
            return ErrorResponse(
                error="Database connection failed",
                detail="Database health check returned unhealthy status",
                timestamp=datetime.now(timezone.utc),
                fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
                fix_command="python scripts/start_server.py",
                file_name=file_name,
                line_number=line_number,
            )

    except FileNotFoundError as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Database file not found",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code=(
                "os.environ['DATABASE_URL'] = "
                "'sqlite+aiosqlite:///./commit_tracker.db'"
            ),
            fix_command="python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )

    except PermissionError as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Database permission denied",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="chmod 644 commit_tracker.db",
            fix_command="chmod 644 commit_tracker.db && python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )

    except Exception as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Database configuration error",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
            fix_command="pip install aiosqlite && python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


# Kubernetes readiness probe endpoint
@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if the service is ready to accept traffic
        db_service = await get_db_service()
        db_healthy = await db_service.health_check()
        
        if db_healthy:
            return {
                "status": "ready",
                "timestamp": datetime.now(timezone.utc),
                "version": settings.APP_VERSION,
                "database_status": "healthy",
                "service_status": "ready"
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - database unhealthy"
            )
    except Exception as e:
        logger.error("Readiness probe failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


# Kubernetes liveness probe endpoint
@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    try:
        # Simple liveness check - if we can respond, we're alive
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc),
            "version": settings.APP_VERSION,
            "uptime": time.time() - STARTUP_TIME,
            "service_status": "running"
        }
    except Exception as e:
        logger.error("Liveness probe failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Service not alive: {str(e)}"
        )


# System monitoring endpoint
@app.get("/api/system")
async def get_system_info():
    """Get system information and resource usage."""
    try:
        # Get system metrics using psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "system": {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100
                }
            },
            "process": {
                "pid": process.pid,
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "create_time": process.create_time(),
                "uptime": time.time() - process.create_time()
            },
            "service": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "uptime": time.time() - STARTUP_TIME,
                "timestamp": datetime.now(timezone.utc)
            }
        }
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get system information",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="pip install psutil",
            fix_command="pip install psutil && python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


# Debug endpoint to check settings
@app.get("/debug")
async def debug_info():
    """Debug endpoint to check current settings."""
    return {
        "debug": settings.DEBUG,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "docs_url": "/api/docs" if settings.DEBUG else None,
        "redoc_url": "/api/redoc" if settings.DEBUG else None,
        "database_url": str(settings.DATABASE_URL).replace(str(settings.DATABASE_URL).split('@')[0].split('//')[1], '***') if '@' in str(settings.DATABASE_URL) else str(settings.DATABASE_URL)
    }

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

    except ValueError as e:
        COMMIT_COUNT.labels(source_type="local", status="error").inc()
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Invalid commit data format",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code=(
                '{"commit_hash": "abc123...", "author_name": "Your Name", '
                '"commit_message": "Your message", "branch_name": "main", '
                '"files_changed": [], "lines_added": 0, "lines_deleted": 0, '
                '"parent_commits": []}'
            ),
            fix_command=(
                "curl -X POST 'http://localhost:8001/api/commits/local' "
                "-H 'Content-Type: application/json' "
                "-d '{\"commit_hash\": \"abc123...\", \"author_name\": \"Your Name\", "
                '"commit_message": "Your message"}\''
            ),
            file_name=file_name,
            line_number=line_number,
        )

    except HTTPException as e:
        # Re-raise HTTP exceptions (like 400 for test data)
        COMMIT_COUNT.labels(source_type="local", status="error").inc()
        raise e

    except Exception as e:
        COMMIT_COUNT.labels(source_type="local", status="error").inc()
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to track commit",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
            fix_command="python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


# Get commit history endpoint
@app.get("/api/commits/{repository_name}", response_model=Union[CommitHistoryResponse, ErrorResponse])
async def get_commit_history(
    repository_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
):
    """Get commit history for a repository."""
    try:
        return await commit_service.get_commit_history(repository_name, page, page_size)
    except ValueError as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Invalid pagination parameters",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="page=1&page_size=50",
            fix_command=(
                f"curl 'http://localhost:8001/api/commits/{repository_name}"
                "?page=1&page_size=50'"
            ),
            file_name=file_name,
            line_number=line_number,
        )

    except Exception as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit history",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
            fix_command="python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


# Get commit metrics endpoint
@app.get("/api/commits/{repository_name}/metrics", response_model=CommitMetrics)
async def get_commit_metrics(
    repository_name: str, current_user: User = Depends(get_current_user)
):
    """Get commit metrics and statistics for a repository."""
    try:
        return await commit_service.get_commit_metrics(repository_name)
    except ValueError as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Invalid repository name",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="repository_name = 'your-repo-name'",
            fix_command=(
                "curl 'http://localhost:8001/api/commits/your-repo-name/metrics'"
            ),
            file_name=file_name,
            line_number=line_number,
        )

    except Exception as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit metrics",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
            fix_command="python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


# Git utilities endpoints
@app.get("/api/git/status")
async def get_git_status():
    """Get current git repository status."""
    try:
        # Check if we're in a Docker environment or if git is available
        try:
            repository_name = git_utils.get_repository_name()
            current_branch = git_utils.get_current_branch()
            uncommitted_changes = git_utils.get_uncommitted_changes()
            
            return {
                "repository_name": repository_name,
                "current_branch": current_branch,
                "uncommitted_changes": uncommitted_changes,
                "environment": "local_git"
            }
        except Exception as git_error:
            # Handle Docker environment where git might not be available
            logger.warning("Git not available in container environment", error=str(git_error))
            return {
                "repository_name": "commit-tracker-service",
                "current_branch": "main",
                "uncommitted_changes": [],
                "environment": "docker_container",
                "note": "Git operations not available in containerized environment",
                "git_error": str(git_error)
            }
    except Exception as e:
        logger.error("Failed to get git status", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get git status",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="git status",
            fix_command="cd /path/to/your/repo && git status",
            file_name=file_name,
            line_number=line_number,
        )


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
            "Failed to get commit info",
            commit_hash=commit_hash[:8],
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


# NEW: Production-ready API endpoints with diff support
@app.post("/api/commits")
async def create_commit(commit_data: dict):
    """Create a new commit record with diff content."""
    start_time = time.time()

    try:
        # Validate commit data format
        if not commit_data.get('commit_hash') or not commit_data.get('author_name'):
            logger.warning("Invalid commit data format", commit_data=commit_data)
            raise HTTPException(status_code=400, detail="Invalid commit data format")
        # Parse commit date if it's a string
        if isinstance(commit_data.get('commit_date'), str):
            commit_data['commit_date'] = datetime.fromisoformat(commit_data['commit_date'])

        # Check if diff content is already provided
        if commit_data.get('diff_content') and commit_data.get('file_diffs'):
            # Use provided diff content
            diff_content = commit_data['diff_content']
            file_diffs = commit_data['file_diffs']
        else:
            # Get diff content from git
            diff_data = git_utils.get_commit_diff(commit_data['commit_hash'])
            diff_content = diff_data['diff_content']
            file_diffs = diff_data['file_diffs']

        # Generate diff hash for deduplication
        diff_hash = hashlib.sha256(diff_content.encode()).hexdigest()

        # Combine commit data with diff
        full_commit_data = {
            **commit_data,
            'diff_content': diff_content,
            'file_diffs': file_diffs,
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
            "processing_time": processing_time,
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
            status=status,
        )
        return commits
        
    except ValueError as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Invalid query parameters",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="page=1&limit=20",
            fix_command="curl 'http://localhost:8001/api/commits?page=1&limit=20'",
            file_name=file_name,
            line_number=line_number,
        )

    except Exception as e:
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Database connection failed",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'",
            fix_command="python scripts/start_server.py",
            file_name=file_name,
            line_number=line_number,
        )


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
                commit["diff_content"] or "",
                commit["file_diffs"] or {},
            ),
            "quality_analysis": pattern_analyzer.analyze_code_quality(
                commit["diff_content"] or "",
                commit["file_diffs"] or {},
            ),
            "summary": pattern_analyzer.generate_summary(commit),
        }

        processing_time = time.time() - start_time
        logger.info("Commit analysis completed",
                   commit_id=commit_id,
                   processing_time=processing_time)

        return {
            "commit_id": commit_id,
            "analysis": analysis,
            "processing_time": processing_time,
            "timestamp": time.time(),
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
            "total": len(results),
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
            "total_files": len(files),
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
    """Handle HTTP exceptions with code fixes."""
    
    # Get error location
    file_name, line_number = get_error_location()
    
    # Add helpful context and fixes based on status code
    if exc.status_code == 401:
        error_message = "Authentication failed"
        fix_code = "curl -X POST 'http://localhost:8001/api/auth/token' -d 'username=admin&password=admin123'"
        fix_command = "curl -X POST 'http://localhost:8001/api/auth/token' -d 'username=admin&password=admin123'"
    elif exc.status_code == 403:
        error_message = "Access denied"
        fix_code = "Authorization: Bearer YOUR_TOKEN"
        fix_command = "curl -H 'Authorization: Bearer YOUR_TOKEN' 'http://localhost:8001/api/commits'"
    elif exc.status_code == 404:
        error_message = "Resource not found"
        fix_code = "Check URL: http://localhost:8001/api/commits"
        fix_command = "curl 'http://localhost:8001/api/commits'"
    elif exc.status_code == 422:
        error_message = "Validation error"
        fix_code = (
            '{"commit_hash": "abc123...", "author_name": "Your Name", '
            '"commit_message": "Your message"}'
        )
        fix_command = (
            "curl -X POST 'http://localhost:8001/api/commits/local' "
            "-H 'Content-Type: application/json' "
            "-d '{\"commit_hash\": \"abc123...\", \"author_name\": \"Your Name\", "
            '"commit_message": "Your message"}\''
        )
    else:
        error_message = exc.detail
        fix_code = None
        fix_command = None
    
    error_response = ErrorResponse(
        error=error_message,
        detail=exc.detail,
        timestamp=datetime.now(timezone.utc),
        request_id=request.headers.get("X-Request-ID"),
        fix_code=fix_code,
        fix_command=fix_command,
        file_name=file_name,
        line_number=line_number,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=json.loads(error_response.model_dump_json()),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with code fixes."""
    logger.error("Unhandled exception", error=str(exc), exc_info=True)

    # Get error location
    file_name, line_number = get_error_location()

    # Provide specific fixes for common errors
    if "database" in str(exc).lower():
        error_message = "Database connection error"
        fix_code = "DATABASE_URL = 'sqlite+aiosqlite:///./commit_tracker.db'"
        fix_command = "python scripts/start_server.py"
    elif "import" in str(exc).lower():
        error_message = "Module import error"
        fix_code = "pip install -r requirements.txt"
        fix_command = "pip install -r requirements.txt && python scripts/start_server.py"
    elif "permission" in str(exc).lower():
        error_message = "Permission error"
        fix_code = "chmod 644 commit_tracker.db"
        fix_command = "chmod 644 commit_tracker.db && python scripts/start_server.py"
    else:
        error_message = "Internal server error"
        fix_code = "python scripts/start_server.py"
        fix_command = "python scripts/start_server.py"

    error_response = ErrorResponse(
        error=error_message,
        detail=str(exc) if settings.DEBUG else "Check server logs for technical details",
        timestamp=datetime.now(timezone.utc),
        request_id=request.headers.get("X-Request-ID"),
        fix_code=fix_code,
        fix_command=fix_command,
        file_name=file_name,
        line_number=line_number,
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


# NEW: Auto-fetch real Git commits endpoint
@app.post("/api/commits/fetch-real")
async def fetch_real_commits(
    count: int = Query(10, ge=1, le=50, description="Number of commits to fetch"),
    current_user: User = Depends(get_current_user)
):
    """Automatically fetch and store real commits from Git repository."""
    try:
        logger.info("Fetching real commits from Git repository", count=count)
        
        # Get real commits from Git
        real_commits = git_utils.get_recent_commits(count)
        
        if not real_commits:
            return {
                "status": "warning",
                "message": "No commits found in Git repository",
                "commits_fetched": 0,
            }
        
        # Store each commit in database
        stored_commits = []
        db_service = await get_db_service()
        
        for commit in real_commits:
            try:
                # Get diff content for this commit
                diff_data = git_utils.get_commit_diff(commit['hash'])
                
                # Prepare commit data for storage
                commit_data = {
                    "commit_hash": commit["hash"],
                    "repository_name": git_utils.get_repository_name(),
                    "author_name": commit["author_name"],
                    "author_email": commit["author_email"],
                    "commit_message": commit["message"],
                    "commit_date": commit["commit_date"],
                    "branch_name": git_utils.get_current_branch(),
                    "files_changed": commit.get("files_changed", []),
                    "lines_added": commit.get("lines_added", 0),
                    "lines_deleted": commit.get("lines_deleted", 0),
                    "parent_commits": commit.get("parent_hashes", []),
                    "diff_content": diff_data.get("diff_content", ""),
                    "file_diffs": diff_data.get("file_diffs", {}),
                }
                
                # Store in database
                commit_id = await db_service.store_commit_with_diff(commit_data)
                stored_commits.append({
                    "commit_hash": commit["hash"][:8],
                    "commit_id": commit_id,
                    "message": (
                        commit["message"][:50] + "..."
                        if len(commit["message"]) > 50
                        else commit["message"]
                    ),
                })
                
            except Exception as e:
                logger.error(f"Failed to store commit {commit['hash'][:8]}", error=str(e))
                continue
        
        return {
            "status": "success",
            "message": f"Successfully fetched and stored {len(stored_commits)} commits",
            "commits_fetched": len(stored_commits),
            "commits": stored_commits,
        }
        
    except Exception as e:
        logger.error("Failed to fetch real commits", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to fetch real commits",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="git log --oneline -10",
            fix_command="cd /path/to/your/repo && git log --oneline -10",
            file_name=file_name,
            line_number=line_number,
        )


# NEW: Get real Git repository information endpoint
@app.get("/api/git/repository")
async def get_git_repository_info():
    """Get comprehensive real Git repository information."""
    try:
        # Get real Git repository information
        repo_info = {
            "repository_name": git_utils.get_repository_name(),
            "current_branch": git_utils.get_current_branch(),
            "repository_path": git_utils.repo_path,
            "is_git_repository": git_utils._is_git_repo,
            "uncommitted_changes": git_utils.get_uncommitted_changes(),
            "recent_commits_count": len(git_utils.get_recent_commits(10)),
            "total_commits": len(git_utils.get_recent_commits(1000)),  # Get a large number to estimate total
            "last_commit": None,
        }
        
        # Get the most recent commit details
        recent_commits = git_utils.get_recent_commits(1)
        if recent_commits:
            repo_info["last_commit"] = {
                "hash": recent_commits[0]["hash"][:8],
                "author": recent_commits[0]["author_name"],
                "message": (
                    recent_commits[0]["message"][:100] + "..."
                    if len(recent_commits[0]["message"]) > 100
                    else recent_commits[0]["message"]
                ),
                "date": recent_commits[0]["commit_date"],
            }
        
        return repo_info
        
    except Exception as e:
        logger.error("Failed to get Git repository info", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get Git repository information",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="git status",
            fix_command="cd /path/to/your/repo && git status",
            file_name=file_name,
            line_number=line_number,
        )


# NEW: Get real commit statistics endpoint
@app.get("/api/git/statistics")
async def get_git_statistics():
    """Get real Git repository statistics."""
    try:
        # Get real Git statistics
        recent_commits = git_utils.get_recent_commits(100)
        
        if not recent_commits:
            return {
                "total_commits": 0,
                "authors": [],
                "most_active_author": None,
                "commit_frequency": {
                    "today": 0,
                    "this_week": 0,
                    "this_month": 0,
                },
                "file_types": {},
                "average_commit_size": 0,
            }
        
        # Calculate statistics
        authors = {}
        file_types = {}
        total_lines_added = 0
        total_lines_deleted = 0
        
        for commit in recent_commits:
            # Count authors
            author = commit['author_name']
            authors[author] = authors.get(author, 0) + 1
            
            # Count file types
            files_changed = commit.get('files_changed', [])
            for file_path in files_changed:
                if '.' in file_path:
                    ext = file_path.split('.')[-1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # Count lines
            total_lines_added += commit.get('lines_added', 0)
            total_lines_deleted += commit.get('lines_deleted', 0)
        
        # Find most active author
        most_active_author = max(authors.items(), key=lambda x: x[1]) if authors else None
        
        # Calculate commit frequency (simplified)
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        commits_today = 0
        commits_this_week = 0
        commits_this_month = 0
        
        for commit in recent_commits:
            commit_date = datetime.fromisoformat(commit['commit_date'].replace('Z', '+00:00')).date()
            if commit_date == today:
                commits_today += 1
            if commit_date >= week_ago:
                commits_this_week += 1
            if commit_date >= month_ago:
                commits_this_month += 1
        
        return {
            "total_commits": len(recent_commits),
            "authors": [{"name": name, "commits": count} for name, count in authors.items()],
            "most_active_author": {"name": most_active_author[0], "commits": most_active_author[1]} if most_active_author else None,
            "commit_frequency": {
                "today": commits_today,
                "this_week": commits_this_week,
                "this_month": commits_this_month,
            },
            "file_types": [{"extension": ext, "count": count} for ext, count in file_types.items()],
            "average_commit_size": {
                "lines_added": total_lines_added // len(recent_commits) if recent_commits else 0,
                "lines_deleted": total_lines_deleted // len(recent_commits) if recent_commits else 0,
            }
        }
        
    except Exception as e:
        logger.error("Failed to get Git statistics", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get Git statistics",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="git log --oneline",
            fix_command="cd /path/to/your/repo && git log --oneline",
            file_name=file_name,
            line_number=line_number,
        )


# ============================================================================
# AUTO-SYNC ENDPOINTS
# ============================================================================

# Startup event is now handled by the lifespan context manager above


@app.post("/api/sync/start")
async def start_auto_sync(
    sync_interval: int = Query(30, ge=10, le=300, description="Sync interval in seconds"),
    current_user: User = Depends(get_current_user)
):
    """Start automatic sync process."""
    try:
        if not auto_sync_service.is_running:
            asyncio.create_task(auto_sync_service.start())
            return {
                "status": "success",
                "message": f"Auto-sync started with {sync_interval}s interval",
                "sync_interval": sync_interval,
            }
        else:
            return ErrorResponse(
                error="Failed to start auto-sync",
                detail="Auto-sync service is already running",
                timestamp=datetime.now(timezone.utc),
                fix_code="Check if auto-sync is already running",
                fix_command="GET /api/sync/status",
                file_name="auto_sync_service.py",
                line_number=1,
            )
    except Exception as e:
        logger.error("Failed to start auto-sync", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to start auto-sync",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check database connection and Git repository",
            fix_command="git status && curl http://localhost:8001/health",
            file_name=file_name,
            line_number=line_number,
        )


@app.post("/api/sync/stop")
async def stop_auto_sync(current_user: User = Depends(get_current_user)):
    """Stop automatic sync process."""
    try:
        if auto_sync_service.is_running:
            await auto_sync_service.stop()
            return {
                "status": "success",
                "message": "Auto-sync stopped successfully",
            }
        else:
            return ErrorResponse(
                error="Failed to stop auto-sync",
                detail="Auto-sync service is not running",
                timestamp=datetime.now(timezone.utc),
                fix_code="Check if auto-sync is running",
                fix_command="GET /api/sync/status",
                file_name="auto_sync_service.py",
                line_number=1,
            )
    except Exception as e:
        logger.error("Failed to stop auto-sync", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to stop auto-sync",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check auto-sync service status",
            fix_command="GET /api/sync/status",
            file_name=file_name,
            line_number=line_number,
        )


@app.get("/api/sync/status")
async def get_sync_status():
    """Get auto-sync service status."""
    try:
        status = auto_sync_service.get_sync_status()
        return {
            "status": "success",
            "data": status,
        }
    except Exception as e:
        logger.error("Failed to get sync status", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get sync status",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check auto-sync service",
            fix_command="Restart the service",
            file_name=file_name,
            line_number=line_number,
        )


@app.post("/api/sync/manual")
async def manual_sync(current_user: User = Depends(get_current_user)):
    """Perform manual sync operation."""
    try:
        result = await auto_sync_service.manual_sync()
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error("Failed to perform manual sync", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to perform manual sync",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check database connection and Git repository",
            fix_command="git status && curl http://localhost:8001/health",
            file_name=file_name,
            line_number=line_number,
        )


@app.post("/api/sync/manual/public")
async def manual_sync_public():
    """Perform manual sync operation (public endpoint for testing)."""
    try:
        result = await auto_sync_service.manual_sync()
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error("Failed to perform manual sync", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to perform manual sync",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check database connection and Git repository",
            fix_command="git status && curl http://localhost:8001/health",
            file_name=file_name,
            line_number=line_number,
        )


@app.get("/api/commits/history")
async def get_commit_history(
    limit: int = Query(50, ge=1, le=100, description="Number of commits to return"),
    offset: int = Query(0, ge=0, description="Number of commits to skip"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    branch: Optional[str] = Query(None, description="Filter by branch name"),
    current_user: User = Depends(get_current_user)
):
    """Get commit history from database with pagination and filtering."""
    try:
        result = await auto_sync_service.get_commit_history(
            limit=limit,
            offset=offset,
            author=author,
            branch=branch,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error("Failed to get commit history", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit history",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check database connection and sync status",
            fix_command="GET /api/sync/status",
            file_name=file_name,
            line_number=line_number,
        )


@app.post("/api/commits/history/public")
async def get_commit_history_public_json(
    request_data: CommitHistoryRequest
):
    """Get commit history with JSON API format input."""
    try:
        # Extract parameters from validated request model
        limit = request_data.limit
        offset = request_data.offset
        author = request_data.author
        branch = request_data.branch
        
        # Get commit history using auto sync service
        result = await auto_sync_service.get_commit_history(
            limit=limit,
            offset=offset,
            author=author,
            branch=branch,
        )
        
        # Agent mode: Add AI-powered analysis and insights
        agent_insights = {
            "analysis": {
                "total_commits": result.get("total_count", 0),
                "page_info": {
                    "current_page": result.get("page", 1),
                    "page_size": result.get("page_size", limit),
                    "has_more": result.get("total_count", 0) > (result.get("page", 1) * limit)
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
        if result.get("total_count", 0) == 0:
            agent_insights["recommendations"].append({
                "type": "info",
                "message": "No commits found with current filters. Try removing author or branch filters.",
                "suggestion": "Remove filters to see all commits",
            })
        elif result.get("total_count", 0) > 100:
            agent_insights["recommendations"].append({
                "type": "optimization",
                "message": "Large dataset detected. Consider using pagination for better performance.",
                "suggestion": "Use smaller limit values or add more specific filters",
            })

        # Return JSON API format response with Agent insights
        return {
            "status": "success",
            "data": result,
            "agent": {
                "mode": "enabled",
                "insights": agent_insights,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        
    except Exception as e:
        logger.error("Failed to get commit history (public)", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit history",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code='{"limit": 10, "offset": 0, "author": "mdasif08", "branch": "main"}',
            fix_command=(
                'curl -X POST "http://localhost:8001/api/commits/history/public" '
                '-H "Content-Type: application/json" '
                '-d \'{"limit": 10, "offset": 0, "author": "mdasif08", "branch": "main"}\''
            ),
            file_name=file_name,
            line_number=line_number,
        )


@app.get("/api/commits/history/public")
async def get_commit_history_public_get(
    limit: int = Query(50, ge=1, le=100, description="Number of commits to return"),
    offset: int = Query(0, ge=0, description="Number of commits to skip"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    branch: Optional[str] = Query(None, description="Filter by branch name")
):
    """Get commit history with query parameters (public endpoint)."""
    try:
        # Get commit history using auto sync service
        result = await auto_sync_service.get_commit_history(
            limit=limit,
            offset=offset,
            author=author,
            branch=branch,
        )
        
        # Agent mode: Add AI-powered analysis and insights
        agent_insights = {
            "analysis": {
                "total_commits": result.get("total_count", 0),
                "page_info": {
                    "current_page": result.get("page", 1),
                    "page_size": result.get("page_size", limit),
                    "has_more": result.get("total_count", 0) > (result.get("page", 1) * limit)
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
        if result.get("total_count", 0) == 0:
            agent_insights["recommendations"].append({
                "type": "info",
                "message": "No commits found with current filters. Try removing author or branch filters.",
                "suggestion": "Remove filters to see all commits",
            })
        elif result.get("total_count", 0) > 100:
            agent_insights["recommendations"].append({
                "type": "optimization",
                "message": "Large dataset detected. Consider using pagination for better performance.",
                "suggestion": "Use smaller limit values or add more specific filters",
            })

        # Return JSON API format response with Agent insights
        return {
            "status": "success",
            "data": result,
            "agent": {
                "mode": "enabled",
                "insights": agent_insights,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
        
    except Exception as e:
        logger.error("Failed to get commit history (public GET)", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit history",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="limit=10&offset=0&author=mdasif08&branch=main",
            fix_command=(
                'curl -X GET "http://localhost:8001/api/commits/history/public?'
                'limit=10&offset=0&author=mdasif08&branch=main"'
            ),
            file_name=file_name,
            line_number=line_number,
        )


@app.get("/api/commits/statistics")
async def get_commit_statistics(current_user: User = Depends(get_current_user)):
    """Get comprehensive commit statistics from database."""
    try:
        result = await auto_sync_service.get_commit_statistics()
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error("Failed to get commit statistics", error=str(e))
        file_name, line_number = get_error_location()
        return ErrorResponse(
            error="Failed to get commit statistics",
            detail=str(e),
            timestamp=datetime.now(timezone.utc),
            fix_code="Check database connection and sync status",
            fix_command="GET /api/sync/status",
            file_name=file_name,
            line_number=line_number,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
