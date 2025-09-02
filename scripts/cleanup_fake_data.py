#!/usr/bin/env python3
"""
Script to clean up fake test data from the database.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

async def cleanup_fake_data():
    """Remove fake test data from the database."""
    try:
        from src.database import get_db_service
        
        print("🔍 Connecting to database...")
        db_service = await get_db_service()
        
        print("🔍 Checking for fake test data...")
        # Get all commits to identify fake ones
        commits = await db_service.get_commits(limit=100, offset=0)
        
        fake_commits = []
        for commit in commits:
            # Identify fake commits by suspicious patterns
            if (commit.get('author_name') == 'Test User' or 
                commit.get('commit_hash') == 'abc1234567890abcdef1234567890abcdef1234' or
                'test' in commit.get('commit_message', '').lower() and commit.get('author_name') != 'mdasif08'):
                fake_commits.append(commit)
        
        if not fake_commits:
            print("✅ No fake test data found!")
            return
        
        print(f"🚨 Found {len(fake_commits)} fake commits:")
        for commit in fake_commits:
            print(f"   - {commit.get('commit_hash', '')[:8]}: {commit.get('author_name', '')} - {commit.get('commit_message', '')}")
        
        # Remove fake commits
        print("\n🗑️  Removing fake commits...")
        for commit in fake_commits:
            commit_hash = commit.get('commit_hash')
            if commit_hash:
                print(f"   - Deleting commit {commit_hash[:8]} and associated files...")
                success = await db_service.delete_commit(commit_hash)
                if success:
                    print(f"   ✅ Successfully deleted commit {commit_hash[:8]}")
                else:
                    print(f"   ❌ Failed to delete commit {commit_hash[:8]}")
        
        print("\n✅ Fake data cleanup completed!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(cleanup_fake_data())
