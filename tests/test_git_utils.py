#!/usr/bin/env python3
"""Test script to verify git_utils is working correctly."""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.git_utils import git_utils, GitUtils

def test_git_utils():
    """Test git_utils functionality."""
    print("=== Git Utils Test ===")
    print(f"Repository path: {git_utils.repo_path}")
    print(f"Is Git repository: {git_utils._is_git_repo}")
    
    # Mock all Git commands for testing
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'commit-tracker-service\n'
        repo_name = git_utils.get_repository_name()
        print(f"Repository name: {repo_name}")
        
        mock_run.return_value.stdout = 'main\n'
        branch = git_utils.get_current_branch()
        print(f"Current branch: {branch}")
        
        mock_run.return_value.stdout = '[]'
        commits = git_utils.get_recent_commits(5)
        print(f"Recent commits count: {len(commits)}")
        
        mock_run.return_value.stdout = ''
        status = git_utils.get_uncommitted_changes()
        print(f"\n=== Git Status ===")
        print(f"Has changes: {status['has_changes']}")
        print(f"Modified files: {status['modified_files']}") 

class TestGitUtils:
    """Test cases for GitUtils class."""

    @pytest.fixture
    def git_utils_instance(self):
        """Create a GitUtils instance for testing."""
        return GitUtils()

    def test_git_utils_initialization(self, git_utils_instance):
        """Test GitUtils initialization."""
        assert git_utils_instance is not None
        assert hasattr(git_utils_instance, 'repo_path')
        assert hasattr(git_utils_instance, '_is_git_repo')

    def test_get_repository_name(self, git_utils_instance):
        """Test getting repository name."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'commit-tracker-service\n'
            result = git_utils_instance.get_repository_name()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_current_branch(self, git_utils_instance):
        """Test getting current branch."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'main\n'
            result = git_utils_instance.get_current_branch()
            assert isinstance(result, str)
            assert len(result) > 0

    def test_get_recent_commits(self, git_utils_instance):
        """Test getting recent commits."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'
            result = git_utils_instance.get_recent_commits(5)
            assert isinstance(result, list)

    def test_get_commit_stats(self, git_utils_instance):
        """Test getting commit statistics."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{}'
            result = git_utils_instance.get_commit_stats('abc123')
            assert isinstance(result, dict)

    def test_get_uncommitted_changes(self, git_utils_instance):
        """Test getting uncommitted changes."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = ''
            result = git_utils_instance.get_uncommitted_changes()
            assert isinstance(result, dict)
            assert 'has_changes' in result
            assert 'modified_files' in result
            assert 'added_files' in result
            assert 'deleted_files' in result

    def test_get_commit_diff(self, git_utils_instance):
        """Test getting commit diff."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{}'
            result = git_utils_instance.get_commit_diff('abc123')
            assert isinstance(result, dict)

    def test_get_git_log(self, git_utils_instance):
        """Test getting git log."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'
            result = git_utils_instance.get_git_log(5)
            assert isinstance(result, list)

    def test_get_file_history(self, git_utils_instance):
        """Test getting file history."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '[]'
            result = git_utils_instance.get_file_history('test.py')
            assert isinstance(result, list)

    def test_get_branch_list(self, git_utils_instance):
        """Test getting branch list."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '["main"]'
            result = git_utils_instance.get_branch_list()
            assert isinstance(result, list)

    def test_get_remote_info(self, git_utils_instance):
        """Test getting remote info."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{}'
            result = git_utils_instance.get_remote_info()
            assert isinstance(result, dict)

    def test_get_git_config(self, git_utils_instance):
        """Test getting git config."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = 'Test User\n'
            result = git_utils_instance.get_git_config('user.name')
            assert isinstance(result, str)

    def test_get_commit_info(self, git_utils_instance):
        """Test getting commit info."""
        # Mock the git command to avoid actual git execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b'{"hash":"abc123","author_name":"Test Author","author_email":"test@example.com","commit_date":"2023-01-01T00:00:00Z","message":"Test commit","parent_hashes":""}'
            
            result = git_utils_instance.get_commit_info('abc123')
            assert isinstance(result, dict)
            assert result['hash'] == 'abc123'

    def test_is_git_repo(self, git_utils_instance):
        """Test git repository detection."""
        # This test depends on the actual environment
        assert isinstance(git_utils_instance._is_git_repo, bool)

if __name__ == "__main__":
    test_git_utils()
