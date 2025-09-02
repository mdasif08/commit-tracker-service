import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models import (
    CommitSource,
    CommitStatus,
    CommitData,
    CommitCreateRequest,
    CommitResponse,
    CommitHistoryResponse,
    CommitMetrics,
    HealthCheckResponse,
    ErrorResponse,
    WebhookPayload,
    LocalCommitData,
)


class TestCommitSource:
    """Test cases for CommitSource enum."""

    def test_commit_source_values(self):
        """Test CommitSource enum values."""
        assert CommitSource.WEBHOOK == "webhook"
        assert CommitSource.LOCAL == "local"

    def test_commit_source_membership(self):
        """Test CommitSource enum membership."""
        assert CommitSource.WEBHOOK in CommitSource
        assert CommitSource.LOCAL in CommitSource
        assert "invalid" not in [e.value for e in CommitSource]


class TestCommitStatus:
    """Test cases for CommitStatus enum."""

    def test_commit_status_values(self):
        """Test CommitStatus enum values."""
        assert CommitStatus.PENDING == "pending"
        assert CommitStatus.PROCESSED == "processed"
        assert CommitStatus.FAILED == "failed"

    def test_commit_status_membership(self):
        """Test CommitStatus enum membership."""
        assert CommitStatus.PENDING in CommitStatus
        assert CommitStatus.PROCESSED in CommitStatus
        assert CommitStatus.FAILED in CommitStatus
        assert "invalid" not in [e.value for e in CommitStatus]


class TestCommitData:
    """Test cases for CommitData model."""

    def test_commit_data_creation(self):
        """Test creating a CommitData instance with all required fields."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
            branch_name="main",
            files_changed=["file1.py", "file2.py"],
            lines_added=10,
            lines_deleted=5,
            parent_commits=["parent123"],
        )

        assert commit_data.commit_hash == "abc123def456"
        assert commit_data.repository_name == "test-repo"
        assert commit_data.author_name == "Test Author"
        assert commit_data.author_email == "test@example.com"
        assert commit_data.commit_message == "Test commit message"
        assert isinstance(commit_data.commit_date, datetime)
        assert commit_data.source_type == CommitSource.WEBHOOK
        assert commit_data.branch_name == "main"
        assert commit_data.files_changed == ["file1.py", "file2.py"]
        assert commit_data.lines_added == 10
        assert commit_data.lines_deleted == 5
        assert commit_data.parent_commits == ["parent123"]

    def test_commit_data_creation_minimal(self):
        """Test creating a CommitData instance with only required fields."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.LOCAL,
        )

        assert commit_data.commit_hash == "abc123def456"
        assert commit_data.repository_name == "test-repo"
        assert commit_data.author_name == "Test Author"
        assert commit_data.author_email == "test@example.com"
        assert commit_data.commit_message == "Test commit message"
        assert isinstance(commit_data.commit_date, datetime)
        assert commit_data.source_type == CommitSource.LOCAL
        assert commit_data.branch_name is None
        assert commit_data.files_changed is None
        assert commit_data.lines_added is None
        assert commit_data.lines_deleted is None
        assert commit_data.parent_commits is None

    def test_commit_data_validation_error_missing_required(self):
        """Test CommitData validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            CommitData(
                commit_hash="abc123def456",
                # Missing repository_name
                author_name="Test Author",
                author_email="test@example.com",
                commit_message="Test commit message",
                commit_date=datetime.now(timezone.utc),
                source_type=CommitSource.WEBHOOK,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("repository_name",)
        assert errors[0]["type"] == "missing"

    def test_commit_data_model_dump(self):
        """Test CommitData model_dump method."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        data = commit_data.model_dump()
        assert data["commit_hash"] == "abc123def456"
        assert data["repository_name"] == "test-repo"
        assert data["author_name"] == "Test Author"
        assert data["source_type"] == "webhook"
        assert "commit_date" in data


class TestCommitCreateRequest:
    """Test cases for CommitCreateRequest model."""

    def test_commit_create_request_creation(self):
        """Test creating a CommitCreateRequest instance."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        metadata = {"source": "webhook", "event_id": "12345"}

        request = CommitCreateRequest(commit_data=commit_data, metadata=metadata)

        assert request.commit_data == commit_data
        assert request.metadata == metadata

    def test_commit_create_request_creation_without_metadata(self):
        """Test creating a CommitCreateRequest instance without metadata."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        request = CommitCreateRequest(commit_data=commit_data)

        assert request.commit_data == commit_data
        assert request.metadata is None


class TestCommitResponse:
    """Test cases for CommitResponse model."""

    def test_commit_response_creation(self):
        """Test creating a CommitResponse instance."""
        response = CommitResponse(
            id="uuid-123",
            commit_hash="abc123def456",
            repository_name="test-repo",
            status=CommitStatus.PROCESSED,
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
        )

        assert response.id == "uuid-123"
        assert response.commit_hash == "abc123def456"
        assert response.repository_name == "test-repo"
        assert response.status == CommitStatus.PROCESSED
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.processed_at, datetime)

    def test_commit_response_creation_without_processed_at(self):
        """Test creating a CommitResponse instance without processed_at."""
        response = CommitResponse(
            id="uuid-123",
            commit_hash="abc123def456",
            repository_name="test-repo",
            status=CommitStatus.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        assert response.id == "uuid-123"
        assert response.commit_hash == "abc123def456"
        assert response.repository_name == "test-repo"
        assert response.status == CommitStatus.PENDING
        assert isinstance(response.created_at, datetime)
        assert response.processed_at is None


class TestCommitHistoryResponse:
    """Test cases for CommitHistoryResponse model."""

    def test_commit_history_response_creation(self):
        """Test creating a CommitHistoryResponse instance."""
        commits = [
            CommitResponse(
                id="uuid-1",
                commit_hash="abc123",
                repository_name="test-repo",
                status=CommitStatus.PROCESSED,
                created_at=datetime.now(timezone.utc),
            ),
            CommitResponse(
                id="uuid-2",
                commit_hash="def456",
                repository_name="test-repo",
                status=CommitStatus.PROCESSED,
                created_at=datetime.now(timezone.utc),
            ),
        ]

        response = CommitHistoryResponse(
            repository_name="test-repo",
            commits=commits,
            total_count=2,
            page=1,
            page_size=10,
        )

        assert response.repository_name == "test-repo"
        assert len(response.commits) == 2
        assert response.total_count == 2
        assert response.page == 1
        assert response.page_size == 10

    def test_commit_history_response_empty_commits(self):
        """Test creating a CommitHistoryResponse instance with empty commits."""
        response = CommitHistoryResponse(
            repository_name="test-repo", commits=[], total_count=0, page=1, page_size=10
        )

        assert response.repository_name == "test-repo"
        assert len(response.commits) == 0
        assert response.total_count == 0
        assert response.page == 1
        assert response.page_size == 10


class TestCommitMetrics:
    """Test cases for CommitMetrics model."""

    def test_commit_metrics_creation(self):
        """Test creating a CommitMetrics instance."""
        metrics = CommitMetrics(
            repository_name="test-repo",
            total_commits=100,
            commits_today=5,
            commits_this_week=20,
            commits_this_month=50,
            average_commits_per_day=3.33,
            most_active_author="Test Author",
            most_active_branch="main",
            last_commit_date=datetime.now(timezone.utc),
        )

        assert metrics.repository_name == "test-repo"
        assert metrics.total_commits == 100
        assert metrics.commits_today == 5
        assert metrics.commits_this_week == 20
        assert metrics.commits_this_month == 50
        assert metrics.average_commits_per_day == 3.33
        assert metrics.most_active_author == "Test Author"
        assert metrics.most_active_branch == "main"
        assert isinstance(metrics.last_commit_date, datetime)

    def test_commit_metrics_creation_without_last_commit_date(self):
        """Test creating a CommitMetrics instance without last_commit_date."""
        metrics = CommitMetrics(
            repository_name="test-repo",
            total_commits=0,
            commits_today=0,
            commits_this_week=0,
            commits_this_month=0,
            average_commits_per_day=0.0,
            most_active_author="No commits",
            most_active_branch="main",
        )

        assert metrics.repository_name == "test-repo"
        assert metrics.total_commits == 0
        assert metrics.commits_today == 0
        assert metrics.commits_this_week == 0
        assert metrics.commits_this_month == 0
        assert metrics.average_commits_per_day == 0.0
        assert metrics.most_active_author == "No commits"
        assert metrics.most_active_branch == "main"
        assert metrics.last_commit_date is None


class TestHealthCheckResponse:
    """Test cases for HealthCheckResponse model."""

    def test_health_check_response_creation(self):
        """Test creating a HealthCheckResponse instance."""
        response = HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            database_status="connected",
        )

        assert response.status == "healthy"
        assert isinstance(response.timestamp, datetime)
        assert response.version == "1.0.0"
        assert response.database_status == "connected"

    def test_health_check_response_unhealthy(self):
        """Test creating a HealthCheckResponse instance for unhealthy status."""
        response = HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            database_status="disconnected",
        )

        assert response.status == "unhealthy"
        assert isinstance(response.timestamp, datetime)
        assert response.version == "1.0.0"
        assert response.database_status == "disconnected"


class TestErrorResponse:
    """Test cases for ErrorResponse model."""

    def test_error_response_creation(self):
        """Test creating an ErrorResponse instance."""
        response = ErrorResponse(
            error="Something went wrong",
            detail="Detailed error information",
            timestamp=datetime.now(timezone.utc),
            request_id="req-12345",
        )

        assert response.error == "Something went wrong"
        assert response.detail == "Detailed error information"
        assert isinstance(response.timestamp, datetime)
        assert response.request_id == "req-12345"

    def test_error_response_creation_without_optional_fields(self):
        """Test creating an ErrorResponse instance without optional fields."""
        response = ErrorResponse(
            error="Something went wrong", timestamp=datetime.now(timezone.utc)
        )

        assert response.error == "Something went wrong"
        assert response.detail is None
        assert isinstance(response.timestamp, datetime)
        assert response.request_id is None


class TestWebhookPayload:
    """Test cases for WebhookPayload model."""

    def test_webhook_payload_creation(self):
        """Test creating a WebhookPayload instance."""
        payload = WebhookPayload(
            event_type="push",
            repository={"full_name": "test/repo", "id": 123},
            commits=[
                {
                    "id": "abc123",
                    "author": {"name": "Test Author", "email": "test@example.com"},
                    "message": "Test commit",
                    "timestamp": "2023-01-01T00:00:00Z",
                }
            ],
            sender={"login": "testuser", "id": 456},
            ref="refs/heads/main",
            before="before123",
            after="after456",
            created=False,
            deleted=False,
            forced=False,
            base_ref="refs/heads/develop",
            compare="https://github.com/test/repo/compare/before123...after456",
            head_commit={"id": "after456", "message": "Test commit"},
        )

        assert payload.event_type == "push"
        assert payload.repository["full_name"] == "test/repo"
        assert payload.repository["id"] == 123
        assert len(payload.commits) == 1
        assert payload.commits[0]["id"] == "abc123"
        assert payload.sender["login"] == "testuser"
        assert payload.ref == "refs/heads/main"
        assert payload.before == "before123"
        assert payload.after == "after456"
        assert payload.created is False
        assert payload.deleted is False
        assert payload.forced is False
        assert payload.base_ref == "refs/heads/develop"
        compare_url = "https://github.com/test/repo/compare/before123...after456"
        assert payload.compare == compare_url
        assert payload.head_commit["id"] == "after456"

    def test_webhook_payload_creation_minimal(self):
        """Test creating a WebhookPayload instance with minimal fields."""
        payload = WebhookPayload(
            event_type="push",
            repository={"full_name": "test/repo"},
            commits=[],
            sender={"login": "testuser"},
            ref="refs/heads/main",
            before="before123",
            after="after456",
            compare="https://github.com/test/repo/compare/before123...after456",
        )

        assert payload.event_type == "push"
        assert payload.repository["full_name"] == "test/repo"
        assert len(payload.commits) == 0
        assert payload.sender["login"] == "testuser"
        assert payload.ref == "refs/heads/main"
        assert payload.before == "before123"
        assert payload.after == "after456"
        assert payload.created is False
        assert payload.deleted is False
        assert payload.forced is False
        assert payload.base_ref is None
        compare_url = "https://github.com/test/repo/compare/before123...after456"
        assert payload.compare == compare_url
        assert payload.head_commit is None

    def test_webhook_payload_creation_with_defaults(self):
        """Test creating a WebhookPayload instance with default values."""
        payload = WebhookPayload(
            event_type="push",
            repository={"full_name": "test/repo"},
            commits=[],
            sender={"login": "testuser"},
            ref="refs/heads/main",
            before="before123",
            after="after456",
            compare=("https://github.com/test/repo/compare/before123...after456"),
            created=True,
            deleted=True,
            forced=True,
        )

        assert payload.created is True
        assert payload.deleted is True
        assert payload.forced is True

    def test_webhook_payload_validation_error_missing_required(self):
        """Test WebhookPayload validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            WebhookPayload(
                event_type="push",
                repository={"full_name": "test/repo"},
                commits=[],
                sender={"login": "testuser"},
                ref="refs/heads/main",
                before="before123",
                after="after456",
                # Missing compare field
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("compare",)
        assert errors[0]["type"] == "missing"


class TestLocalCommitData:
    """Test cases for LocalCommitData model."""

    def test_local_commit_data_creation(self):
        """Test creating a LocalCommitData instance."""
        local_commit = LocalCommitData(
            commit_hash="abc123def456",
            repository_path="/path/to/repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            branch_name="main",
            files_changed=["file1.py", "file2.py"],
            lines_added=10,
            lines_deleted=5,
            parent_commits=["parent123", "parent456"],
        )

        assert local_commit.commit_hash == "abc123def456"
        assert local_commit.repository_path == "/path/to/repo"
        assert local_commit.author_name == "Test Author"
        assert local_commit.author_email == "test@example.com"
        assert local_commit.commit_message == "Test commit message"
        assert isinstance(local_commit.commit_date, datetime)
        assert local_commit.branch_name == "main"
        assert local_commit.files_changed == ["file1.py", "file2.py"]
        assert local_commit.lines_added == 10
        assert local_commit.lines_deleted == 5
        assert local_commit.parent_commits == ["parent123", "parent456"]

    def test_local_commit_data_creation_minimal(self):
        """Test creating a LocalCommitData instance with minimal data."""
        local_commit = LocalCommitData(
            commit_hash="abc123def456",
            repository_path="/path/to/repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime.now(timezone.utc),
            branch_name="main",
            files_changed=[],
            lines_added=0,
            lines_deleted=0,
            parent_commits=[],
        )

        assert local_commit.commit_hash == "abc123def456"
        assert local_commit.repository_path == "/path/to/repo"
        assert local_commit.author_name == "Test Author"
        assert local_commit.author_email == "test@example.com"
        assert local_commit.commit_message == "Test commit message"
        assert isinstance(local_commit.commit_date, datetime)
        assert local_commit.branch_name == "main"
        assert local_commit.files_changed == []
        assert local_commit.lines_added == 0
        assert local_commit.lines_deleted == 0
        assert local_commit.parent_commits == []

    def test_local_commit_data_validation_error_missing_required(self):
        """Test LocalCommitData validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            LocalCommitData(
                commit_hash="abc123def456",
                repository_path="/path/to/repo",
                author_name="Test Author",
                author_email="test@example.com",
                commit_message="Test commit message",
                commit_date=datetime.now(timezone.utc),
                branch_name="main",
                files_changed=["file1.py"],
                lines_added=5,
                lines_deleted=2,
                # Missing parent_commits field
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("parent_commits",)
        assert errors[0]["type"] == "missing"


class TestModelSerialization:
    """Test cases for model serialization and deserialization."""

    def test_commit_data_serialization(self):
        """Test CommitData serialization to dict."""
        commit_data = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        data = commit_data.model_dump()
        assert data["commit_hash"] == "abc123def456"
        assert data["repository_name"] == "test-repo"
        assert data["author_name"] == "Test Author"
        assert data["source_type"] == "webhook"
        assert "commit_date" in data

    def test_webhook_payload_serialization(self):
        """Test WebhookPayload serialization to dict."""
        payload = WebhookPayload(
            event_type="push",
            repository={"full_name": "test/repo"},
            commits=[],
            sender={"login": "testuser"},
            ref="refs/heads/main",
            before="before123",
            after="after456",
            compare="https://github.com/test/repo/compare/before123...after456",
        )

        data = payload.model_dump()
        assert data["event_type"] == "push"
        assert data["repository"]["full_name"] == "test/repo"
        assert data["commits"] == []
        assert data["sender"]["login"] == "testuser"
        assert data["created"] is False
        assert data["deleted"] is False
        assert data["forced"] is False

    def test_error_response_serialization(self):
        """Test ErrorResponse serialization to dict."""
        response = ErrorResponse(
            error="Something went wrong",
            detail="Detailed error information",
            timestamp=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            request_id="req-12345",
        )

        data = response.model_dump()
        assert data["error"] == "Something went wrong"
        assert data["detail"] == "Detailed error information"
        assert data["request_id"] == "req-12345"
        assert "timestamp" in data


class TestModelValidation:
    """Test cases for model validation."""

    def test_commit_data_invalid_source_type(self):
        """Test CommitData validation with invalid source type."""
        with pytest.raises(ValidationError) as exc_info:
            CommitData(
                commit_hash="abc123def456",
                repository_name="test-repo",
                author_name="Test Author",
                author_email="test@example.com",
                commit_message="Test commit message",
                commit_date=datetime.now(timezone.utc),
                source_type="invalid_source",  # Invalid enum value
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("source_type",)
        assert "enum" in errors[0]["type"]

    def test_commit_response_invalid_status(self):
        """Test CommitResponse validation with invalid status."""
        with pytest.raises(ValidationError) as exc_info:
            CommitResponse(
                id="uuid-123",
                commit_hash="abc123def456",
                repository_name="test-repo",
                status="invalid_status",  # Invalid enum value
                created_at=datetime.now(timezone.utc),
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("status",)
        assert "enum" in errors[0]["type"]

    def test_commit_metrics_negative_values(self):
        """Test CommitMetrics validation with negative values."""
        # Pydantic doesn't automatically validate negative integers by default
        # This test ensures the model accepts negative values
        # (which might be valid in some contexts)
        metrics = CommitMetrics(
            repository_name="test-repo",
            total_commits=-1,  # Negative value
            commits_today=0,
            commits_this_week=0,
            commits_this_month=0,
            average_commits_per_day=0.0,
            most_active_author="No commits",
            most_active_branch="main",
        )

        assert metrics.total_commits == -1
        assert metrics.repository_name == "test-repo"


class TestModelEquality:
    """Test cases for model equality."""

    def test_commit_data_equality(self):
        """Test CommitData equality."""
        commit_data1 = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        commit_data2 = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        assert commit_data1 == commit_data2

    def test_commit_data_inequality(self):
        """Test CommitData inequality."""
        commit_data1 = CommitData(
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        commit_data2 = CommitData(
            commit_hash="def456ghi789",  # Different hash
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        assert commit_data1 != commit_data2
