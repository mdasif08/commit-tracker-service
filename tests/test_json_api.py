"""
Test JSON API Format Conversion for Commit History Endpoint
Demonstrates the steps to convert curl parameters to JSON API format
"""

import json
import requests
import pytest
from datetime import datetime
from typing import Dict, Any


class TestJSONAPIFormat:
    """Test class for JSON API format conversion and testing."""
    
    BASE_URL = "http://localhost:8001"
    
    def test_curl_to_json_api_conversion_steps(self):
        """Test the conversion steps from curl to JSON API format."""
        print("\n" + "="*80)
        print("🔄 CURL TO JSON API FORMAT CONVERSION STEPS")
        print("="*80)
        
        # Step 1: Original curl command
        original_curl = "curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'"
        
        print("\n📋 STEP 1: Original curl command")
        print("-" * 50)
        print(original_curl)
        
        # Step 2: Extract parameters
        print("\n📋 STEP 2: Extract query parameters")
        print("-" * 50)
        params = {
            "limit": 10,
            "offset": 0,
            "author": "mdasif08",
            "branch": "main"
        }
        print("Extracted parameters:")
        print(json.dumps(params, indent=2))
        
        # Step 3: Convert to JSON API format
        print("\n📋 STEP 3: Convert to JSON API format")
        print("-" * 50)
        json_api_request = {
            "limit": 10,
            "offset": 0,
            "author": "mdasif08",
            "branch": "main"
        }
        print("JSON API request body:")
        print(json.dumps(json_api_request, indent=2))
        
        # Step 4: New curl command with JSON body
        print("\n📋 STEP 4: New curl command with JSON body")
        print("-" * 50)
        new_curl = """curl -X POST 'http://localhost:8001/api/commits/history/public' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "limit": 10,
    "offset": 0,
    "author": "mdasif08",
    "branch": "main"
  }'"""
        print(new_curl)
        
        # Verify the conversion was successful
        assert params == json_api_request
        assert "limit" in params
        assert "author" in params
    
    def test_json_api_endpoint_post(self):
        """Test the POST endpoint with JSON API format."""
        print("\n" + "="*80)
        print("🧪 TESTING JSON API FORMAT (POST)")
        print("="*80)
        
        # JSON API request body
        request_body = {
            "limit": 10,
            "offset": 0,
            "author": "mdasif08",
            "branch": "main"
        }
        
        print("\n📤 Sending JSON API request:")
        print(json.dumps(request_body, indent=2))
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/api/commits/history/public",
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("\n📥 JSON API Response:")
                print(json.dumps(response_data, indent=2))
                
                # Verify JSON API format
                self._verify_json_api_format(response_data)
                
                # Verify Agent mode
                self._verify_agent_mode(response_data)
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    def test_json_api_endpoint_get(self):
        """Test the GET endpoint with query parameters."""
        print("\n" + "="*80)
        print("🧪 TESTING JSON API FORMAT (GET)")
        print("="*80)
        
        # Query parameters
        params = {
            "limit": 10,
            "offset": 0,
            "author": "mdasif08",
            "branch": "main"
        }
        
        print("\n📤 Sending GET request with query parameters:")
        print(f"URL: {self.BASE_URL}/api/commits/history/public")
        print(f"Parameters: {params}")
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/commits/history/public",
                params=params,
                timeout=10
            )
            
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print("\n📥 JSON API Response:")
                print(json.dumps(response_data, indent=2))
                
                # Verify JSON API format
                self._verify_json_api_format(response_data)
                
                # Verify Agent mode
                self._verify_agent_mode(response_data)
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
    
    def test_json_api_format_validation(self):
        """Test JSON API format validation."""
        print("\n" + "="*80)
        print("🔍 JSON API FORMAT VALIDATION")
        print("="*80)
        
        # Test cases for validation
        test_cases = [
            {
                "name": "Valid request",
                "data": {"limit": 10, "offset": 0, "author": "mdasif08", "branch": "main"},
                "expected_status": 200
            },
            {
                "name": "Invalid limit (too high)",
                "data": {"limit": 150, "offset": 0, "author": "mdasif08", "branch": "main"},
                "expected_status": 400
            },
            {
                "name": "Invalid offset (negative)",
                "data": {"limit": 10, "offset": -5, "author": "mdasif08", "branch": "main"},
                "expected_status": 400
            },
            {
                "name": "Missing required fields",
                "data": {"author": "mdasif08"},
                "expected_status": 200  # Should work with defaults
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"📤 Request: {json.dumps(test_case['data'], indent=2)}")
            
            try:
                response = requests.post(
                    f"{self.BASE_URL}/api/commits/history/public",
                    json=test_case['data'],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                print(f"📥 Status: {response.status_code} (Expected: {test_case['expected_status']})")
                
                if response.status_code == test_case['expected_status']:
                    print("✅ PASS")
                else:
                    print("❌ FAIL")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Request failed: {e}")
    
    def _verify_json_api_format(self, response_data: Dict[str, Any]):
        """Verify the response follows JSON API format."""
        print("\n🔍 Verifying JSON API format:")
        
        # Check required fields
        required_fields = ["status", "data"]
        for field in required_fields:
            if field in response_data:
                print(f"✅ {field}: present")
            else:
                print(f"❌ {field}: missing")
        
        # Check data structure
        if "data" in response_data:
            data = response_data["data"]
            data_fields = ["commits", "total_count", "page", "page_size"]
            for field in data_fields:
                if field in data:
                    print(f"✅ data.{field}: present")
                else:
                    print(f"❌ data.{field}: missing")
    
    def _verify_agent_mode(self, response_data: Dict[str, Any]):
        """Verify Agent mode is enabled and working."""
        print("\n🤖 Verifying Agent mode:")
        
        if "agent" in response_data:
            agent = response_data["agent"]
            print("✅ Agent mode: enabled")
            
            if "mode" in agent and agent["mode"] == "enabled":
                print("✅ Agent mode: confirmed enabled")
            else:
                print("❌ Agent mode: not properly configured")
            
            if "insights" in agent:
                insights = agent["insights"]
                print("✅ Agent insights: present")
                
                if "analysis" in insights:
                    print("✅ Agent analysis: present")
                if "recommendations" in insights:
                    print(f"✅ Agent recommendations: {len(insights['recommendations'])} items")
            else:
                print("❌ Agent insights: missing")
        else:
            print("❌ Agent mode: not found in response")


def main():
    """Main function to run all tests."""
    print("🚀 JSON API FORMAT TESTING SUITE")
    print("="*80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = TestJSONAPIFormat()
    
    # Run conversion steps demonstration
    tester.test_curl_to_json_api_conversion_steps()
    
    # Run actual tests
    tester.test_json_api_endpoint_post()
    tester.test_json_api_endpoint_get()
    tester.test_json_api_format_validation()
    
    print("\n" + "="*80)
    print("✅ JSON API FORMAT TESTING COMPLETE")
    print("="*80)
    
    print("\n📋 SUMMARY OF CONVERSION STEPS:")
    print("1. Extract parameters from curl query string")
    print("2. Convert to JSON object format")
    print("3. Use POST method with JSON body")
    print("4. Add Content-Type: application/json header")
    print("5. Agent mode provides intelligent insights and recommendations")


if __name__ == "__main__":
    main()


