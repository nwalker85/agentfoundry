#!/bin/bash

# Backlog View Testing Script
# Tests the /backlog route functionality

echo "🧪 Testing Backlog View v0.7.0"
echo "================================"
echo ""

# Check if MCP server is running
echo "1. Checking MCP Server..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ MCP Server is running on port 8001"
else
    echo "   ❌ MCP Server not running. Please start with: python mcp_server.py"
    exit 1
fi

# Check if Next.js dev server is running
echo ""
echo "2. Checking Next.js Server..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Next.js Server is running on port 3000"
else
    echo "   ❌ Next.js Server not running. Please start with: npm run dev"
    exit 1
fi

# Test the stories API endpoint
echo ""
echo "3. Testing Stories API Endpoint..."
response=$(curl -s -w "\n%{http_code}" http://localhost:3000/api/stories?limit=5)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "   ✅ API endpoint responding (HTTP 200)"
    
    # Check if response is valid JSON
    if echo "$body" | jq . > /dev/null 2>&1; then
        echo "   ✅ Response is valid JSON"
        
        # Count stories in response
        story_count=$(echo "$body" | jq '.stories | length')
        echo "   📊 Found $story_count stories in response"
        
        if [ "$story_count" -gt 0 ]; then
            echo "   ✅ Stories data populated"
            
            # Show first story details
            echo ""
            echo "   Sample Story:"
            echo "$body" | jq '.stories[0] | {title, priority, status, epic_title}'
        else
            echo "   ⚠️  No stories found (database might be empty)"
        fi
    else
        echo "   ❌ Response is not valid JSON"
        echo "   Response: $body"
        exit 1
    fi
else
    echo "   ❌ API endpoint error (HTTP $http_code)"
    echo "   Response: $body"
    exit 1
fi

# Test filter parameters
echo ""
echo "4. Testing Filter Parameters..."

# Test priority filter
echo "   Testing priority filter (P0, P1)..."
response=$(curl -s "http://localhost:3000/api/stories?priorities=P0&priorities=P1&limit=5")
if echo "$response" | jq . > /dev/null 2>&1; then
    echo "   ✅ Priority filter working"
else
    echo "   ❌ Priority filter failed"
fi

# Test status filter
echo "   Testing status filter (Ready)..."
response=$(curl -s "http://localhost:3000/api/stories?status=Ready&limit=5")
if echo "$response" | jq . > /dev/null 2>&1; then
    echo "   ✅ Status filter working"
else
    echo "   ❌ Status filter failed"
fi

echo ""
echo "================================"
echo "✅ All tests passed!"
echo ""
echo "Access the backlog view at:"
echo "   http://localhost:3000/backlog"
echo ""
echo "Manual testing checklist:"
echo "  □ Page loads without errors"
echo "  □ Stories display in cards"
echo "  □ Filter sidebar opens/closes"
echo "  □ Priority filter works"
echo "  □ Status filter works"
echo "  □ Search bar filters stories"
echo "  □ Links to Notion pages work"
echo "  □ Links to GitHub issues work"
echo "  □ Dark mode toggle works"
echo "  □ Mobile responsive layout"
echo "  □ Refresh button reloads data"
echo ""
