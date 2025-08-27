#!/usr/bin/env python3
"""
Start the Commit Tracker Service Mock Server
"""

import uvicorn
import sys
from pathlib import Path

# Add tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

if __name__ == "__main__":
    print("🚀 Starting Commit Tracker Service Mock Server...")
    print("📍 Server will be available at: http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    print("🏥 Health Check: http://localhost:8001/health")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        uvicorn.run(
            "test_server:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
