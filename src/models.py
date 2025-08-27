from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class CommitSource(str, Enum):
    """Source of commit data."""

    WEBHOOK = "webhook"
    LOCAL = "local"

class CommitStatus(str, Enum):
    """Status of commit processing."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class CommitData(BaseModel):
    """Commit data structure."""

    commit_hash: str = Field(..., description="Git commit hash")
    repository_name: str = Field(..., description="Repository name")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    commit_message: str = Field(..., description="Commit message")
    commit_date: datetime = Field(..., description="Commit timestamp")
    source_type: CommitSource = Field(..., description="Source of commit data")
    branch_name: Optional[str] = Field(None, description="Branch name")
    files_changed: Optional[List[str]] = Field(
        None, description="List of changed files"
    )
    lines_added: Optional[int] = Field(None, description="Lines added")
    lines_deleted: Optional[int] = Field(None, description="Lines deleted")
    parent_commits: Optional[List[str]] = Field(
        None, description="Parent commit hashes"
    )

class CommitCreateRequest(BaseModel):
    """Request model for creating a commit record."""

    commit_data: CommitData
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class CommitResponse(BaseModel):
    """Response model for commit operations."""

    id: str = Field(..., description="Commit record ID")
    commit_hash: str = Field(..., description="Git commit hash")
    repository_name: str = Field(..., description="Repository name")
    status: CommitStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Record creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")

class CommitHistoryResponse(BaseModel):
    """Response model for commit history."""

    repository_name: str = Field(..., description="Repository name")
    commits: List[CommitResponse] = Field(..., description="List of commits")
    total_count: int = Field(..., description="Total number of commits")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")

class CommitMetrics(BaseModel):
    """Commit metrics and statistics."""

    repository_name: str = Field(..., description="Repository name")
    total_commits: int = Field(..., description="Total number of commits")
    commits_today: int = Field(..., description="Commits made today")
    commits_this_week: int = Field(..., description="Commits made this week")
    commits_this_month: int = Field(..., description="Commits made this month")
    average_commits_per_day: float = Field(..., description="Average commits per day")
    most_active_author: str = Field(..., description="Most active author")
    most_active_branch: str = Field(..., description="Most active branch")
    last_commit_date: Optional[datetime] = Field(None, description="Last commit date")

class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    database_status: str = Field(..., description="Database connection status")

class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class WebhookPayload(BaseModel):
    """Webhook payload from GitHub webhook service."""

    event_type: str = Field(..., description="GitHub event type")
    repository: Dict[str, Any] = Field(..., description="Repository information")
    commits: List[Dict[str, Any]] = Field(..., description="List of commits")
    sender: Dict[str, Any] = Field(..., description="Sender information")
    ref: str = Field(..., description="Git reference")
    before: str = Field(..., description="Previous commit hash")
    after: str = Field(..., description="Current commit hash")
    created: bool = Field(False, description="Whether this is a new branch")
    deleted: bool = Field(False, description="Whether this is a deleted branch")
    forced: bool = Field(False, description="Whether this was a forced push")
    base_ref: Optional[str] = Field(None, description="Base reference")
    compare: str = Field(..., description="Compare URL")
    head_commit: Optional[Dict[str, Any]] = Field(
        None, description="Head commit information"
    )

class LocalCommitData(BaseModel):
    """Local commit data structure."""

    commit_hash: str = Field(..., description="Git commit hash")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    commit_message: str = Field(..., description="Commit message")
    commit_date: datetime = Field(..., description="Commit timestamp")
    branch_name: str = Field(..., description="Branch name")
    files_changed: List[str] = Field(..., description="List of changed files")
    lines_added: int = Field(..., description="Lines added")
    lines_deleted: int = Field(..., description="Lines deleted")
    parent_commits: List[str] = Field(..., description="Parent commit hashes")
    repository_path: str = Field(..., description="Repository path")

class User(BaseModel):
    """User model for authentication."""

    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    disabled: bool = Field(False, description="Account disabled status")

class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str = Field(..., description="Hashed password")

class Token(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

class TokenData(BaseModel):
    """Token data model."""

    username: Optional[str] = Field(None, description="Username from token")
