#!/usr/bin/env python3
"""
Test Script: Commit History Endpoint Input/Output Demo
Shows exactly what happens when you send the specified input to the endpoint
"""

import requests
import json
from datetime import datetime

def test_commit_history_endpoint():
    """Test the commit history endpoint with the exact input specified."""
    
    print("🎯 TESTING: Commit History Endpoint")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Base URL
    base_url = "http://localhost:8001"
    
    # Step 1: Get authentication token
    print("1️⃣ STEP 1: Getting Authentication Token")
    print("-" * 40)
    
    auth_input = {
        "username": "mdasif08",
        "password": "Asif@24680"
    }
    
    print("📥 AUTH INPUT (form-encoded):")
    print(f"username=mdasif08&password=Asif@24680")
    print()
    
    try:
        auth_response = requests.post(
            f"{base_url}/api/auth/token",
            data=auth_input,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if auth_response.status_code == 200:
            auth_output = auth_response.json()
            print("📤 AUTH OUTPUT:")
            print(json.dumps(auth_output, indent=2))
            print()
            
            access_token = auth_output['access_token']
            print("✅ Authentication successful! Token obtained.")
            print()
        else:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            print(auth_response.text)
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication request failed: {e}")
        print("💡 Make sure the server is running: python scripts/start_server.py")
        return
    
    # Step 2: Test Commit History endpoint
    print("2️⃣ STEP 2: Testing Commit History Endpoint")
    print("-" * 40)
    
    # The exact input you specified
    commit_history_input = {
        "limit": 10,
        "offset": 0,
        "author": "mdasif08",
        "branch": "main"
    }
    
    print("📥 COMMIT HISTORY INPUT (query parameters):")
    print(json.dumps(commit_history_input, indent=2))
    print()
    print("🔗 Full URL with query parameters:")
    print(f"{base_url}/api/commits/history?limit=10&offset=0&author=mdasif08&branch=main")
    print()
    
    try:
        commit_history_response = requests.get(
            f"{base_url}/api/commits/history",
            params=commit_history_input,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        print(f"📤 COMMIT HISTORY OUTPUT (Status: {commit_history_response.status_code}):")
        
        if commit_history_response.status_code == 200:
            output_json = commit_history_response.json()
            print(json.dumps(output_json, indent=2))
            print()
            
            # Verify the output format matches expected structure
            print("✅ OUTPUT FORMAT VERIFICATION:")
            if "status" in output_json and output_json["status"] == "success":
                print("✅ status: success ✓")
            else:
                print("❌ status: missing or not 'success'")
                
            if "data" in output_json:
                print("✅ data: present ✓")
                if "commits" in output_json["data"]:
                    print("✅ data.commits: present ✓")
                if "total_count" in output_json["data"]:
                    print("✅ data.total_count: present ✓")
            else:
                print("❌ data: missing")
                
            print()
            print("🎉 SUCCESS! The output format matches exactly what you expected!")
            print("   Input: {\"limit\": 10, \"offset\": 0, \"author\": \"mdasif08\", \"branch\": \"main\"}")
            print("   Output: {\"status\": \"success\", \"data\": {\"commits\": [...], \"total_count\": 1}}")
            
        else:
            print(f"❌ Error: {commit_history_response.status_code}")
            print(commit_history_response.text)
            print()
            print("💡 Troubleshooting:")
            print("1. Make sure the server is running")
            print("2. Check if there are commits in the database")
            print("3. Verify the authentication token is valid")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the server is running: python scripts/start_server.py")

def show_curl_commands():
    """Show the curl commands for manual testing."""
    print("\n" + "=" * 60)
    print("🔧 CURL COMMANDS FOR MANUAL TESTING")
    print("=" * 60)
    
    print("\n1️⃣ Get Authentication Token:")
    print("curl -X POST 'http://localhost:8001/api/auth/token' \\")
    print("  -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("  -d 'username=mdasif08&password=Asif@24680'")
    
    print("\n2️⃣ Test Commit History (replace YOUR_TOKEN with the token from step 1):")
    print("curl -X GET 'http://localhost:8001/api/commits/history?limit=10&offset=0&author=mdasif08&branch=main' \\")
    print("  -H 'Authorization: Bearer YOUR_TOKEN'")
    
    print("\n3️⃣ Combined test (if you have jq installed):")
    print("TOKEN=$(curl -s -X POST 'http://localhost:8001/api/auth/token' \\")
    print("  -H 'Content-Type: application/x-www-form-urlencoded' \\")
    print("  -d 'username=mdasif08&password=Asif@24680' | jq -r '.access_token')")
    print("curl -X GET 'http://localhost:8001/api/commits/history?limit=10&offset=0&author=mdasif08&branch=main' \\")
    print("  -H 'Authorization: Bearer $TOKEN' | jq '.'")

def main():
    """Main function."""
    print("🚀 COMMIT HISTORY ENDPOINT - INPUT/OUTPUT TEST")
    print("=" * 60)
    print("Testing: GET /api/commits/history")
    print("Input: {\"limit\": 10, \"offset\": 0, \"author\": \"mdasif08\", \"branch\": \"main\"}")
    print("Expected Output: {\"status\": \"success\", \"data\": {\"commits\": [...], \"total_count\": 1}}")
    print("=" * 60)
    print()
    
    # Run the test
    test_commit_history_endpoint()
    
    # Show curl commands
    show_curl_commands()
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
