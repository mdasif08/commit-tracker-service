#!/usr/bin/env python3
"""
Comprehensive API test script using JSON files for Commit Tracker Service
"""

import requests
import json
import os
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = Path("data")

class APITester:
    def __init__(self):
        self.access_token = None
        self.test_results = []
    
    def log_test(self, test_name, status, response=None, error=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "response": response,
            "error": error
        }
        self.test_results.append(result)
        
        if status == "PASS":
            print(f"✅ {test_name}: PASS")
        else:
            print(f"❌ {test_name}: FAIL - {error}")
    
    def get_auth_token(self):
        """Get authentication token"""
        try:
            auth_file = TEST_DATA_DIR / "auth_token.json"
            with open(auth_file, 'r') as f:
                auth_data = json.load(f)
            
            response = requests.post(
                f"{BASE_URL}/api/auth/token",
                data=auth_data["request_data"],
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.log_test("Authentication", "PASS", token_data)
                return True
            else:
                self.log_test("Authentication", "FAIL", None, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", None, str(e))
            return False
    
    def test_health_check(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Health Check", "PASS", response.json())
            else:
                self.log_test("Health Check", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", "FAIL", None, str(e))
    
    def test_get_commits(self):
        """Test get commits endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/commits?page=1&limit=5", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Commits", "PASS", f"Total: {data.get('total', 0)} commits")
            else:
                self.log_test("Get Commits", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Commits", "FAIL", None, str(e))
    
    def test_search_commits(self):
        """Test search commits endpoint"""
        if not self.access_token:
            self.log_test("Search Commits", "SKIP", None, "No auth token")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/api/commits/search?q=authentication&limit=5",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("Search Commits", "PASS", f"Found {data.get('total', 0)} results")
            else:
                self.log_test("Search Commits", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Search Commits", "FAIL", None, str(e))
    
    def test_create_commit(self):
        """Test create commit endpoint"""
        try:
            commit_file = TEST_DATA_DIR / "create_commit.json"
            with open(commit_file, 'r') as f:
                commit_data = json.load(f)
            
            response = requests.post(
                f"{BASE_URL}/api/commits",
                json=commit_data["request_data"],
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("Create Commit", "PASS", response.json())
            else:
                self.log_test("Create Commit", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Commit", "FAIL", None, str(e))
    
    def test_track_webhook_commit(self):
        """Test track webhook commit endpoint"""
        if not self.access_token:
            self.log_test("Track Webhook Commit", "SKIP", None, "No auth token")
            return
        
        try:
            webhook_file = TEST_DATA_DIR / "track_webhook_commit.json"
            with open(webhook_file, 'r') as f:
                webhook_data = json.load(f)
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/api/commits/webhook",
                json=webhook_data["request_data"],
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("Track Webhook Commit", "PASS", response.json())
            else:
                self.log_test("Track Webhook Commit", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Track Webhook Commit", "FAIL", None, str(e))
    
    def test_track_local_commit(self):
        """Test track local commit endpoint"""
        if not self.access_token:
            self.log_test("Track Local Commit", "SKIP", None, "No auth token")
            return
        
        try:
            local_file = TEST_DATA_DIR / "track_local_commit.json"
            with open(local_file, 'r') as f:
                local_data = json.load(f)
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/api/commits/local",
                json=local_data["request_data"],
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                self.log_test("Track Local Commit", "PASS", response.json())
            else:
                self.log_test("Track Local Commit", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Track Local Commit", "FAIL", None, str(e))
    
    def test_git_status(self):
        """Test git status endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/git/status", timeout=10)
            if response.status_code == 200:
                self.log_test("Git Status", "PASS", response.json())
            else:
                self.log_test("Git Status", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Git Status", "FAIL", None, str(e))
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Testing Commit Tracker Service API with JSON files")
        print("=" * 60)
        
        # Check if test data directory exists
        if not TEST_DATA_DIR.exists():
            print(f"❌ Test data directory not found: {TEST_DATA_DIR}")
            return False
        
        # Run tests
        self.test_health_check()
        self.get_auth_token()
        self.test_get_commits()
        self.test_search_commits()
        self.test_create_commit()
        self.test_track_webhook_commit()
        self.test_track_local_commit()
        self.test_git_status()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📈 Total: {total}")
        
        if failed == 0:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return False

def main():
    """Main function"""
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
