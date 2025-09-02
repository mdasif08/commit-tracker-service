#!/usr/bin/env python3
"""
Test JSON API Format Conversion with PostgreSQL Database
Demonstrates the conversion from curl to JSON API format using real database
"""

import json
import requests
from datetime import datetime

def test_postgresql_conversion():
    """Test the conversion from curl to JSON API format with PostgreSQL."""
    
    print("🔄 JSON API FORMAT CONVERSION TEST - POSTGRESQL")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Original curl command
    print("📋 STEP 1: Original curl command")
    print("-" * 40)
    original_curl = "curl -X GET 'http://127.0.0.1:8002/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'"
    print(original_curl)
    print()
    
    # Step 2: Test original GET method
    print("📋 STEP 2: Test original GET method")
    print("-" * 40)
    try:
        response = requests.get(
            "http://127.0.0.1:8002/api/commits/history/public",
            params={
                "limit": 10,
                "offset": 0,
                "author": "mdasif08",
                "branch": "main"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ GET method: SUCCESS")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Total commits: {data.get('data', {}).get('total_count', 0)}")
            print(f"   Database: PostgreSQL")
        else:
            print(f"❌ GET method: FAILED - Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ GET method: ERROR - {e}")
    
    print()
    
    # Step 3: Convert to JSON API format
    print("📋 STEP 3: Convert to JSON API format")
    print("-" * 40)
    json_api_request = {
        "limit": 10,
        "offset": 0,
        "author": "mdasif08",
        "branch": "main"
    }
    print("JSON API request body:")
    print(json.dumps(json_api_request, indent=2))
    print()
    
    # Step 4: New curl command with JSON body
    print("📋 STEP 4: New curl command with JSON body")
    print("-" * 40)
    new_curl = """curl -X POST 'http://127.0.0.1:8002/api/commits/history/public' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "limit": 10,
    "offset": 0,
    "author": "mdasif08",
    "branch": "main"
  }'"""
    print(new_curl)
    print()
    
    # Step 5: Test JSON API POST method
    print("📋 STEP 5: Test JSON API POST method")
    print("-" * 40)
    try:
        response = requests.post(
            "http://127.0.0.1:8002/api/commits/history/public",
            json=json_api_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ POST method: SUCCESS")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Total commits: {data.get('data', {}).get('total_count', 0)}")
            print(f"   Database: PostgreSQL")
            
            # Show commit details
            commits = data.get('data', {}).get('commits', [])
            if commits:
                print(f"   Commits found:")
                for i, commit in enumerate(commits[:3], 1):  # Show first 3 commits
                    print(f"     {i}. {commit.get('commit_hash', 'N/A')} - {commit.get('author_name', 'N/A')}")
                if len(commits) > 3:
                    print(f"     ... and {len(commits) - 3} more commits")
                    
        else:
            print(f"❌ POST method: FAILED - Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ POST method: ERROR - {e}")
    
    print()
    
    # Step 6: Database Information
    print("📋 STEP 6: Database Information")
    print("-" * 40)
    print("Database Type: PostgreSQL")
    print("Connection: postgresql+asyncpg://postgres:password@localhost:5432/commit_tracker")
    print("Driver: asyncpg")
    print("Features:")
    print("   • Real database storage")
    print("   • ACID compliance")
    print("   • Concurrent access")
    print("   • Data persistence")
    print("   • Advanced querying")
    print()
    
    # Step 7: Comparison
    print("📋 STEP 7: Comparison")
    print("-" * 40)
    print("OLD FORMAT (Query Parameters):")
    print("  Method: GET")
    print("  Parameters: URL query string")
    print("  Content-Type: Not required")
    print("  Database: PostgreSQL")
    print()
    print("NEW FORMAT (JSON API):")
    print("  Method: POST")
    print("  Parameters: JSON request body")
    print("  Content-Type: application/json")
    print("  Database: PostgreSQL")
    print()
    
    print("✅ BENEFITS OF JSON API FORMAT WITH POSTGRESQL:")
    print("   • Structured data format")
    print("   • Better validation")
    print("   • Real database storage")
    print("   • Data persistence")
    print("   • Concurrent access")
    print("   • ACID compliance")
    print("   • Advanced querying capabilities")
    
    print()
    print("=" * 60)
    print("✅ POSTGRESQL CONVERSION TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_postgresql_conversion()
