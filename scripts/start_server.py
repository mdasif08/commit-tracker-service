#!/usr/bin/env python3
"""
Clean Server Startup Script
Handles all import errors and starts the server without issues
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def install_dependencies():
    """Install/upgrade required dependencies."""
    print("🔧 Installing/upgrading dependencies...")
    
    # Update bcrypt to fix import issues
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "bcrypt==4.0.1"], check=True)
    
    # Install other dependencies
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    print("✅ Dependencies installed successfully!")

def check_database():
    """Check if database is accessible."""
    print("🗄️ Checking database connection...")
    
    try:
        import asyncpg
        conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/commit_tracker')
        result = await conn.fetchval("SELECT COUNT(*) FROM commits")
        await conn.close()
        print(f"✅ Database connected! Found {result} commits.")
        return True
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        print("📋 Using SQLite fallback...")
        return False

def start_server():
    """Start the server with proper error handling."""
    print("🚀 Starting Commit Tracker Service...")
    
    # Set environment variables
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./commit_tracker.db"
    
    # Start server with proper host and port
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "src.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8001",
        "--reload"
    ]
    
    print(f"🎯 Starting server with command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")

async def main():
    """Main function."""
    print("🔄 Commit Tracker Service - Clean Startup")
    print("=" * 50)
    
    # Install dependencies
    install_dependencies()
    
    # Check database (optional)
    try:
        await check_database()
    except:
        pass
    
    # Start server
    start_server()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
