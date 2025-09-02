#!/usr/bin/env python3
"""
Auto Sync Service for Commit Tracker
Handles automatic synchronization of Git commits to the database.
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import structlog
from src.database import get_db_service
from src.utils.git_utils import GitUtils

logger = structlog.get_logger(__name__)

class AutoSyncService:
    """Service for automatic commit synchronization."""
    
    def __init__(self):
        self.sync_task = None
        self.is_running = False
        self.sync_interval = 30  # Default 30 seconds
        self.last_sync_time = None
        self.sync_count = 0
        self.error_count = 0
        
    async def start_auto_sync(self, interval: int = 30) -> bool:
        """Start automatic synchronization."""
        try:
            if self.is_running:
                logger.warning("Auto-sync is already running")
                return True
                
            self.sync_interval = interval
            self.is_running = True
            
            # Start the sync task
            self.sync_task = asyncio.create_task(self._sync_loop())
            logger.info("Auto-sync started", interval=interval)
            return True
            
        except Exception as e:
            logger.error("Failed to start auto-sync", error=str(e))
            self.is_running = False
            return False
    
    async def stop_auto_sync(self) -> bool:
        """Stop automatic synchronization."""
        try:
            if not self.is_running:
                logger.warning("Auto-sync is not running")
                return True
                
            self.is_running = False
            
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
                    
            logger.info("Auto-sync stopped")
            return True
            
        except Exception as e:
            logger.error("Failed to stop auto-sync", error=str(e))
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return {
            "is_running": self.is_running,
            "sync_interval": self.sync_interval,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_count": self.sync_count,
            "error_count": self.error_count,
            "status": "running" if self.is_running else "stopped"
        }
    
    async def manual_sync(self) -> Dict[str, Any]:
        """Perform manual synchronization."""
        try:
            logger.info("Starting manual sync")
            result = await self._sync_commits()
            
            if result["success"]:
                logger.info("Manual sync completed", commits_synced=result["commits_synced"])
            else:
                logger.error("Manual sync failed", error=result["error"])
                
            return result
            
        except Exception as e:
            logger.error("Manual sync error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "commits_synced": 0
            }
    
    async def get_commit_history(
        self, 
        limit: int = 50, 
        offset: int = 0, 
        author: Optional[str] = None, 
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get commit history from database."""
        try:
            db_service = await get_db_service()
            
            # Build query parameters
            query_params = {
                "limit": limit,
                "offset": offset
            }
            
            if author:
                query_params["author"] = author
            if branch:
                query_params["branch"] = branch
            
            commits = await db_service.get_commits(**query_params)
            
            # For count, only pass author and branch filters, not pagination
            count_params = {}
            if author:
                count_params["author"] = author
            if branch:
                count_params["branch"] = branch
            
            total_count = await db_service.get_commit_count(**count_params)
            
            return {
                "commits": commits,
                "total_count": total_count,
                "page": (offset // limit) + 1,
                "page_size": limit
            }
            
        except Exception as e:
            logger.error("Failed to get commit history", error=str(e))
            raise
    
    async def get_commit_statistics(self) -> Dict[str, Any]:
        """Get comprehensive commit statistics."""
        try:
            db_service = await get_db_service()
            
            # Get various statistics
            total_commits = await db_service.get_commit_count()
            
            # Get commits by author
            author_stats = await db_service.get_commits_by_author()
            
            # Get commits by date (last 30 days)
            date_stats = await db_service.get_commits_by_date(days=30)
            
            # Get file change statistics
            file_stats = await db_service.get_file_change_stats()
            
            return {
                "total_commits": total_commits,
                "authors": author_stats,
                "recent_activity": date_stats,
                "file_statistics": file_stats,
                "sync_status": self.get_sync_status()
            }
            
        except Exception as e:
            logger.error("Failed to get commit statistics", error=str(e))
            raise
    
    async def _sync_loop(self):
        """Main sync loop."""
        while self.is_running:
            try:
                await self._sync_commits()
                self.last_sync_time = datetime.now(timezone.utc)
                self.sync_count += 1
                
                # Wait for next sync
                await asyncio.sleep(self.sync_interval)
                
            except asyncio.CancelledError:
                logger.info("Sync loop cancelled")
                break
            except Exception as e:
                logger.error("Sync loop error", error=str(e))
                self.error_count += 1
                await asyncio.sleep(5)  # Wait before retry
    
    async def _sync_commits(self) -> Dict[str, Any]:
        """Sync new commits to database."""
        try:
            # Get Git utils
            git_utils = GitUtils()
            
            # Get recent commits from Git
            recent_commits = git_utils.get_recent_commits(count=10)
            
            if not recent_commits:
                return {"success": True, "commits_synced": 0, "message": "No new commits"}
            
            # Get database service
            db_service = await get_db_service()
            
            synced_count = 0
            
            for commit_data in recent_commits:
                commit_hash = commit_data["hash"]
                
                # Check if commit already exists
                existing = await db_service.get_commit_metadata_by_hash(commit_hash)
                if existing:
                    continue
                
                # Get detailed diff information
                diff_data = git_utils.get_commit_diff(commit_hash)
                
                # Prepare commit record
                commit_record = {
                    'commit_hash': commit_hash,
                    'repository_name': git_utils.get_repository_name(),
                    'author_name': commit_data["author_name"],
                    'author_email': commit_data["author_email"],
                    'commit_message': commit_data["message"],
                    'commit_date': commit_data["date"],
                    'source_type': 'LOCAL',
                    'branch_name': git_utils.get_current_branch(),
                    'files_changed': list(diff_data.get('file_diffs', {}).keys()),
                    'lines_added': sum(len(diff_data.get('file_diffs', {}).get(f, {}).get('additions', [])) for f in diff_data.get('file_diffs', {})),
                    'lines_deleted': sum(len(diff_data.get('file_diffs', {}).get(f, {}).get('deletions', [])) for f in diff_data.get('file_diffs', {})),
                    'parent_commits': commit_data.get("parent_hashes", []),
                    'status': 'PROCESSED',
                    'metadata': {
                        'synced_from_git': True,
                        'sync_date': datetime.now().isoformat(),
                        'auto_synced': True
                    },
                    'diff_content': diff_data.get('diff_content', ''),
                    'file_diffs': diff_data.get('file_diffs', {}),
                    'diff_hash': f"git_{commit_hash}"
                }
                
                # Store in database
                await db_service.store_commit_with_diff(commit_record)
                synced_count += 1
                
                logger.info("Synced commit", 
                           hash=commit_hash[:8], 
                           message=commit_data["message"][:50])
            
            return {
                "success": True,
                "commits_synced": synced_count,
                "message": f"Synced {synced_count} new commits"
            }
            
        except Exception as e:
            logger.error("Failed to sync commits", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "commits_synced": 0
            }

# Create singleton instance
auto_sync_service = AutoSyncService()
