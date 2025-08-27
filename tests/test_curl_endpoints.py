#!/usr/bin/env python3
"""
Comprehensive curl endpoint testing for Commit Tracker Service
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
DATA_DIR = Path("data")

class CurlEndpointTester:
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
        elif status == "FAIL":
            print(f"❌ {test_name}: FAIL - {error}")
        else:
            print(f"⚠️  {test_name}: {status}")
    
    def get_auth_token(self):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/token",
                data={"username": "admin", "password": "admin123"},
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.log_test("Authentication", "PASS", f"Token: {self.access_token[:20]}...")
                return True
            else:
                self.log_test("Authentication", "FAIL", None, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", None, str(e))
            return False
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Health Endpoint", "PASS", response.json())
            else:
                self.log_test("Health Endpoint", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", "FAIL", None, str(e))
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                self.log_test("Root Endpoint", "PASS", response.json())
            else:
                self.log_test("Root Endpoint", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", "FAIL", None, str(e))
    
    def test_git_status_endpoint(self):
        """Test git status endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/git/status", timeout=10)
            if response.status_code == 200:
                self.log_test("Git Status Endpoint", "PASS", response.json())
            else:
                self.log_test("Git Status Endpoint", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Git Status Endpoint", "FAIL", None, str(e))
    
    def test_get_commits_endpoint(self):
        """Test get commits endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/api/commits?page=1&limit=5", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Commits Endpoint", "PASS", f"Total: {len(data.get('commits', []))} commits")
            else:
                self.log_test("Get Commits Endpoint", "FAIL", None, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Commits Endpoint", "FAIL", None, str(e))
    
    def test_create_commit_with_json(self):
        """Test create commit endpoint with JSON file"""
        try:
            json_file = DATA_DIR / "create_commit.json"
            if not json_file.exists():
                self.log_test("Create Commit with JSON", "SKIP", None, "JSON file not found")
                return
            
            with open(json_file, 'r') as f:
                commit_data = json.load(f)
            
            response = requests.post(
                f"{BASE_URL}/api/commits",
                json=commit_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Create Commit with JSON", "PASS", response.json())
            else:
                error_detail = response.json() if response.content else f"Status: {response.status_code}"
                self.log_test("Create Commit with JSON", "FAIL", None, error_detail)
        except Exception as e:
            self.log_test("Create Commit with JSON", "FAIL", None, str(e))
    
    def test_search_commits_with_auth(self):
        """Test search commits endpoint with authentication"""
        if not self.access_token:
            self.log_test("Search Commits with Auth", "SKIP", None, "No auth token")
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
                self.log_test("Search Commits with Auth", "PASS", f"Found {data.get('total', 0)} results")
            else:
                error_detail = response.json() if response.content else f"Status: {response.status_code}"
                self.log_test("Search Commits with Auth", "FAIL", None, error_detail)
        except Exception as e:
            self.log_test("Search Commits with Auth", "FAIL", None, str(e))
    
    def test_webhook_commit_with_json(self):
        """Test webhook commit endpoint with JSON file"""
        if not self.access_token:
            self.log_test("Webhook Commit with JSON", "SKIP", None, "No auth token")
            return
        
        try:
            json_file = DATA_DIR / "webhook_commit.json"
            if not json_file.exists():
                self.log_test("Webhook Commit with JSON", "SKIP", None, "JSON file not found")
                return
            
            with open(json_file, 'r') as f:
                webhook_data = json.load(f)
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/api/commits/webhook",
                json=webhook_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Webhook Commit with JSON", "PASS", response.json())
            else:
                error_detail = response.json() if response.content else f"Status: {response.status_code}"
                self.log_test("Webhook Commit with JSON", "FAIL", None, error_detail)
        except Exception as e:
            self.log_test("Webhook Commit with JSON", "FAIL", None, str(e))
    
    def test_local_commit_with_json(self):
        """Test local commit endpoint with JSON file"""
        if not self.access_token:
            self.log_test("Local Commit with JSON", "SKIP", None, "No auth token")
            return
        
        try:
            json_file = DATA_DIR / "local_commit.json"
            if not json_file.exists():
                self.log_test("Local Commit with JSON", "SKIP", None, "JSON file not found")
                return
            
            with open(json_file, 'r') as f:
                local_data = json.load(f)
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/api/commits/local",
                json=local_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Local Commit with JSON", "PASS", response.json())
            else:
                error_detail = response.json() if response.content else f"Status: {response.status_code}"
                self.log_test("Local Commit with JSON", "FAIL", None, error_detail)
        except Exception as e:
            self.log_test("Local Commit with JSON", "FAIL", None, str(e))
    
    def cleanup_test_data(self):
        """Clean up test data from database"""
        try:
            import psycopg2
            
            # Connect to database
            conn = psycopg2.connect(
                host='localhost',
                port='5432',
                database='commit_tracker',
                user='commit_user',
                password='commit_password'
            )
            
            cur = conn.cursor()
            
            # Find and delete test entries
            cur.execute("""
                DELETE FROM commits 
                WHERE commit_hash LIKE 'test_%' 
                   OR author_name LIKE 'Test%' 
                   OR repository_name LIKE 'test_%'
                   OR commit_hash = 'abc1234567890abcdef1234567890abcdef1234'
            """)
            
            deleted_count = cur.rowcount
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} test entries")
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Testing Commit Tracker Service Curl Endpoints")
        print("=" * 60)
        
        # Clean up test data before running tests
        print("🧹 Cleaning up any existing test data...")
        self.cleanup_test_data()
        
        # Run tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_git_status_endpoint()
        self.test_get_commits_endpoint()
        self.get_auth_token()
        self.test_create_commit_with_json()
        self.test_search_commits_with_auth()
        self.test_webhook_commit_with_json()
        self.test_local_commit_with_json()
        
        # Clean up test data after running tests
        print("🧹 Final cleanup to ensure no test data remains...")
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Curl Endpoint Test Results:")
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📈 Total: {total}")
        
        # Print detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏭️"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
        
        return failed == 0

def main():
    """Main function"""
    tester = CurlEndpointTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
