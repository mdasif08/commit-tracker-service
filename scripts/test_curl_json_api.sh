#!/bin/bash

echo "🔄 CURL TO JSON API FORMAT CONVERSION DEMO"
echo "=========================================="
echo "Converting curl parameters to JSON API format"
echo "=========================================="
echo ""

# Step 1: Original curl command
echo "📋 STEP 1: Original curl command (Query Parameters)"
echo "--------------------------------------------------"
echo "curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main'"
echo ""

# Step 2: Extract parameters
echo "📋 STEP 2: Extract query parameters"
echo "----------------------------------"
echo "Parameters extracted:"
echo "  limit: 10"
echo "  offset: 0"
echo "  author: mdasif08"
echo "  branch: main"
echo ""

# Step 3: Convert to JSON API format
echo "📋 STEP 3: Convert to JSON API format"
echo "------------------------------------"
echo "JSON API request body:"
echo '{'
echo '  "limit": 10,'
echo '  "offset": 0,'
echo '  "author": "mdasif08",'
echo '  "branch": "main"'
echo '}'
echo ""

# Step 4: New curl command with JSON body
echo "📋 STEP 4: New curl command with JSON body"
echo "-----------------------------------------"
echo "curl -X POST 'http://localhost:8001/api/commits/history/public' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"limit\": 10,"
echo "    \"offset\": 0,"
echo "    \"author\": \"mdasif08\","
echo "    \"branch\": \"main\""
echo "  }'"
echo ""

# Test the original format
echo "🧪 TESTING ORIGINAL FORMAT (GET with query parameters)"
echo "====================================================="
curl -X GET 'http://localhost:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main' \
  -H 'Accept: application/json' \
  -w "\n\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -s
echo ""

# Test the new JSON API format
echo "🧪 TESTING JSON API FORMAT (POST with JSON body)"
echo "==============================================="
curl -X POST 'http://localhost:8001/api/commits/history/public' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "limit": 10,
    "offset": 0,
    "author": "mdasif08",
    "branch": "main"
  }' \
  -w "\n\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -s
echo ""

echo "📊 FORMAT COMPARISON"
echo "==================="
echo ""
echo "OLD FORMAT (Query Parameters):"
echo "  Method: GET"
echo "  Parameters: URL query string"
echo "  Content-Type: Not required"
echo "  Validation: Basic"
echo "  Agent Mode: Disabled"
echo ""
echo "NEW FORMAT (JSON API):"
echo "  Method: POST"
echo "  Parameters: JSON request body"
echo "  Content-Type: application/json"
echo "  Validation: Advanced"
echo "  Agent Mode: Enabled"
echo ""

echo "✅ BENEFITS OF JSON API FORMAT:"
echo "   • Structured data format"
echo "   • Better validation"
echo "   • Agent mode enabled"
echo "   • Intelligent insights"
echo "   • Recommendations"
echo "   • Consistent API design"
echo ""

echo "=========================================="
echo "✅ DEMO COMPLETE!"
echo "=========================================="
echo ""
echo "📋 SUMMARY:"
echo "1. Extract parameters from curl query string"
echo "2. Convert to JSON object format"
echo "3. Use POST method with JSON body"
echo "4. Add Content-Type: application/json header"
echo "5. Agent mode provides intelligent insights and recommendations"
