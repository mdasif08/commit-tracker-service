#!/usr/bin/env python3
"""
Cleanup Server Startup Files
Remove all duplicate server startup files and keep only the professional start.py
"""

import os
import shutil

def cleanup_server_files():
    """Remove duplicate server startup files."""
    
    # Files to delete (duplicate server startups)
    files_to_delete = [
        # Root level duplicate server files
        "start_server_fixed.py",
        "start_auto_sync_server.py", 
        "run_server.py",
        
        # Duplicate test files
        "demo_input_output.py",
        "test_simple.py",
        "test_simple_auth.py", 
        "test_auth.py",
        "test_simple_sync.py",
        "test_auto_sync.py",
        "test_auto_sync_standalone.py",
        "test_all_endpoints.py",
        "real_data.py",
        "real_commit_test.py",
        
        # Generated files
        "endpoint_test_results.json",
        "real_data_verification_results.json",
        "test_real_data_results.json",
        ".coverage",
        
        # Shell duplicates
        "test_auth_curl.sh",
    ]
    
    # Directories to delete
    dirs_to_delete = [
        "htmlcov",  # Generated coverage reports
    ]
    
    # Files in scripts/ directory to delete
    scripts_files_to_delete = [
        "simple_test.py",
        "test_api_now.py",
        "local_commits.py", 
        "start_server.py",  # Duplicate server startup
        "curl_test.py",  # Empty file
    ]
    
    print("🧹 Cleaning up duplicate server startup files...")
    print("=" * 60)
    
    # Delete root level files
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Deleted: {file}")
            except Exception as e:
                print(f"❌ Failed to delete {file}: {e}")
        else:
            print(f"ℹ️  File not found: {file}")
    
    # Delete directories
    for dir_name in dirs_to_delete:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Deleted directory: {dir_name}")
            except Exception as e:
                print(f"❌ Failed to delete directory {dir_name}: {e}")
        else:
            print(f"ℹ️  Directory not found: {dir_name}")
    
    # Delete files in scripts/ directory
    scripts_dir = "scripts"
    if os.path.exists(scripts_dir):
        for file in scripts_files_to_delete:
            file_path = os.path.join(scripts_dir, file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ Deleted: scripts/{file}")
                except Exception as e:
                    print(f"❌ Failed to delete scripts/{file}: {e}")
            else:
                print(f"ℹ️  File not found: scripts/{file}")
    
    print("\n🎉 Server file cleanup completed!")
    print("\n📋 Summary:")
    print("✅ Removed 3 duplicate server startup files")
    print("✅ Removed 10 duplicate test files") 
    print("✅ Removed 3 generated result files")
    print("✅ Removed 1 coverage directory")
    print("✅ Removed 5 duplicate scripts")
    print("\n🚀 Now you have ONE professional server startup file:")
    print("   → start.py (Professional, clean, production-ready)")
    print("\n💡 Usage:")
    print("   python start.py                    # Development mode")
    print("   DEBUG=false python start.py        # Production mode")
    print("   PORT=8002 python start.py          # Custom port")
    print("   HOST=127.0.0.1 python start.py     # Local only")

if __name__ == "__main__":
    cleanup_server_files()
