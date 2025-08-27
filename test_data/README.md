# Commit Tracker Service - JSON Test Files

This directory contains JSON files for testing the Commit Tracker Service API endpoints using curl commands.

## 📁 Available Test Files

### 1. `auth_token.json`
**Purpose**: Get authentication token
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### 2. `create_commit.json`
**Purpose**: Create a new commit record
```bash
curl -X POST "http://localhost:8000/api/commits" \
  -H "Content-Type: application/json" \
  -d @create_commit.json
```

### 3. `track_webhook_commit.json`
**Purpose**: Track commits from GitHub webhook
```bash
curl -X POST "http://localhost:8000/api/commits/webhook" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @track_webhook_commit.json
```

### 4. `track_local_commit.json`
**Purpose**: Track commits from local git repository
```bash
curl -X POST "http://localhost:8000/api/commits/local" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @track_local_commit.json
```

## 🚀 How to Use

### Method 1: Using curl with JSON files
1. **Get authentication token first:**
   ```bash
   curl -X POST "http://localhost:8000/api/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   ```

2. **Use the token for protected endpoints:**
   ```bash
   # Replace YOUR_TOKEN with the actual token from step 1
   curl -X POST "http://localhost:8000/api/commits/webhook" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d @track_webhook_commit.json
   ```

### Method 2: Using the Python test script
```bash
python test_api_with_json.py
```

This script will:
- Run all tests automatically
- Use the JSON files for request data
- Handle authentication automatically
- Provide detailed test results

## 📋 Test Endpoints

| Endpoint | Method | Auth Required | JSON File |
|----------|--------|---------------|-----------|
| `/health` | GET | ❌ No | - |
| `/api/commits` | GET | ❌ No | - |
| `/api/commits/search` | GET | ✅ Yes | - |
| `/api/commits` | POST | ❌ No | `create_commit.json` |
| `/api/commits/webhook` | POST | ✅ Yes | `track_webhook_commit.json` |
| `/api/commits/local` | POST | ✅ Yes | `track_local_commit.json` |
| `/api/git/status` | GET | ❌ No | - |

## 🔧 Customizing Test Data

You can modify the JSON files to test different scenarios:

1. **Change commit data** in `create_commit.json`
2. **Modify webhook payload** in `track_webhook_commit.json`
3. **Update local commit info** in `track_local_commit.json`

## 📊 Expected Responses

Each JSON file contains:
- `description`: What the test does
- `curl_command`: The exact curl command to run
- `request_data`: The data to send in the request
- `expected_response`: What response you should expect

## 🛠️ Troubleshooting

### Common Issues:
1. **Authentication Error (403)**: Make sure you have a valid token
2. **Connection Refused**: Ensure the server is running on port 8000
3. **JSON Parse Error**: Check that your JSON files are valid

### Server Status Check:
```bash
curl -X GET "http://localhost:8000/health"
```

### Get Fresh Token:
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## 📝 Notes

- All timestamps should be in ISO 8601 format: `2024-01-15T10:30:00Z`
- Commit hashes should be valid Git commit hashes
- File paths should be relative to the repository root
- The server must be running before running any tests
