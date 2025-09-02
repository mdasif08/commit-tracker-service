#!/usr/bin/env python3
"""
Test JSON API Format Conversion
Demonstrates the conversion from curl to JSON API format
"""

import json
import requests
from datetime import datetime

def test_conversion():
    """Test the conversion from curl to JSON API format."""
    
    print("🔄 JSON API FORMAT CONVERSION TEST")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Original curl command
    print("📋 STEP 1: Original curl command")
    print("-" * 40)
    original_curl = "curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'"
    print(original_curl)
    print()
    
    # Step 2: Test original GET method
    print("📋 STEP 2: Test original GET method")
    print("-" * 40)
    try:
        response = requests.get(
            "http://localhost:8001/api/commits/history/public",
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
            print(f"   Agent mode: {data.get('agent', {}).get('mode', 'disabled')}")
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
    new_curl = """curl -X POST 'http://localhost:8001/api/commits/history/public' \\
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
            "http://localhost:8001/api/commits/history/public",
            json=json_api_request,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ POST method: SUCCESS")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Total commits: {data.get('data', {}).get('total_count', 0)}")
            print(f"   Agent mode: {data.get('agent', {}).get('mode', 'disabled')}")
            
            # Show Agent insights
            agent = data.get('agent', {})
            if agent.get('mode') == 'enabled':
                insights = agent.get('insights', {})
                analysis = insights.get('analysis', {})
                print(f"   Agent insights:")
                print(f"     - Total commits: {analysis.get('total_commits', 0)}")
                print(f"     - Current page: {analysis.get('page_info', {}).get('current_page', 0)}")
                print(f"     - Has more: {analysis.get('page_info', {}).get('has_more', False)}")
                print(f"     - Author filter: {analysis.get('filter_summary', {}).get('author_filter', 'None')}")
                print(f"     - Branch filter: {analysis.get('filter_summary', {}).get('branch_filter', 'None')}")
                
                recommendations = insights.get('recommendations', [])
                if recommendations:
                    print(f"   Recommendations:")
                    for rec in recommendations:
                        print(f"     - {rec.get('type', 'info')}: {rec.get('message', 'No message')}")
                else:
                    print(f"   Recommendations: None")
                    
        else:
            print(f"❌ POST method: FAILED - Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ POST method: ERROR - {e}")
    
    print()
    
    # Step 6: Comparison
    print("📋 STEP 6: Comparison")
    print("-" * 40)
    print("OLD FORMAT (Query Parameters):")
    print("  Method: GET")
    print("  Parameters: URL query string")
    print("  Content-Type: Not required")
    print("  Validation: Basic")
    print("  Agent Mode: Disabled")
    print()
    print("NEW FORMAT (JSON API):")
    print("  Method: POST")
    print("  Parameters: JSON request body")
    print("  Content-Type: application/json")
    print("  Validation: Advanced")
    print("  Agent Mode: Enabled")
    print()
    
    print("✅ BENEFITS OF JSON API FORMAT:")
    print("   • Structured data format")
    print("   • Better validation")
    print("   • Agent mode enabled")
    print("   • Intelligent insights")
    print("   • Recommendations")
    print("   • Consistent API design")
    
    print()
    print("=" * 60)
    print("✅ CONVERSION TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_conversion()
