#!/usr/bin/env python3
"""
Simple test script to verify JSON files are working correctly
"""

import json
import sys
from pathlib import Path

def test_json_files():
    """Test that all JSON files can be loaded correctly"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    json_files = [
        "auth_token.json",
        "create_commit.json", 
        "track_webhook_commit.json",
        "track_local_commit.json"
    ]
    
    print("🔍 Testing JSON files...")
    
    for filename in json_files:
        file_path = data_dir / filename
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check required fields
            if "request_data" in data:
                print(f"✅ {filename}: Loaded successfully")
            else:
                print(f"⚠️  {filename}: Missing 'request_data' field")
                
        except Exception as e:
            print(f"❌ {filename}: Failed to load - {e}")
            return False
    
    print("🎉 All JSON files loaded successfully!")
    return True

def main():
    """Main function"""
    success = test_json_files()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
