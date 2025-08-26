import pytest
import json
from unittest.mock import patch, MagicMock
from subprocess import CalledProcessError
from src.utils.git_utils import GitUtils, git_utils


class TestGitUtils:
    """Test cases for GitUtils class."""

    @pytest.fixture
    def git_utils_instance(self):
        """Create a GitUtils instance for testing."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                return GitUtils("/test/repo/path")

    @pytest.fixture
    def git_utils_not_repo(self):
        """Create a GitUtils instance for non-Git repo testing."""
        with patch("os.path.exists", return_value=False):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                return GitUtils("/test/repo/path")

    def test_git_utils_initialization(self):
        """Test GitUtils initialization with valid Git repo."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                utils = GitUtils("/test/repo/path")
                assert utils.repo_path == "/test/repo/path"
                assert utils._is_git_repo is True

    def test_git_utils_initialization_not_git_repo(self):
        """Test GitUtils initialization with non-Git repo."""
        with patch("os.path.exists", return_value=False):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                utils = GitUtils("/test/repo/path")
                assert utils.repo_path == "/test/repo/path"
                assert utils._is_git_repo is False

    def test_validate_git_repo_true(self):
        """Test _validate_git_repo with valid Git repository."""
        with patch("os.path.exists", return_value=True):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                utils = GitUtils("/test/repo/path")
                assert utils._validate_git_repo() is True

    def test_validate_git_repo_false(self):
        """Test _validate_git_repo with non-Git repository."""
        with patch("os.path.exists", return_value=False):
            with patch("os.path.abspath", return_value="/test/repo/path"):
                utils = GitUtils("/test/repo/path")
                assert utils._validate_git_repo() is False

    def test_run_git_command_success(self, git_utils_instance):
        """Test successful Git command execution."""
        mock_result = MagicMock()
        mock_result.stdout = "test output\n"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = git_utils_instance._run_git_command(["status"])

            assert result == "test output"
            mock_run.assert_called_once_with(
                ["git", "status"],
                cwd="/test/repo/path",
                capture_output=True,
                text=True,
                check=True,
            )

    def test_run_git_command_failure(self, git_utils_instance):
        """Test Git command execution failure."""
        with patch(
            "subprocess.run",
            side_effect=CalledProcessError(1, "git", stderr="error message"),
        ):
            with pytest.raises(CalledProcessError):
                git_utils_instance._run_git_command(["invalid"])

    def test_run_git_command_not_git_repo(self, git_utils_not_repo):
        """Test Git command execution in non-Git repository."""
        with pytest.raises(ValueError, match="Not a Git repository"):
            git_utils_not_repo._run_git_command(["status"])

    def test_get_current_branch_success(self, git_utils_instance):
        """Test getting current branch successfully."""
        with patch.object(git_utils_instance, "_run_git_command", return_value="main"):
            result = git_utils_instance.get_current_branch()
            assert result == "main"

    def test_get_current_branch_not_git_repo(self, git_utils_not_repo):
        """Test getting current branch in non-Git repository."""
        result = git_utils_not_repo.get_current_branch()
        assert result == "unknown"

    def test_get_repository_name_from_remote(self, git_utils_instance):
        """Test getting repository name from remote origin."""
        with patch.object(
            git_utils_instance,
            "_run_git_command",
            return_value="https://github.com/user/repo.git",
        ):
            result = git_utils_instance.get_repository_name()
            assert result == "repo"

    def test_get_repository_name_from_remote_no_git_extension(self, git_utils_instance):
        """Test getting repository name from remote without .git extension."""
        with patch.object(
            git_utils_instance,
            "_run_git_command",
            return_value="https://github.com/user/repo",
        ):
            result = git_utils_instance.get_repository_name()
            assert result == "repo"

    def test_get_repository_name_fallback(self, git_utils_instance):
        """Test getting repository name with fallback to directory name."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("No remote")
        ):
            with patch("os.path.basename", return_value="repo"):
                result = git_utils_instance.get_repository_name()
                assert result == "repo"

    def test_get_repository_name_not_git_repo(self, git_utils_not_repo):
        """Test getting repository name in non-Git repository."""
        with patch("os.path.basename", return_value="repo"):
            result = git_utils_not_repo.get_repository_name()
            assert result == "repo"

    def test_get_recent_commits_success(self, git_utils_instance):
        """Test getting recent commits successfully."""
        mock_commit_data = {
            "hash": "abc123",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "commit_date": "2023-01-01T00:00:00+00:00",
            "message": "Test commit",
            "parent_hashes": "def456 ghi789",
        }

        with patch.object(
            git_utils_instance,
            "_run_git_command",
            return_value=json.dumps(mock_commit_data),
        ):
            result = git_utils_instance.get_recent_commits(5)

            assert len(result) == 1
            assert result[0]["hash"] == "abc123"
            assert result[0]["author_name"] == "Test Author"
            assert result[0]["parent_hashes"] == ["def456", "ghi789"]

    def test_get_recent_commits_multiple(self, git_utils_instance):
        """Test getting multiple recent commits."""
        mock_commit_data1 = {
            "hash": "abc123",
            "author_name": "Test Author 1",
            "author_email": "test1@example.com",
            "commit_date": "2023-01-01T00:00:00+00:00",
            "message": "Test commit 1",
            "parent_hashes": "def456",
        }
        mock_commit_data2 = {
            "hash": "def456",
            "author_name": "Test Author 2",
            "author_email": "test2@example.com",
            "commit_date": "2023-01-02T00:00:00+00:00",
            "message": "Test commit 2",
            "parent_hashes": "",
        }

        output = json.dumps(mock_commit_data1) + "\n" + json.dumps(mock_commit_data2)

        with patch.object(git_utils_instance, "_run_git_command", return_value=output):
            result = git_utils_instance.get_recent_commits(2)

            assert len(result) == 2
            assert result[0]["hash"] == "abc123"
            assert result[1]["hash"] == "def456"
            assert result[1]["parent_hashes"] == []

    def test_get_recent_commits_invalid_json(self, git_utils_instance):
        """Test getting recent commits with invalid JSON."""
        with patch.object(
            git_utils_instance, "_run_git_command", return_value="invalid json"
        ):
            result = git_utils_instance.get_recent_commits(5)
            assert result == []

    def test_get_recent_commits_exception(self, git_utils_instance):
        """Test getting recent commits with exception."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("Git error")
        ):
            result = git_utils_instance.get_recent_commits(5)
            assert result == []

    def test_get_recent_commits_not_git_repo(self, git_utils_not_repo):
        """Test getting recent commits in non-Git repository."""
        result = git_utils_not_repo.get_recent_commits(5)
        assert result == []

    def test_get_commit_stats_success(self, git_utils_instance):
        """Test getting commit stats successfully."""
        files_output = "file1.py\nfile2.py\n"
        stats_output = " 2 files changed, 10 insertions(+), 5 deletions(-)"

        with patch.object(git_utils_instance, "_run_git_command") as mock_run:
            mock_run.side_effect = [files_output, stats_output]

            result = git_utils_instance.get_commit_stats("abc123")

            assert result["files_changed"] == ["file1.py", "file2.py"]
            assert result["lines_added"] == 10
            assert result["lines_deleted"] == 5

    def test_get_commit_stats_no_changes(self, git_utils_instance):
        """Test getting commit stats with no changes."""
        files_output = ""
        stats_output = " 0 files changed"

        with patch.object(git_utils_instance, "_run_git_command") as mock_run:
            mock_run.side_effect = [files_output, stats_output]

            result = git_utils_instance.get_commit_stats("abc123")

            assert result["files_changed"] == []
            assert result["lines_added"] == 0
            assert result["lines_deleted"] == 0

    def test_get_commit_stats_exception(self, git_utils_instance):
        """Test getting commit stats with exception."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("Git error")
        ):
            result = git_utils_instance.get_commit_stats("abc123")

            assert result["files_changed"] == []
            assert result["lines_added"] == 0
            assert result["lines_deleted"] == 0

    def test_get_commit_stats_not_git_repo(self, git_utils_not_repo):
        """Test getting commit stats in non-Git repository."""
        result = git_utils_not_repo.get_commit_stats("abc123")

        assert result["files_changed"] == []
        assert result["lines_added"] == 0
        assert result["lines_deleted"] == 0

    def test_get_commit_info_success(self, git_utils_instance):
        """Test getting commit info successfully."""
        mock_commit_data = {
            "hash": "abc123",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "commit_date": "2023-01-01T00:00:00+00:00",
            "message": "Test commit",
            "parent_hashes": "def456",
        }

        with patch.object(
            git_utils_instance,
            "_run_git_command",
            return_value=json.dumps(mock_commit_data),
        ):
            with patch.object(
                git_utils_instance,
                "get_commit_stats",
                return_value={
                    "files_changed": ["file1.py"],
                    "lines_added": 10,
                    "lines_deleted": 5,
                },
            ):
                result = git_utils_instance.get_commit_info("abc123")

                assert result["hash"] == "abc123"
                assert result["author_name"] == "Test Author"
                assert result["files_changed"] == ["file1.py"]
                assert result["lines_added"] == 10
                assert result["lines_deleted"] == 5

    def test_get_commit_info_empty_output(self, git_utils_instance):
        """Test getting commit info with empty output."""
        with patch.object(git_utils_instance, "_run_git_command", return_value=""):
            result = git_utils_instance.get_commit_info("abc123")
            assert result is None

    def test_get_commit_info_exception(self, git_utils_instance):
        """Test getting commit info with exception."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("Git error")
        ):
            result = git_utils_instance.get_commit_info("abc123")
            assert result is None

    def test_get_commit_info_not_git_repo(self, git_utils_not_repo):
        """Test getting commit info in non-Git repository."""
        result = git_utils_not_repo.get_commit_info("abc123")
        assert result is None

    def test_get_uncommitted_changes_success(self, git_utils_instance):
        """Test getting uncommitted changes successfully."""
        status_output = "M  modified_file.py\nA  new_file.py\nD  deleted_file.py"

        with patch.object(
            git_utils_instance, "_run_git_command", return_value=status_output
        ):
            result = git_utils_instance.get_uncommitted_changes()

            assert result["has_changes"] is True
            assert result["modified_files"] == ["modified_file.py"]
            assert result["added_files"] == ["new_file.py"]
            assert result["deleted_files"] == ["deleted_file.py"]

    def test_get_uncommitted_changes_no_changes(self, git_utils_instance):
        """Test getting uncommitted changes with no changes."""
        with patch.object(git_utils_instance, "_run_git_command", return_value=""):
            result = git_utils_instance.get_uncommitted_changes()

            assert result["has_changes"] is False
            assert result["modified_files"] == []
            assert result["added_files"] == []
            assert result["deleted_files"] == []

    def test_get_uncommitted_changes_exception(self, git_utils_instance):
        """Test getting uncommitted changes with exception."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("Git error")
        ):
            result = git_utils_instance.get_uncommitted_changes()

            assert result["has_changes"] is False
            assert result["modified_files"] == []
            assert result["added_files"] == []
            assert result["deleted_files"] == []

    def test_get_uncommitted_changes_not_git_repo(self, git_utils_not_repo):
        """Test getting uncommitted changes in non-Git repository."""
        result = git_utils_not_repo.get_uncommitted_changes()

        assert result["has_changes"] is False
        assert result["modified_files"] == []
        assert result["added_files"] == []
        assert result["deleted_files"] == []

    def test_create_commit_success(self, git_utils_instance):
        """Test creating commit successfully."""
        with patch.object(git_utils_instance, "_run_git_command") as mock_run:
            mock_run.side_effect = [None, None, "abc123"]  # add, commit, rev-parse

            result = git_utils_instance.create_commit("Test commit message")

            assert result == "abc123"
            assert mock_run.call_count == 3

    def test_create_commit_with_files(self, git_utils_instance):
        """Test creating commit with specific files."""
        with patch.object(git_utils_instance, "_run_git_command") as mock_run:
            mock_run.side_effect = [
                None,
                None,
                None,
                "abc123",
            ]  # add file1, add file2, commit, rev-parse

            result = git_utils_instance.create_commit(
                "Test commit", ["file1.py", "file2.py"]
            )

            assert result == "abc123"
            assert mock_run.call_count == 4  # 2 adds + commit + rev-parse

    def test_create_commit_exception(self, git_utils_instance):
        """Test creating commit with exception."""
        with patch.object(
            git_utils_instance, "_run_git_command", side_effect=Exception("Git error")
        ):
            result = git_utils_instance.create_commit("Test commit")
            assert result is None

    def test_create_commit_not_git_repo(self, git_utils_not_repo):
        """Test creating commit in non-Git repository."""
        result = git_utils_not_repo.create_commit("Test commit")
        assert result is None


class TestGlobalGitUtils:
    """Test cases for the global git utils instance."""

    def test_global_git_utils_instance(self):
        """Test that the global git utils instance exists."""
        assert isinstance(git_utils, GitUtils)

    def test_global_git_utils_methods(self):
        """Test that global git utils methods are callable."""
        # Test that methods exist and are callable
        assert hasattr(git_utils, "get_current_branch")
        assert hasattr(git_utils, "get_repository_name")
        assert hasattr(git_utils, "get_recent_commits")
        assert hasattr(git_utils, "get_commit_stats")
        assert hasattr(git_utils, "get_commit_info")
        assert hasattr(git_utils, "get_uncommitted_changes")
        assert hasattr(git_utils, "create_commit")
        assert hasattr(git_utils, "_run_git_command")
        assert hasattr(git_utils, "_validate_git_repo")

    def test_global_git_utils_attributes(self):
        """Test that global git utils has required attributes."""
        assert hasattr(git_utils, "repo_path")
        assert hasattr(git_utils, "_is_git_repo")
