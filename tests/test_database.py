import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from src.database import (
    DatabaseService,
    CommitRecord,
    get_db_service,
    close_db_service,
    engine,
    AsyncSessionLocal,
    Base,
)
from src.models import CommitSource, CommitStatus


class TestCommitRecord:
    """Test cases for CommitRecord model."""

    def test_commit_record_creation(self):
        """Test creating a CommitRecord instance."""
        commit_id = uuid.uuid4()
        commit_date = datetime.now(timezone.utc)

        record = CommitRecord(
            id=commit_id,
            commit_hash="abc123def456",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit message",
            commit_date=commit_date,
            source_type=CommitSource.WEBHOOK,
            branch_name="main",
            files_changed=["file1.py", "file2.py"],
            lines_added=10,
            lines_deleted=5,
            parent_commits=["parent1", "parent2"],
            status=CommitStatus.PENDING,
            commit_metadata={"key": "value"},
        )

        assert record.id == commit_id
        assert record.commit_hash == "abc123def456"
        assert record.repository_name == "test-repo"
        assert record.author_name == "Test Author"
        assert record.author_email == "test@example.com"
        assert record.commit_message == "Test commit message"
        assert record.commit_date == commit_date
        assert record.source_type == CommitSource.WEBHOOK
        assert record.branch_name == "main"
        assert record.files_changed == ["file1.py", "file2.py"]
        assert record.lines_added == 10
        assert record.lines_deleted == 5
        assert record.parent_commits == ["parent1", "parent2"]
        assert record.status == CommitStatus.PENDING
        assert record.commit_metadata == {"key": "value"}

    def test_commit_record_table_name(self):
        """Test that CommitRecord has correct table name."""
        assert CommitRecord.__tablename__ == "commits"

    def test_commit_record_columns(self):
        """Test that CommitRecord has all expected columns."""
        columns = CommitRecord.__table__.columns

        expected_columns = {
            "id",
            "commit_hash",
            "repository_name",
            "author_name",
            "author_email",
            "commit_message",
            "commit_date",
            "source_type",
            "branch_name",
            "files_changed",
            "lines_added",
            "lines_deleted",
            "parent_commits",
            "status",
            "commit_metadata",
            "created_at",
            "processed_at",
            "updated_at",
        }

        actual_columns = {col.name for col in columns}
        assert actual_columns == expected_columns

    def test_commit_record_indexes(self):
        """Test that CommitRecord has expected indexes."""
        indexes = CommitRecord.__table__.indexes

        indexed_columns = set()
        for index in indexes:
            for column in index.columns:
                indexed_columns.add(column.name)

        expected_indexed = {
            "commit_hash",
            "repository_name",
            "commit_date",
            "source_type",
            "branch_name",
        }

        assert expected_indexed.issubset(indexed_columns)


class TestDatabaseService:
    """Test cases for DatabaseService class."""

    def test_database_service_initialization(self):
        """Test DatabaseService initialization."""
        db_service = DatabaseService()
        assert db_service.session_factory == AsyncSessionLocal
        assert db_service._engine == engine

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        db_service = DatabaseService()

        # Mock the session and its context manager
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.execute.side_effect = Exception("Connection failed")

        with patch.object(db_service, "get_session") as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await db_service.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_session_exception(self):
        """Test health check with session creation exception."""
        db_service = DatabaseService()

        with patch.object(db_service, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Session error")

            result = await db_service.health_check()

            assert result is False


class TestDatabaseGlobals:
    """Test cases for global database functions."""

    @pytest.fixture(autouse=True)
    def reset_global_service(self):
        """Reset global database service before each test."""
        import src.database

        src.database._db_service = None
        yield
        src.database._db_service = None

    @pytest.mark.asyncio
    async def test_get_db_service_first_time(self):
        """Test getting database service for the first time."""
        with patch("src.database.DatabaseService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            result = await get_db_service()

            mock_service_class.assert_called_once()
            mock_service.create_tables.assert_called_once()
            assert result == mock_service

    @pytest.mark.asyncio
    async def test_get_db_service_cached(self):
        """Test getting cached database service."""
        # First call to create the service
        with patch("src.database.DatabaseService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            result1 = await get_db_service()

            # Second call should return the same instance
            result2 = await get_db_service()

            assert result1 == result2
            # create_tables should only be called once
            mock_service.create_tables.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_service_with_service(self):
        """Test closing database service when service exists."""
        # First create a service
        with patch("src.database.DatabaseService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            await get_db_service()

            # Now close it
            await close_db_service()

            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_db_service_without_service(self):
        """Test closing database service when no service exists."""
        # Should not raise any exception
        await close_db_service()

    @pytest.mark.asyncio
    async def test_close_db_service_exception(self):
        """Test closing database service with exception."""
        # First create a service
        with patch("src.database.DatabaseService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.close.side_effect = Exception("Close error")
            mock_service_class.return_value = mock_service

            await get_db_service()

            # Should raise the exception
            with pytest.raises(Exception, match="Close error"):
                await close_db_service()


class TestDatabaseEngine:
    """Test cases for database engine configuration."""

    def test_engine_configuration(self):
        """Test that engine is configured correctly."""
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "echo")
        # Note: pool_pre_ping and pool_recycle are not directly accessible
        # on AsyncEngine, they are configuration options

    def test_session_factory_configuration(self):
        """Test that session factory is configured correctly."""
        assert AsyncSessionLocal is not None
        assert hasattr(AsyncSessionLocal, "__call__")

    def test_base_declarative(self):
        """Test that Base is a declarative base."""
        assert Base is not None
        assert hasattr(Base, "metadata")


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    def test_commit_record_crud_operations(self):
        """Test CRUD operations with CommitRecord."""
        # This test would require a real database connection
        # For now, we'll test the model structure and validation

        commit_record = CommitRecord(
            commit_hash="test123",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        # Test that all required fields are present
        assert commit_record.commit_hash == "test123"
        assert commit_record.repository_name == "test-repo"
        assert commit_record.author_name == "Test Author"
        assert commit_record.author_email == "test@example.com"
        assert commit_record.commit_message == "Test commit"
        assert commit_record.source_type == CommitSource.WEBHOOK

    @pytest.mark.asyncio
    async def test_database_service_lifecycle(self):
        """Test complete database service lifecycle."""
        with patch("src.database.DatabaseService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Get service
            service = await get_db_service()
            assert service == mock_service

            # Close service
            await close_db_service()
            mock_service.close.assert_called_once()

    def test_commit_record_enum_values(self):
        """Test that CommitRecord uses correct enum values."""
        record = CommitRecord(
            commit_hash="test123",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
            status=CommitStatus.PENDING,
        )

        assert record.source_type in CommitSource
        assert record.status in CommitStatus

    def test_commit_record_json_fields(self):
        """Test that JSON fields work correctly."""
        test_data = {
            "files_changed": ["file1.py", "file2.py"],
            "parent_commits": ["abc123", "def456"],
            "commit_metadata": {"branch": "main", "pr": 123},
        }

        record = CommitRecord(
            commit_hash="test123",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
            files_changed=test_data["files_changed"],
            parent_commits=test_data["parent_commits"],
            commit_metadata=test_data["commit_metadata"],
        )

        assert record.files_changed == test_data["files_changed"]
        assert record.parent_commits == test_data["parent_commits"]
        assert record.commit_metadata == test_data["commit_metadata"]

    def test_commit_record_string_representation(self):
        """Test CommitRecord string representation."""
        record = CommitRecord(
            commit_hash="test123",
            repository_name="test-repo",
            author_name="Test Author",
            author_email="test@example.com",
            commit_message="Test commit",
            commit_date=datetime.now(timezone.utc),
            source_type=CommitSource.WEBHOOK,
        )

        str_repr = str(record)
        assert "CommitRecord" in str_repr
        # The string representation might not include specific field values
        # but should contain the class name

    @pytest.mark.asyncio
    async def test_database_service_multiple_sessions(self):
        """Test creating multiple database sessions."""
        db_service = DatabaseService()

        with patch.object(db_service, "get_session") as mock_get_session:
            mock_session1 = AsyncMock()
            mock_session2 = AsyncMock()
            mock_get_session.side_effect = [mock_session1, mock_session2]

            session1 = await db_service.get_session()
            session2 = await db_service.get_session()

            assert session1 == mock_session1
            assert session2 == mock_session2
            assert session1 != session2
