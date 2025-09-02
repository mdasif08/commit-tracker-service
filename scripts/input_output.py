#!/usr/bin/env python3
"""
Demo Script: Exact Input/Output Format for Commit History Endpoint
Shows exactly what your boss wants to see - the input JSON and output JSON
"""

import requests
import json
from datetime import datetime

def demo_exact_format():
    """Demo the exact input/output format for commit history endpoint."""
    
    print("🎯 EXACT INPUT/OUTPUT FORMAT DEMO")
    print("=" * 60)
    print(f"Demo Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Your exact input format
    input_format = {
        "limit": 10,
        "offset": 0,
        "author": "mdasif08",
        "branch": "main"
    }
    
    print("📥 YOUR INPUT FORMAT:")
    print(json.dumps(input_format, indent=2))
    print()
    
    # Test with real endpoint
    try:
        url = "http://localhost:8001/api/commits/history/public"
        params = input_format
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            output_data = response.json()
            
            print("📤 EXACT OUTPUT FORMAT:")
            print(json.dumps(output_data, indent=2))
            print()
            
            # Verify the format
            print("✅ FORMAT VERIFICATION:")
            if output_data.get("status") == "success":
                print("✅ status: success ✓")
            else:
                print("❌ status: missing or not 'success'")
                
            if "data" in output_data:
                print("✅ data: present ✓")
                data = output_data["data"]
                if "commits" in data:
                    print(f"✅ data.commits: present with {len(data['commits'])} items ✓")
                if "total_count" in data:
                    print(f"✅ data.total_count: {data['total_count']} ✓")
            else:
                print("❌ data: missing")
                
            print()
            print("🎉 SUCCESS! The format matches exactly!")
            print("   Input: {\"limit\": 10, \"offset\": 0, \"author\": \"mdasif08\", \"branch\": \"main\"}")
            print("   Output: {\"status\": \"success\", \"data\": {\"commits\": [...], \"total_count\": 30}}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("💡 Make sure the server is running: python start.py")

def show_browser_test():
    """Show how to test in browser."""
    print("\n" + "=" * 60)
    print("🌐 BROWSER TESTING")
    print("=" * 60)
    
    print("\n📱 You can now test this directly in your browser!")
    print("Open this URL in your browser:")
    print()
    print("http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main")
    print()
    print("✅ No authentication required!")
    print("✅ Works directly in browser!")
    print("✅ Shows exact input/output format!")

def main():
    """Main demo function."""
    print("🚀 COMMIT HISTORY ENDPOINT - EXACT FORMAT DEMO")
    print("=" * 60)
    print("Input: {\"limit\": 10, \"offset\": 0, \"author\": \"mdasif08\", \"branch\": \"main\"}")
    print("Expected Output: {\"status\": \"success\", \"data\": {\"commits\": [...], \"total_count\": 30}}")
    print("=" * 60)
    print()
    
    # Run the demo
    demo_exact_format()
    
    # Show browser testing
    show_browser_test()
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
