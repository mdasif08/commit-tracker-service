#!/usr/bin/env python3
"""
JSON API Format Conversion Demo
Shows the exact steps to convert curl parameters to JSON API format
"""

import json
import requests
from datetime import datetime


def demo_conversion_steps():
    """Demonstrate the conversion steps from curl to JSON API format."""
    
    print("🔄 CURL TO JSON API FORMAT CONVERSION")
    print("=" * 60)
    print(f"Demo Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Original curl command
    print("📋 STEP 1: Original curl command")
    print("-" * 40)
    original_curl = "curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'"
    print(original_curl)
    print()
    
    # Step 2: Extract parameters
    print("📋 STEP 2: Extract query parameters")
    print("-" * 40)
    params = {
        "limit": 10,
        "offset": 0,
        "author": "mdasif08",
        "branch": "main"
    }
    print("Extracted parameters:")
    print(json.dumps(params, indent=2))
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
    
    return params, json_api_request


def test_json_api_endpoint():
    """Test the JSON API endpoint."""
    print("🧪 TESTING JSON API ENDPOINT")
    print("=" * 60)
    
    # JSON API request body
    request_body = {
        "limit": 10,
        "offset": 0,
        "author": "mdasif08",
        "branch": "main"
    }
    
    print("📤 Sending JSON API request:")
    print(json.dumps(request_body, indent=2))
    print()
    
    try:
        response = requests.post(
            "http://localhost:8001/api/commits/history/public",
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            print("📥 JSON API Response:")
            print(json.dumps(response_data, indent=2))
            print()
            
            # Verify Agent mode
            if "agent" in response_data:
                agent = response_data["agent"]
                print("🤖 Agent Mode: ENABLED")
                print(f"   Mode: {agent.get('mode', 'unknown')}")
                print(f"   Timestamp: {agent.get('timestamp', 'unknown')}")
                
                if "insights" in agent:
                    insights = agent["insights"]
                    print("   Analysis:")
                    print(f"     Total commits: {insights.get('analysis', {}).get('total_commits', 'unknown')}")
                    print(f"     Recommendations: {len(insights.get('recommendations', []))} items")
            else:
                print("❌ Agent Mode: NOT FOUND")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the server is running: python start.py")


def show_comparison():
    """Show comparison between old and new formats."""
    print("📊 FORMAT COMPARISON")
    print("=" * 60)
    
    print("OLD FORMAT (Query Parameters):")
    print("curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'")
    print()
    
    print("NEW FORMAT (JSON API):")
    print("curl -X POST 'http://localhost:8001/api/commits/history/public' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{")
    print("    \"limit\": 10,")
    print("    \"offset\": 0,")
    print("    \"author\": \"mdasif08\",")
    print("    \"branch\": \"main\"")
    print("  }'")
    print()
    
    print("✅ BENEFITS OF JSON API FORMAT:")
    print("   • Structured data format")
    print("   • Better validation")
    print("   • Agent mode enabled")
    print("   • Intelligent insights")
    print("   • Recommendations")
    print("   • Consistent API design")


def main():
    """Main function."""
    print("🚀 JSON API FORMAT CONVERSION DEMO")
    print("=" * 60)
    print("Converting curl parameters to JSON API format")
    print("=" * 60)
    print()
    
    # Show conversion steps
    demo_conversion_steps()
    
    # Test the endpoint
    test_json_api_endpoint()
    
    # Show comparison
    show_comparison()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)
    print()
    print("📋 SUMMARY:")
    print("1. Extract parameters from curl query string")
    print("2. Convert to JSON object format")
    print("3. Use POST method with JSON body")
    print("4. Add Content-Type: application/json header")
    print("5. Agent mode provides intelligent insights and recommendations")


if __name__ == "__main__":
    main()
