#!/usr/bin/env python3
"""
Automatic commit sync script for Git hooks.
This script automatically syncs new commits to the database.
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime
from src.database import get_db_service
from src.utils.git_utils import GitUtils

async def auto_sync_latest_commit():
    """Automatically sync the most recent commit to the database."""
    try:
        # Get the latest commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        commit_hash = result.stdout.strip()
        
        # Get commit details
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"],
            capture_output=True, text=True, check=True, encoding='utf-8'
        )
        
        line = result.stdout.strip()
        if not line:
            print("❌ No commit found")
            return
        
        parts = line.split('|')
        if len(parts) != 5:
            print("❌ Invalid commit format")
            return
        
        commit_hash, author_name, author_email, date_str, message = parts
        
        # Get database service
        db_service = await get_db_service()
        
        # Check if commit already exists
        existing_commit = await db_service.get_commit_metadata_by_hash(commit_hash)
        if existing_commit:
            print(f"✅ Commit {commit_hash[:8]} already exists in database")
            return
        
        # Get detailed commit information including diff
        git_utils = GitUtils()
        diff_data = git_utils.get_commit_diff(commit_hash)
        
        # Prepare commit data for database
        commit_record = {
            'commit_hash': commit_hash,
            'repository_name': 'commit-tracker-service',
            'author_name': author_name,
            'author_email': author_email,
            'commit_message': message,
            'commit_date': datetime.fromisoformat(date_str.replace('Z', '+00:00')),
            'source_type': 'LOCAL',
            'branch_name': 'main',
            'files_changed': list(diff_data.get('file_diffs', {}).keys()),
            'lines_added': sum(len(diff_data.get('file_diffs', {}).get(f, {}).get('additions', [])) for f in diff_data.get('file_diffs', {})),
            'lines_deleted': sum(len(diff_data.get('file_diffs', {}).get(f, {}).get('deletions', [])) for f in diff_data.get('file_diffs', {})),
            'parent_commits': [],
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
        commit_id = await db_service.store_commit_with_diff(commit_record)
        print(f"✅ Auto-synced commit: {commit_hash[:8]} - {message}")
        
    except Exception as e:
        print(f"❌ Failed to auto-sync commit: {e}")

if __name__ == "__main__":
    asyncio.run(auto_sync_latest_commit())
