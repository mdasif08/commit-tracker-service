import subprocess
import structlog
from typing import List, Dict, Any, Optional
import os
import json
import re

logger = structlog.get_logger(__name__)

class GitUtils:
    """Utility class for Git operations and local commit tracking."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)
        self._is_git_repo = self._validate_git_repo()

    def _validate_git_repo(self) -> bool:
        """Validate that the path is a Git repository."""
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            logger.warning(f"Not a Git repository: {self.repo_path}")
            return False
        return True

    def _run_git_command(self, command: List[str]) -> str:
        """Run a Git command and return the output."""
        if not self._is_git_repo:
            raise ValueError("Not a Git repository")

        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error("Git command failed", command=command, error=e.stderr)
            raise
        except FileNotFoundError:
            logger.error("Git not found on system")
            raise ValueError("Git is not installed on this system")

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        if not self._is_git_repo:
            return "unknown"
        return self._run_git_command(["branch", "--show-current"])

    def get_repository_name(self) -> str:
        """Get the repository name from remote origin."""
        if not self._is_git_repo:
            return os.path.basename(self.repo_path)

        try:
            remote_url = self._run_git_command(["config", "--get", "remote.origin.url"])
            # Extract repo name from URL
            if remote_url.endswith(".git"):
                remote_url = remote_url[:-4]
            return remote_url.split("/")[-1]
        except Exception:
            # Fallback to directory name
            return os.path.basename(self.repo_path)

    def get_recent_commits(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits with detailed information."""
        if not self._is_git_repo:
            return []

        try:
            # Get commit information in JSON format
            format_str = (
                '{"hash":"%H","author_name":"%an","author_email":"%ae",'
                '"commit_date":"%aI","message":"%s","parent_hashes":"%P"}'
            )

            output = self._run_git_command(
                ["log", f"-{count}", "--pretty=format:" + format_str, "--no-merges"]
            )

            commits = []
            for line in output.split("\n"):
                if line.strip():
                    try:
                        commit_data = json.loads(line)
                        # Parse parent hashes
                        parent_hashes = (
                            commit_data["parent_hashes"].split()
                            if commit_data["parent_hashes"]
                            else []
                        )

                        commits.append(
                            {
                                "hash": commit_data["hash"],
                                    "author_name": commit_data["author_name"],
                                        "author_email": commit_data["author_email"],
                                        "commit_date": commit_data["commit_date"],
                                        "message": commit_data["message"],
                                        "parent_hashes": parent_hashes,
                            }
                        )
                    except json.JSONDecodeError as e:
                        logger.warning(
                                       "Failed to parse commit data", line=line, error=str(e)
                        )
                        continue

            return commits

        except Exception as e:
            logger.error("Failed to get recent commits", error=str(e))
            return []

    def get_commit_stats(self, commit_hash: str) -> Dict[str, Any]:
        """Get detailed statistics for a specific commit."""
        if not self._is_git_repo:
            return {"files_changed": [], "lines_added": 0, "lines_deleted": 0}

        try:
            # Get files changed
            files_output = self._run_git_command(
                ["show", "--name-only", "--pretty=format:", commit_hash]
            )

            files_changed = [f.strip() for f in files_output.split("\n") if f.strip()]

            # Get line statistics
            stats_output = self._run_git_command(
                ["show", "--stat", "--pretty=format:", commit_hash]
            )

            lines_added = 0
            lines_deleted = 0

            # Parse stat output
            for line in stats_output.split("\n"):
                if "insertions" in line and "deletions" in line:
                    parts = line.split(",")
                    for part in parts:
                        part = part.strip()
                        if "insertion" in part:
                            lines_added = int(part.split()[0])
                        elif "deletion" in part:
                            lines_deleted = int(part.split()[0])
                    break

            return {
                "files_changed": files_changed,
                    "lines_added": lines_added,
                        "lines_deleted": lines_deleted,
            }

        except Exception as e:
            logger.error(
                         "Failed to get commit stats", commit_hash=commit_hash[:8], error=str(e)
            )
            return {"files_changed": [], "lines_added": 0, "lines_deleted": 0}

    def get_commit_info(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific commit."""
        if not self._is_git_repo:
            return None

        try:
            # Get commit information in JSON format
            format_str = (
                '{"hash":"%H","author_name":"%an","author_email":"%ae",'
                '"commit_date":"%aI","message":"%s","parent_hashes":"%P"}'
            )

            output = self._run_git_command(
                ["show", "--pretty=format:" + format_str, "--no-patch", commit_hash]
            )

            if not output.strip():
                return None

            commit_data = json.loads(output)
            parent_hashes = (
                commit_data["parent_hashes"].split()
                if commit_data["parent_hashes"]
                else []
            )

            # Get stats
            stats = self.get_commit_stats(commit_hash)

            return {
                "hash": commit_data["hash"],
                    "author_name": commit_data["author_name"],
                        "author_email": commit_data["author_email"],
                        "commit_date": commit_data["commit_date"],
                        "message": commit_data["message"],
                        "parent_hashes": parent_hashes,
                        "files_changed": stats["files_changed"],
                        "lines_added": stats["lines_added"],
                        "lines_deleted": stats["lines_deleted"],
            }

        except Exception as e:
            logger.error(
                         "Failed to get commit info", commit_hash=commit_hash[:8], error=str(e)
            )
            return None

    def get_uncommitted_changes(self) -> Dict[str, Any]:
        """Get information about uncommitted changes."""
        if not self._is_git_repo:
            return {
                "has_changes": False,
                    "modified_files": [],
                        "added_files": [],
                        "deleted_files": [],
            }

        try:
            # Check if there are any changes
            status_output = self._run_git_command(["status", "--porcelain"])

            if not status_output.strip():
                return {
                    "has_changes": False,
                        "modified_files": [],
                            "added_files": [],
                            "deleted_files": [],
                }

            modified_files = []
            added_files = []
            deleted_files = []

            for line in status_output.split("\n"):
                if line.strip():
                    status = line[:2]
                    filename = line[3:]

                    if status.startswith("M"):
                        modified_files.append(filename)
                    elif status.startswith("A"):
                        added_files.append(filename)
                    elif status.startswith("D"):
                        deleted_files.append(filename)

            return {
                "has_changes": True,
                    "modified_files": modified_files,
                        "added_files": added_files,
                        "deleted_files": deleted_files,
            }

        except Exception as e:
            logger.error("Failed to get uncommitted changes", error=str(e))
            return {
                "has_changes": False,
                    "modified_files": [],
                        "added_files": [],
                        "deleted_files": [],
            }

    def create_commit(
        self, message: str, files: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create a new commit."""
        if not self._is_git_repo:
            return None

        try:
            # Add files if specified
            if files:
                for file in files:
                    self._run_git_command(["add", file])
            else:
                # Add all changes
                self._run_git_command(["add", "."])

            # Create commit
            self._run_git_command(["commit", "-m", message])

            # Get the commit hash
            return self._run_git_command(["rev-parse", "HEAD"])

        except Exception as e:
            logger.error("Failed to create commit", error=str(e))
            return None

    def get_commit_diff(self, commit_hash: str) -> Dict[str, Any]:
        """Get the actual diff content for a commit."""
        try:
            # Get raw diff output
            diff_output = self._run_git_command([
                "show", "--unified=3", "--no-prefix", commit_hash
            ])

            # Get structured diff data
            file_diffs = self._parse_file_diffs(commit_hash)

            return {
                "diff_content": diff_output,
                    "file_diffs": file_diffs
            }
        except Exception as e:
            logger.error(f"Failed to get diff for {commit_hash}", error=str(e))
            return {"diff_content": "", "file_diffs": {}}

    def _parse_file_diffs(self, commit_hash: str) -> Dict[str, Any]:
        """Parse file-by-file diff information with detailed analysis."""
        try:
            # Get file changes with status
            files_output = self._run_git_command([
                "show", "--name-status", "--pretty=format:", commit_hash
            ])

            file_diffs = {}
            for line in files_output.split("\n"):
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]

                        # Get file-specific diff
                        file_diff = self._get_file_diff(commit_hash, filename)

                        file_diffs[filename] = {
                            "status": self._map_git_status(status),
                                "additions": file_diff.get("additions", []),
                                    "deletions": file_diff.get("deletions", []),
                                    "modifications": file_diff.get("modifications", []),
                                    "diff_content": file_diff.get("diff_content", ""),
                                    "size_before": file_diff.get("size_before"),
                                    "size_after": file_diff.get("size_after"),
                                    "complexity_score": self._calculate_complexity(file_diff.get("diff_content", "")),
                                    "security_risk_level": self._assess_security_risk(filename, file_diff.get("diff_content", ""))
                        }

            return file_diffs
        except Exception as e:
            logger.error(f"Failed to parse file diffs for {commit_hash}", error=str(e))
            return {}

    def _get_file_diff(self, commit_hash: str, filename: str) -> Dict[str, Any]:
        """Get detailed diff for a specific file."""
        try:
            # Get file-specific diff
            diff_output = self._run_git_command([
                "show", "--unified=3", "--no-prefix", commit_hash, "--", filename
            ])

            additions = []
            deletions = []
            modifications = []

            for line in diff_output.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    additions.append(line)
                elif line.startswith('-') and not line.startswith('---'):
                    deletions.append(line)
                elif line.startswith('@@'):
                    modifications.append(line)

            return {
                "diff_content": diff_output,
                    "additions": additions,
                        "deletions": deletions,
                        "modifications": modifications
            }
        except Exception as e:
            logger.error(f"Failed to get file diff for {filename}", error=str(e))
            return {"diff_content": "", "additions": [], "deletions": [], "modifications": []}

    def _map_git_status(self, git_status: str) -> str:
        """Map git status to our status format."""
        status_map = {
            'A': 'added',
            'M': 'modified',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied'
        }
        return status_map.get(git_status, 'modified')

    def _calculate_complexity(self, diff_content: str) -> int:
        """Calculate complexity score based on diff content."""
        if not diff_content:
            return 0

        complexity = 0
        lines = diff_content.split('\n')

        for line in lines:
            if line.startswith('+') or line.startswith('-'):
                # Count nested structures
                if 'for ' in line and ' in ' in line:
                    complexity += 2
                if 'if ' in line and ':' in line:
                    complexity += 1
                if 'def ' in line:
                    complexity += 1
                if 'class ' in line:
                    complexity += 2

        return min(complexity, 10)  # Cap at 10

    def _assess_security_risk(self, filename: str, diff_content: str) -> str:
        """Assess security risk level based on file and content."""
        if not diff_content:
            return 'low'

        # Check file extension
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
        high_risk_extensions = ['py', 'js', 'php', 'java', 'sql']

        if file_extension in high_risk_extensions:
            # Check for security-sensitive patterns
            security_patterns = [
                r'password.*=',
                r'api_key.*=',
                r'secret.*=',
                r'SELECT.*WHERE.*\$\{',
                r'INSERT INTO.*\$\{',
                r'exec\(',
                r'eval\(',
                r'os\.system\('
            ]

            for pattern in security_patterns:
                if re.search(pattern, diff_content, re.IGNORECASE):
                    return 'high'

        return 'low'

# Global git utils instance
git_utils = GitUtils()
