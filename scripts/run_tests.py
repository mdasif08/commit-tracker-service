#!/usr/bin/env python3
"""
Run Commit Tracker Service Tests
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🚀 {description}")
    print(f"📝 Command: {command}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Main test runner"""
    print("🧪 Commit Tracker Service Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: Please run this script from the commit-tracker-service directory")
        sys.exit(1)
    
    # Test 1: Start mock server
    print("\n1️⃣ Starting Mock Server...")
    print("   This will start a mock server on port 8001 for testing")
    
    # Start server in background
    try:
        server_process = subprocess.Popen([
            sys.executable, "scripts/start_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        print("   Waiting for server to start...")
        time.sleep(3)
        
        # Test if server is running
        if run_command("curl -f http://localhost:8001/health", "Testing server health"):
            print("✅ Mock server is running!")
        else:
            print("❌ Mock server failed to start")
            server_process.terminate()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)
    
    # Test 2: Run curl endpoint tests
    print("\n2️⃣ Running Curl Endpoint Tests...")
    if run_command("python tests/test_curl_endpoints.py", "Running comprehensive API tests"):
        print("✅ Curl endpoint tests passed!")
    else:
        print("❌ Curl endpoint tests failed")
    
    # Test 3: Run API tests
    print("\n3️⃣ Running API Tests...")
    if run_command("python tests/test_api.py", "Running basic API tests"):
        print("✅ API tests passed!")
    else:
        print("❌ API tests failed")
    
    # Test 4: Run database tests
    print("\n4️⃣ Running Database Tests...")
    if run_command("python tests/test_database.py", "Running database tests"):
        print("✅ Database tests passed!")
    else:
        print("❌ Database tests failed")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✅ Mock server stopped")
    except:
        print("⚠️  Server cleanup warning (this is normal)")
    
    print("\n🎉 All tests completed!")
    print("📊 Check the output above for detailed results")

if __name__ == "__main__":
    main()
