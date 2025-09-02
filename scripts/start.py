#!/usr/bin/env python3
"""
Commit Tracker Service - Single Server Startup Script
Professional, clean server startup for production and development.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

def setup_environment():
    """Setup environment variables."""
    # Database configuration
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./commit_tracker.db")
    
    # Server configuration
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8001")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("LOG_LEVEL", "info")
    
    # Security
    os.environ.setdefault("SECRET_KEY", "your-secret-key-change-in-production")
    
    print("✅ Environment configured")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import uvicorn
        import fastapi
        import sqlalchemy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_database():
    """Check database connection."""
    try:
        import asyncio
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from database import get_db_service, close_db_service
        
        async def check():
            try:
                db_service = await get_db_service()
                if await db_service.health_check():
                    print("✅ Database connection: OK")
                    return True
                else:
                    print("❌ Database connection: FAILED")
                    return False
            except Exception as e:
                print(f"❌ Database error: {e}")
                return False
            finally:
                await close_db_service()
        
        return asyncio.run(check())
    except Exception as e:
        print(f"⚠️  Database check skipped: {e}")
        return True

def start_server(host: str = "0.0.0.0", port: int = 8001, reload: bool = True, log_level: str = "info"):
    """Start the server with proper configuration."""
    
    print("🚀 Starting Commit Tracker Service...")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🏥 Health: http://{host}:{port}/health")
    print(f"🔄 Reload: {'Enabled' if reload else 'Disabled'}")
    print(f"📝 Log Level: {log_level.upper()}")
    print("=" * 60)
    
    try:
        # Change to src directory for proper imports
        src_path = Path(__file__).parent / "src"
        os.chdir(src_path)
        
        # Start uvicorn server
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", host,
            "--port", str(port),
            "--reload" if reload else "--no-reload",
            "--log-level", log_level
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    """Main startup function."""
    print("🎯 Commit Tracker Service - Professional Startup")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database (optional)
    check_database()
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Start server
    success = start_server(
        host=host,
        port=port,
        reload=debug,
        log_level=log_level
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
