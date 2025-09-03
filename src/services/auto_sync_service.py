#!/usr/bin/env python3
"""
Auto Sync Service for Commit Tracker
Handles automatic synchronization of Git commits to the database.
"""

import asyncio
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, Any

from src.database import get_db_service
from src.utils.git_utils import GitUtils
from src.models import CommitSource

logger = structlog.get_logger(__name__)

class AutoSyncService:
    """Service for automatically syncing Git commits to the database."""
    
    def __init__(self, repository_name: str = "commit-tracker-service"):
        self.repository_name = repository_name
        self.git_utils = GitUtils()
        self.db_service = None
        self.is_running = False
        
    async def start(self):
        """Start the auto-sync service."""
        if self.is_running:
            logger.warning("Auto-sync service is already running")
            return
            
        self.is_running = True
        self.db_service = await get_db_service()
        logger.info("Auto-sync service started")
        
        try:
            while self.is_running:
                await self._sync_commits()
                await asyncio.sleep(30)  # Sync every 30 seconds
        except Exception as e:
            logger.error("Auto-sync service error", error=str(e))
            self.is_running = False
        finally:
            if self.db_service:
                await self.db_service.close()
    
    async def stop(self):
        """Stop the auto-sync service."""
        self.is_running = False
        logger.info("Auto-sync service stopped")
    
    async def _sync_commits(self):
        """Sync commits from Git repository to database."""
        try:
            # Get recent commits from Git
            commits = self.git_utils.get_recent_commits()
            
            if not commits:
                logger.info("No new commits found to sync")
                return
            
            logger.info(f"Found {len(commits)} commits to sync")
            
            for commit_data in commits:
                try:
                    # Check if commit already exists
                    existing_commit = await self.db_service.get_commit_metadata_by_hash(commit_data["hash"])
                    if existing_commit:
                        logger.debug(f"Commit {commit_data['hash'][:8]} already exists, skipping")
                        continue
                    
                    # Get detailed commit statistics
                    stats_data = self.git_utils.get_commit_stats(commit_data["hash"])
                    
                    # Prepare file details for storage
                    file_details = []
                    if stats_data.get('files'):
                        for file_info in stats_data['files']:
                            file_detail = {
                                'file_path': file_info.get('file_path', ''),
                                'file_name': file_info.get('file_name', ''),
                                'file_extension': file_info.get('file_extension', ''),
                                'change_type': file_info.get('change_type', 'modified'),
                                'lines_added': file_info.get('lines_added', 0),
                                'lines_deleted': file_info.get('lines_deleted', 0),
                                'file_size_before': file_info.get('file_size_before'),
                                'file_size_after': file_info.get('file_size_after'),
                                'diff_content': file_info.get('diff_content', ''),
                                'language_detected': self._detect_language(file_info.get('file_extension', '')),
                                'complexity_score': file_info.get('complexity_score', 0),
                                'security_risk_level': file_info.get('security_risk_level', 'low')
                            }
                            file_details.append(file_detail)
                    
                    # Prepare commit record
                    commit_record = {
                        'commit_hash': commit_data["hash"],
                        'repository_name': self.repository_name,
                        'author_name': commit_data["author_name"],
                        'author_email': commit_data["author_email"],
                        'commit_message': commit_data["message"],
                        'commit_date': datetime.fromisoformat(commit_data["commit_date"].replace('Z', '+00:00')),
                        'source_type': CommitSource.LOCAL,
                        'branch_name': commit_data.get("branch_name", "main"),
                        'files_changed': stats_data.get('files', []),
                        'lines_added': stats_data.get('lines_added', 0),
                        'lines_deleted': stats_data.get('lines_deleted', 0),
                        'diff_content': stats_data.get('diff_content', ''),
                        'parent_commits': commit_data.get("parent_hashes", [])  # This will be stored as JSON
                    }
                    
                    # Store commit with file details
                    # Convert parent_commits list to JSON string if it's a list
                    if isinstance(commit_record['parent_commits'], list):
                        commit_record['parent_commits'] = json.dumps(commit_record['parent_commits'])
                    
                    # Convert file_details to file_diffs format expected by database
                    file_diffs = {}
                    for file_detail in file_details:
                        filename = file_detail.get('file_name', 'unknown')
                        file_diffs[filename] = {
                            'status': file_detail.get('change_type', 'modified'),
                            'additions': file_detail.get('lines_added', []),
                            'deletions': file_detail.get('lines_deleted', []),
                            'diff_content': file_detail.get('diff_content', ''),
                            'size_before': file_detail.get('file_size_before'),
                            'size_after': file_detail.get('file_size_after'),
                            'complexity_score': file_detail.get('complexity_score', 0),
                            'security_risk_level': file_detail.get('security_risk_level', 'low')
                        }
                    
                    commit_record['file_diffs'] = file_diffs
                    commit_id = await self.db_service.store_commit(commit_record)
                    
                    logger.info(
                        f"Synced commit {commit_data['hash'][:8]}: "
                        f"{commit_data['message'][:50]}... "
                        f"(files: {len(file_details)})"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to sync commit {commit_data['hash'][:8]}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error("Failed to sync commits", error=str(e))
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'cs': 'C#',
            'php': 'PHP',
            'rb': 'Ruby',
            'go': 'Go',
            'rs': 'Rust',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'html': 'HTML',
            'css': 'CSS',
            'sql': 'SQL',
            'json': 'JSON',
            'xml': 'XML',
            'yaml': 'YAML',
            'yml': 'YAML',
            'md': 'Markdown',
            'txt': 'Text'
        }
        return language_map.get(file_extension.lower(), 'Unknown')

    async def manual_sync(self) -> Dict[str, Any]:
        """Perform manual synchronization."""
        try:
            if not self.db_service:
                self.db_service = await get_db_service()
            
            await self._sync_commits()
            return {
                "success": True,
                "message": "Manual sync completed successfully"
            }
        except Exception as e:
            logger.error("Manual sync failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def get_commit_history(self, limit: int = 50, offset: int = 0, author: str = None, branch: str = None) -> Dict[str, Any]:
        """Get commit history from database."""
        try:
            if not self.db_service:
                self.db_service = await get_db_service()
            
            commits = await self.db_service.get_commits(
                limit=limit,
                offset=offset,
                author=author,
                branch=branch
            )
            
            total_count = await self.db_service.get_commit_count(
                author=author,
                branch=branch
            )
            
            return {
                "commits": commits,
                "total_count": total_count,
                "page": (offset // limit) + 1,
                "page_size": limit
            }
        except Exception as e:
            logger.error("Failed to get commit history", error=str(e))
            raise

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return {
            "is_running": self.is_running,
            "repository_name": self.repository_name,
            "status": "running" if self.is_running else "stopped"
        }

# Create singleton instance
auto_sync_service = AutoSyncService()

async def start_auto_sync():
    """Start the auto-sync service."""
    await auto_sync_service.start()

async def stop_auto_sync():
    """Stop the auto-sync service."""
    await auto_sync_service.stop()
