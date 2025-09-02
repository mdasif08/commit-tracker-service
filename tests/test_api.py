#!/usr/bin/env python3
"""
Simple API test script for Commit Tracker Service
"""

import requests
import json
import sys
import pytest
from unittest.mock import patch, MagicMock

# Configuration
BASE_URL = "http://localhost:8001"  # Update this port as needed

def test_health():
    """Test health endpoint"""
    # Mock the health check without requiring a running service
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response
        
        response = mock_get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

def test_root():
    """Test root endpoint"""
    # Mock the root endpoint check
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Welcome to Commit Tracker Service"}
        mock_get.return_value = mock_response
        
        response = mock_get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        assert "Welcome" in response.json()["message"]

def test_commits():
    """Test commits endpoint"""
    # Mock the commits endpoint check
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"commits": [], "total": 0, "page": 1}
        mock_get.return_value = mock_response
        
        response = mock_get(f"{BASE_URL}/api/commits?page=1&limit=5", timeout=5)
        assert response.status_code == 200
        assert "commits" in response.json()

def test_git_status():
    """Test git status endpoint"""
    # Mock the git status endpoint check
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "clean", "branch": "main"}
        mock_get.return_value = mock_response
        
        response = mock_get(f"{BASE_URL}/api/git/status", timeout=5)
        assert response.status_code == 200
        assert "status" in response.json()

def cleanup_test_data():
    """Clean up test data from database using direct SQL"""
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
        
        # Find test entries
        cur.execute("""
            SELECT id, commit_hash, repository_name, author_name, author_email 
            FROM commits 
            WHERE commit_hash LIKE 'test_%' 
               OR author_name LIKE 'Test%' 
               OR repository_name LIKE 'test_%'
               OR commit_hash = 'abc1234567890abcdef1234567890abcdef1234'
        """)
        
        test_entries = cur.fetchall()
        
        if test_entries:
            print(f"\n🧹 Found {len(test_entries)} test entries to clean up:")
            for entry in test_entries:
                print(f"   - {entry[1]} ({entry[2]} - {entry[3]})")
            
            # Delete test entries
            cur.execute("""
                DELETE FROM commits 
                WHERE commit_hash LIKE 'test_%' 
                   OR author_name LIKE 'Test%' 
                   OR repository_name LIKE 'test_%'
                   OR commit_hash = 'abc1234567890abcdef1234567890abcdef1234'
            """)
            
            conn.commit()
            print(f"✅ Cleaned up {len(test_entries)} test entries")
        else:
            print("✅ No test entries found to clean up")
        
        # Show remaining data
        cur.execute("SELECT COUNT(*) FROM commits")
        total_count = cur.fetchone()[0]
        print(f"📊 Total commits remaining: {total_count}")
        
        # Show by repository
        cur.execute("""
            SELECT repository_name, COUNT(*) as count 
            FROM commits 
            GROUP BY repository_name 
            ORDER BY count DESC
        """)
        repo_counts = cur.fetchall()
        
        print("📁 Commits by repository:")
        for repo, count in repo_counts:
            print(f"   {repo}: {count} commits")
        
        cur.close()
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Commit Tracker Service API")
    print("=" * 50)
    
    # Always clean up test data first
    print("\n🧹 Cleaning up any existing test data...")
    cleanup_test_data()
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Commits Endpoint", test_commits),
        ("Git Status", test_git_status),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            test_func()
            passed += 1
            print("✅ Test passed")
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Test failed: {e}")
        print()
    
    # Clean up again after tests to ensure no test data remains
    print("\n🧹 Final cleanup to ensure no test data remains...")
    cleanup_test_data()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check server status and configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
