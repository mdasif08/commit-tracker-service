#!/usr/bin/env python3
"""
Commit Tracker Service - Comprehensive Test Suite
Single test script for all endpoint testing and validation.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class CommitTrackerTester:
    """Comprehensive test suite for Commit Tracker Service."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, endpoint: str, method: str, status: str, response_data: Any = None, error: str = None):
        """Log test result."""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "response": response_data,
            "error": error
        }
        self.test_results.append(result)
        
        # Print result with emojis
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {method} {endpoint}")
        if error:
            print(f"   Error: {error}")
        if response_data:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()
    
    def test_health(self) -> bool:
        """Test health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("/health", "GET", "PASS", data)
                return True
            else:
                self.log_test("/health", "GET", "FAIL", error=f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/health", "GET", "FAIL", error=str(e))
            return False
    
    def test_git_status(self) -> bool:
        """Test Git status endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/git/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("/api/git/status", "GET", "PASS", data)
                return True
            else:
                self.log_test("/api/git/status", "GET", "FAIL", error=f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/api/git/status", "GET", "FAIL", error=str(e))
            return False
    
    def test_recent_commits(self) -> bool:
        """Test recent commits endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/git/commits/recent?limit=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("/api/git/commits/recent", "GET", "PASS", data)
                return True
            else:
                self.log_test("/api/git/commits/recent", "GET", "FAIL", error=f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/api/git/commits/recent", "GET", "FAIL", error=str(e))
            return False
    
    def test_auth(self) -> bool:
        """Test authentication endpoint."""
        try:
            auth_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            response = requests.post(f"{self.base_url}/api/auth/token", data=auth_data, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.log_test("/api/auth/token", "POST", "PASS", data)
                return True
            else:
                self.log_test("/api/auth/token", "POST", "FAIL", error=f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("/api/auth/token", "POST", "FAIL", error=str(e))
            return False
    
    def test_protected_endpoints(self) -> bool:
        """Test protected endpoints with authentication."""
        if not self.auth_token:
            print("⚠️  No auth token - skipping protected endpoints")
            return False
        
        headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json'}
        
        # Test sync status
        try:
            response = requests.get(f"{self.base_url}/api/sync/status", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("/api/sync/status", "GET", "PASS", data)
            else:
                self.log_test("/api/sync/status", "GET", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("/api/sync/status", "GET", "FAIL", error=str(e))
        
        # Test commit history
        try:
            response = requests.get(f"{self.base_url}/api/commits/history?limit=5", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("/api/commits/history", "GET", "PASS", data)
            else:
                self.log_test("/api/commits/history", "GET", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("/api/commits/history", "GET", "FAIL", error=str(e))
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("🧪 Commit Tracker Service - Comprehensive Test Suite")
        print("=" * 60)
        print(f"Testing server at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test public endpoints
        print("📋 Testing Public Endpoints:")
        print("-" * 30)
        
        health_ok = self.test_health()
        git_status_ok = self.test_git_status()
        recent_commits_ok = self.test_recent_commits()
        
        # Test authentication
        print("🔐 Testing Authentication:")
        print("-" * 30)
        
        auth_ok = self.test_auth()
        
        # Test protected endpoints
        if auth_ok:
            print("🔒 Testing Protected Endpoints:")
            print("-" * 30)
            self.test_protected_endpoints()
        
        # Summary
        print("📊 Test Summary:")
        print("-" * 30)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

def main():
    """Main test function."""
    tester = CommitTrackerTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: test_results.json")
    print("🎉 Testing completed!")

if __name__ == "__main__":
    main()
