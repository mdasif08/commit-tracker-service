#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
Sets up the PostgreSQL database and runs migrations
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from config import settings

async def setup_database():
    """Set up PostgreSQL database and run migrations."""
    
    print("🚀 Setting up PostgreSQL Database for Commit Tracker Service")
    print("=" * 60)
    
    # Database configuration
    db_config = {
        'user': 'postgres',
        'password': 'password',
        'host': 'localhost',
        'port': 5432,
        'database': 'postgres'  # Connect to default database first
    }
    
    try:
        # Connect to PostgreSQL server
        print("📡 Connecting to PostgreSQL server...")
        conn = await asyncpg.connect(**db_config)
        
        # Check if database exists
        print("🔍 Checking if database exists...")
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            'commit_tracker'
        )
        
        if not result:
            print("📊 Creating database 'commit_tracker'...")
            await conn.execute("CREATE DATABASE commit_tracker")
            print("✅ Database created successfully!")
        else:
            print("✅ Database 'commit_tracker' already exists!")
        
        await conn.close()
        
        # Connect to the commit_tracker database
        db_config['database'] = 'commit_tracker'
        conn = await asyncpg.connect(**db_config)
        
        # Check if tables exist
        print("🔍 Checking if tables exist...")
        result = await conn.fetchval(
            "SELECT 1 FROM information_schema.tables WHERE table_name = 'commits'"
        )
        
        if not result:
            print("📋 Tables don't exist. Running migrations...")
            await conn.close()
            
            # Run Alembic migrations
            import subprocess
            result = subprocess.run([
                'alembic', 'upgrade', 'head'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Migrations completed successfully!")
            else:
                print(f"❌ Migration failed: {result.stderr}")
                return False
        else:
            print("✅ Tables already exist!")
            await conn.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("📊 Database: commit_tracker")
        print("🔗 Connection: postgresql+asyncpg://postgres:password@localhost:5432/commit_tracker")
        print("📋 Tables: commits, commit_files")
        print("🔍 Features: Full-text search, Materialized views, Indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if postgres user exists with password 'password'")
        print("3. Ensure port 5432 is available")
        print("4. Install PostgreSQL: https://www.postgresql.org/download/")
        return False

async def test_connection():
    """Test database connection."""
    
    print("\n🧪 Testing database connection...")
    
    try:
        conn = await asyncpg.connect(
            'postgresql://postgres:password@localhost:5432/commit_tracker'
        )
        
        # Test basic query
        result = await conn.fetchval("SELECT COUNT(*) FROM commits")
        print(f"✅ Connection successful! Found {result} commits in database.")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def main():
    """Main function."""
    
    print("🔄 PostgreSQL Database Setup for Commit Tracker Service")
    print("=" * 60)
    
    # Setup database
    success = await setup_database()
    
    if success:
        # Test connection
        await test_connection()
        
        print("\n🎯 Next steps:")
        print("1. Start the application: python -m uvicorn src.main:app --host 127.0.0.1 --port 8001")
        print("2. Test the API: curl http://127.0.0.1:8001/health")
        print("3. View API docs: http://127.0.0.1:8001/docs")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())


