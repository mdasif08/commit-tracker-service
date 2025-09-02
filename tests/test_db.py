#!/usr/bin/env python3
"""
Simple test script to check existing database content
"""

import asyncio
import sys
import os

# Add src to path (go up one level from tests folder)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

async def test_db():
    """Test database connection and content."""
    try:
        from database import get_db_service
        
        print("✅ Import successful")
        
        # Get database service
        db_service = await get_db_service()
        print("✅ Database service created")
        
        # Check health
        health = await db_service.health_check()
        print(f"✅ Database health: {health}")
        
        # Get commits
        commits = await db_service.get_commits(limit=10, offset=0)
        print(f"✅ Found {len(commits)} commits")
        
        for i, commit in enumerate(commits[:3]):
            print(f"  {i+1}. {commit['commit_hash'][:8]}: {commit['commit_message'][:50]}...")
        
        # Get total count
        total = await db_service.get_commit_count()
        print(f"✅ Total commits: {total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())
