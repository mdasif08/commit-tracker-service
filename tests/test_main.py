import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app, lifespan, track_requests, STARTUP_TIME
from src.models import (
    WebhookPayload,
    LocalCommitData,
    CommitHistoryResponse,
    CommitMetrics,
)
from src.config import settings


def get_auth_token(client: TestClient) -> str:
    """Helper function to get authentication token for tests."""
    response = client.post(
        "/api/auth/token", data={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]


class TestLifespan:
    """Test cases for application lifespan manager."""

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self):
        """Test successful application startup."""
        mock_app = MagicMock()

        with patch("src.main.get_db_service") as mock_get_db:
            mock_db_service = AsyncMock()
            mock_get_db.return_value = mock_db_service

            async with lifespan(mock_app):
                mock_get_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_failure(self):
        """Test application startup with database failure."""
        mock_app = MagicMock()

        with patch("src.main.get_db_service") as mock_get_db:
            mock_get_db.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception, match="Database connection failed"):
                async with lifespan(mock_app):
                    pass

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_success(self):
        """Test successful application shutdown."""
        mock_app = MagicMock()

        with patch("src.main.get_db_service") as mock_get_db, patch(
            "src.main.close_db_service"
        ) as mock_close_db:
            mock_db_service = AsyncMock()
            mock_get_db.return_value = mock_db_service

            async with lifespan(mock_app):
                pass

            mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_exception(self):
        """Test application shutdown with exception."""
        mock_app = MagicMock()

        with patch("src.main.get_db_service") as mock_get_db, patch(
            "src.main.close_db_service"
        ) as mock_close_db:
            mock_db_service = AsyncMock()
            mock_get_db.return_value = mock_db_service
            mock_close_db.side_effect = Exception("Close error")

            # Should not raise exception during shutdown
            async with lifespan(mock_app):
                pass

            mock_close_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_cancelled(self):
        """Test application shutdown with CancelledError."""
        mock_app = MagicMock()

        with patch("src.main.get_db_service") as mock_get_db, patch(
            "src.main.close_db_service"
        ) as mock_close_db:
            mock_db_service = AsyncMock()
            mock_get_db.return_value = mock_db_service
            mock_close_db.side_effect = asyncio.CancelledError()

            # Should handle CancelledError gracefully
            async with lifespan(mock_app):
                pass

            mock_close_db.assert_called_once()


class TestMiddleware:
    """Test cases for middleware functions."""

    @pytest.mark.asyncio
    async def test_track_requests_middleware(self):
        """Test request tracking middleware."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_call_next = AsyncMock(return_value=mock_response)

        with patch("src.main.time.time") as mock_time:
            mock_time.side_effect = [
                100.0,
                100.1,
                100.2,
            ]  # start_time, end_time, extra calls

            response = await track_requests(mock_request, mock_call_next)

            assert response == mock_response
            mock_call_next.assert_called_once_with(mock_request)


class TestHealthCheck:
    """Test cases for health check endpoint."""

    def test_health_check_success(self):
        """Test successful health check."""
        with patch("src.main.get_db_service") as mock_get_db:
            mock_db_service = AsyncMock()
            mock_db_service.health_check.return_value = True
            mock_get_db.return_value = mock_db_service

            client = TestClient(app)
            response = client.get("/health", headers={"Host": "localhost"})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "healthy"
            assert "timestamp" in data
            assert data["version"] == settings.APP_VERSION

    def test_health_check_database_unhealthy(self):
        """Test health check with unhealthy database."""
        with patch("src.main.get_db_service") as mock_get_db:
            mock_db_service = AsyncMock()
            mock_db_service.health_check.return_value = False
            mock_get_db.return_value = mock_db_service

            client = TestClient(app)
            response = client.get("/health", headers={"Host": "localhost"})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "unhealthy"

    def test_health_check_database_error(self):
        """Test health check with database error."""
        with patch("src.main.get_db_service") as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            client = TestClient(app)
            response = client.get("/health", headers={"Host": "localhost"})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database_status"] == "error"


class TestMetrics:
    """Test cases for metrics endpoint."""

    def test_metrics_enabled(self):
        """Test metrics endpoint when enabled."""
        with patch("src.main.settings.ENABLE_METRICS", True):
            client = TestClient(app)
            response = client.get("/metrics", headers={"Host": "localhost"})

            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]

    def test_metrics_disabled(self):
        """Test metrics endpoint when disabled."""
        with patch("src.main.settings.ENABLE_METRICS", False):
            client = TestClient(app)
            response = client.get("/metrics", headers={"Host": "localhost"})

            assert response.status_code == 404
            response_data = response.json()
            assert response_data["error"] == "Metrics disabled"


class TestWebhookCommitTracking:
    """Test cases for webhook commit tracking endpoint."""

    def test_track_webhook_commit_success(self):
        """Test successful webhook commit tracking."""
        webhook_data = {
            "event_type": "push",
            "repository": {"full_name": "test/repo"},
            "commits": [
                {
                    "id": "abc123",
                    "message": "Test commit",
                    "author": {"name": "Test Author", "email": "test@example.com"},
                    "timestamp": "2023-01-01T00:00:00Z",
                }
            ],
            "sender": {"login": "testuser"},
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "compare": "https://github.com/test/repo/compare/abc123...def456",
        }

        with patch("src.main.commit_service.track_webhook_commit") as mock_track:
            mock_track.return_value = [{"id": "abc123", "status": "tracked"}]

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/commits/webhook", json=webhook_data, headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Tracked 1 commits from webhook" in data["message"]
            assert len(data["commits"]) == 1

    def test_track_webhook_commit_failure(self):
        """Test webhook commit tracking failure."""
        webhook_data = {
            "event_type": "push",
            "repository": {"full_name": "test/repo"},
            "commits": [],
            "sender": {"login": "testuser"},
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "compare": "https://github.com/test/repo/compare/abc123...def456",
        }

        with patch("src.main.commit_service.track_webhook_commit") as mock_track:
            mock_track.side_effect = Exception("Tracking failed")

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/commits/webhook", json=webhook_data, headers=headers
            )

            assert response.status_code == 500
            assert "Tracking failed" in response.json()["error"]


class TestLocalCommitTracking:
    """Test cases for local commit tracking endpoint."""

    def test_track_local_commit_success(self):
        """Test successful local commit tracking."""
        local_commit_data = {
            "commit_hash": "abc123def456",
            "repository_path": "/path/to/repo",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "commit_message": "Test commit",
            "commit_date": "2023-01-01T00:00:00Z",
            "branch_name": "main",
            "files_changed": ["file1.py", "file2.py"],
            "lines_added": 10,
            "lines_deleted": 5,
            "parent_commits": ["parent1", "parent2"],
        }

        with patch("src.main.commit_service.track_local_commit") as mock_track:
            mock_track.return_value = {"id": "abc123", "status": "tracked"}

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/commits/local",
                json=local_commit_data,
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Local commit tracked successfully" in data["message"]
            assert data["commit"]["id"] == "abc123"

    def test_track_local_commit_failure(self):
        """Test local commit tracking failure."""
        local_commit_data = {
            "commit_hash": "abc123",
            "repository_path": "/path/to/repo",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "commit_message": "Test commit",
            "commit_date": "2023-01-01T00:00:00Z",
            "branch_name": "main",
            "files_changed": ["file1.py"],
            "lines_added": 5,
            "lines_deleted": 2,
            "parent_commits": ["parent1"],
        }

        with patch("src.main.commit_service.track_local_commit") as mock_track:
            mock_track.side_effect = Exception("Tracking failed")

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/commits/local",
                json=local_commit_data,
                headers=headers,
            )

            assert response.status_code == 500
            assert "Tracking failed" in response.json()["error"]


class TestCommitHistory:
    """Test cases for commit history endpoint."""

    def test_get_commit_history_success(self):
        """Test successful commit history retrieval."""
        with patch("src.main.commit_service.get_commit_history") as mock_get_history:
            mock_get_history.return_value = CommitHistoryResponse(
                repository_name="test-repo",
                commits=[],
                total_count=0,
                page=1,
                page_size=50,
            )

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.get("/api/commits/test-repo", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 0
            assert data["page"] == 1

    def test_get_commit_history_with_pagination(self):
        """Test commit history with pagination parameters."""
        with patch("src.main.commit_service.get_commit_history") as mock_get_history:
            mock_get_history.return_value = CommitHistoryResponse(
                repository_name="test-repo",
                commits=[],
                total_count=0,
                page=2,
                page_size=25,
            )

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.get(
                "/api/commits/test-repo?page=2&page_size=25",
                headers=headers,
            )

            assert response.status_code == 200
            mock_get_history.assert_called_once_with("test-repo", 2, 25)

    def test_get_commit_history_failure(self):
        """Test commit history retrieval failure."""
        with patch("src.main.commit_service.get_commit_history") as mock_get_history:
            mock_get_history.side_effect = Exception("History retrieval failed")

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.get("/api/commits/test-repo", headers=headers)

            assert response.status_code == 500
            assert "History retrieval failed" in response.json()["error"]


class TestCommitMetrics:
    """Test cases for commit metrics endpoint."""

    def test_get_commit_metrics_success(self):
        """Test successful commit metrics retrieval."""
        with patch("src.main.commit_service.get_commit_metrics") as mock_get_metrics:
            mock_get_metrics.return_value = CommitMetrics(
                repository_name="test-repo",
                total_commits=100,
                commits_today=5,
                commits_this_week=20,
                commits_this_month=50,
                average_commits_per_day=3.33,
                most_active_author="Test Author",
                most_active_branch="main",
            )

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.get("/api/commits/test-repo/metrics", headers=headers)

            assert response.status_code == 200
            data = response.json()
            assert data["total_commits"] == 100
            assert data["commits_today"] == 5

    def test_get_commit_metrics_failure(self):
        """Test commit metrics retrieval failure."""
        with patch("src.main.commit_service.get_commit_metrics") as mock_get_metrics:
            mock_get_metrics.side_effect = Exception("Metrics retrieval failed")

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}
            response = client.get("/api/commits/test-repo/metrics", headers=headers)

            assert response.status_code == 500
            assert "Metrics retrieval failed" in response.json()["error"]


class TestGitUtilities:
    """Test cases for git utilities endpoints."""

    def test_get_git_status_success(self):
        """Test successful git status retrieval."""
        with patch("src.main.git_utils.get_repository_name") as mock_get_name, patch(
            "src.main.git_utils.get_current_branch"
        ) as mock_get_branch, patch(
            "src.main.git_utils.get_uncommitted_changes"
        ) as mock_get_changes:

            mock_get_name.return_value = "test-repo"
            mock_get_branch.return_value = "main"
            mock_get_changes.return_value = ["file1.py", "file2.py"]

            client = TestClient(app)
            response = client.get("/api/git/status", headers={"Host": "localhost"})

            assert response.status_code == 200
            data = response.json()
            assert data["repository_name"] == "test-repo"
            assert data["current_branch"] == "main"
            assert data["uncommitted_changes"] == ["file1.py", "file2.py"]

    def test_get_git_status_failure(self):
        """Test git status retrieval failure."""
        with patch("src.main.git_utils.get_repository_name") as mock_get_name:
            mock_get_name.side_effect = Exception("Git status failed")

            client = TestClient(app)
            response = client.get("/api/git/status", headers={"Host": "localhost"})

            assert response.status_code == 500
            assert "Git status failed" in response.json()["error"]

    def test_get_recent_commits_success(self):
        """Test successful recent commits retrieval."""
        with patch("src.main.git_utils.get_recent_commits") as mock_get_commits:
            mock_get_commits.return_value = [
                {"hash": "abc123", "message": "Test commit 1"},
                {"hash": "def456", "message": "Test commit 2"},
            ]

            client = TestClient(app)
            response = client.get(
                "/api/git/commits/recent?count=2", headers={"Host": "localhost"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["commits"]) == 2
            mock_get_commits.assert_called_once_with(2)

    def test_get_recent_commits_failure(self):
        """Test recent commits retrieval failure."""
        with patch("src.main.git_utils.get_recent_commits") as mock_get_commits:
            mock_get_commits.side_effect = Exception("Recent commits failed")

            client = TestClient(app)
            response = client.get(
                "/api/git/commits/recent", headers={"Host": "localhost"}
            )

            assert response.status_code == 500
            assert "Recent commits failed" in response.json()["error"]

    def test_get_commit_info_success(self):
        """Test successful commit info retrieval."""
        with patch("src.main.git_utils.get_commit_info") as mock_get_info:
            mock_get_info.return_value = {
                "hash": "abc123",
                "message": "Test commit",
                "author": "Test Author",
                "date": "2023-01-01T00:00:00Z",
            }

            client = TestClient(app)
            response = client.get(
                "/api/git/commits/abc123", headers={"Host": "localhost"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["hash"] == "abc123"
            assert data["message"] == "Test commit"

    def test_get_commit_info_not_found(self):
        """Test commit info retrieval for non-existent commit."""
        with patch("src.main.git_utils.get_commit_info") as mock_get_info:
            mock_get_info.return_value = None

            client = TestClient(app)
            response = client.get(
                "/api/git/commits/nonexistent", headers={"Host": "localhost"}
            )

            assert response.status_code == 404
            response_data = response.json()
            assert response_data["error"] == "Commit not found"

    def test_get_commit_info_failure(self):
        """Test commit info retrieval failure."""
        with patch("src.main.git_utils.get_commit_info") as mock_get_info:
            mock_get_info.side_effect = Exception("Commit info failed")

            client = TestClient(app)
            response = client.get(
                "/api/git/commits/abc123", headers={"Host": "localhost"}
            )

            assert response.status_code == 500
            response_data = response.json()
            assert "Commit info failed" in response_data["error"]


class TestErrorHandlers:
    """Test cases for error handlers."""

    def test_http_exception_handler(self):
        """Test HTTP exception handler."""
        client = TestClient(app)
        response = client.get("/nonexistent-endpoint", headers={"Host": "localhost"})

        assert response.status_code == 404
        data = response.json()
        # FastAPI's default 404 handler returns {"detail": "Not Found"}
        assert "detail" in data
        assert data["detail"] == "Not Found"


class TestRootEndpoint:
    """Test cases for root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        client = TestClient(app)
        response = client.get("/", headers={"Host": "localhost"})

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert data["status"] == "running"
        assert "uptime" in data
        assert isinstance(data["uptime"], (int, float))


class TestAppConfiguration:
    """Test cases for FastAPI app configuration."""

    def test_app_title_and_version(self):
        """Test app title and version configuration."""
        assert app.title == settings.APP_NAME
        assert app.version == settings.APP_VERSION

    def test_trusted_host_middleware(self):
        """Test trusted host middleware configuration."""
        client = TestClient(app)
        response = client.get("/", headers={"Host": "localhost:8000"})

        # Should work with localhost
        assert response.status_code == 200


class TestStartupTime:
    """Test cases for startup time functionality."""

    def test_startup_time_initialization(self):
        """Test startup time initialization."""
        assert isinstance(STARTUP_TIME, (int, float))
        assert STARTUP_TIME > 0

    def test_uptime_calculation(self):
        """Test uptime calculation in root endpoint."""
        client = TestClient(app)
        response = client.get("/", headers={"Host": "localhost"})

        data = response.json()
        uptime = data["uptime"]

        assert isinstance(uptime, (int, float))
        assert uptime >= 0


class TestModelValidation:
    """Test cases for model validation."""

    def test_webhook_payload_validation(self):
        """Test WebhookPayload model validation."""
        valid_data = {
            "event_type": "push",
            "repository": {"full_name": "test/repo"},
            "commits": [],
            "sender": {"login": "testuser"},
            "ref": "refs/heads/main",
            "before": "abc123",
            "after": "def456",
            "compare": "https://github.com/test/repo/compare/abc123...def456",
        }

        payload = WebhookPayload(**valid_data)
        assert payload.event_type == "push"
        assert payload.repository["full_name"] == "test/repo"

    def test_local_commit_data_validation(self):
        """Test LocalCommitData model validation."""
        valid_data = {
            "commit_hash": "abc123def456",
            "repository_path": "/path/to/repo",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "commit_message": "Test commit",
            "commit_date": "2023-01-01T00:00:00Z",
            "branch_name": "main",
            "files_changed": ["file1.py", "file2.py"],
            "lines_added": 10,
            "lines_deleted": 5,
            "parent_commits": ["parent1", "parent2"],
        }

        commit_data = LocalCommitData(**valid_data)
        assert commit_data.commit_hash == "abc123def456"
        assert commit_data.author_name == "Test Author"


class TestQueryParameters:
    """Test cases for query parameter validation."""

    def test_commit_history_pagination_validation(self):
        """Test pagination parameter validation."""
        with patch("src.main.commit_service.get_commit_history") as mock_get_history:
            mock_get_history.return_value = CommitHistoryResponse(
                repository_name="test-repo",
                commits=[],
                total_count=0,
                page=1,
                page_size=50,
            )

            client = TestClient(app)
            token = get_auth_token(client)
            headers = {"Host": "localhost", "Authorization": f"Bearer {token}"}

            # Test valid parameters
            response = client.get(
                "/api/commits/test-repo?page=1&page_size=50",
                headers=headers,
            )
            assert response.status_code == 200

            # Test invalid page number
            response = client.get("/api/commits/test-repo?page=0", headers=headers)
            assert response.status_code == 422

            # Test invalid page size
            response = client.get("/api/commits/test-repo?page_size=0", headers=headers)
            assert response.status_code == 422

            # Test page size too large
            response = client.get(
                "/api/commits/test-repo?page_size=101", headers=headers
            )
            assert response.status_code == 422

    def test_recent_commits_count_validation(self):
        """Test count parameter validation for recent commits."""
        with patch("src.main.git_utils.get_recent_commits") as mock_get_commits:
            mock_get_commits.return_value = []

            client = TestClient(app)

            # Test valid count
            response = client.get(
                "/api/git/commits/recent?count=10", headers={"Host": "localhost"}
            )
            assert response.status_code == 200

            # Test invalid count
            response = client.get(
                "/api/git/commits/recent?count=0", headers={"Host": "localhost"}
            )
            assert response.status_code == 422

            # Test count too large
            response = client.get(
                "/api/git/commits/recent?count=51", headers={"Host": "localhost"}
            )
            assert response.status_code == 422
