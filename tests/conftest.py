import pytest
import asyncio
from unittest.mock import AsyncMock
from src.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_service():
    """Mock database service for testing."""
    mock_service = AsyncMock()
    mock_session = AsyncMock()
    mock_service.get_session.return_value.__aenter__.return_value = mock_session
    return mock_service


@pytest.fixture
def test_settings():
    """Test settings with overridden values."""
    return settings


@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload for testing."""
    return {
        "event_type": "push",
        "repository": {
            "full_name": "test/repo",
            "name": "repo",
            "owner": {"login": "test"},
        },
        "commits": [
            {
                "id": "abc123def456",
                "author": {"name": "Test Author", "email": "test@example.com"},
                "message": "Test commit message",
                "timestamp": "2023-01-01T00:00:00Z",
                "modified": ["file1.py"],
                "added": ["file2.py"],
                "removed": [],
                "stats": {"additions": 10, "deletions": 5},
                "parents": ["parent123"],
            }
        ],
        "sender": {"login": "testuser"},
        "ref": "refs/heads/main",
        "before": "before123",
        "after": "after456",
        "created": False,
        "compare": "https://github.com/test/repo/compare/before123...after456",
    }


@pytest.fixture
def sample_local_commit_data():
    """Sample local commit data for testing."""
    return {
        "commit_hash": "abc123def456",
        "repository_path": "/path/to/repo",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "commit_message": "Test commit message",
        "commit_date": "2023-01-01T00:00:00Z",
        "branch_name": "main",
        "files_changed": ["file1.py", "file2.py"],
        "lines_added": 10,
        "lines_deleted": 5,
        "parent_commits": ["parent123"],
    }
