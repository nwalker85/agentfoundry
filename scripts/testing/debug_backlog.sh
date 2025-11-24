#!/bin/bash

# Backlog Debug Script
# Comprehensive debugging for the /backlog route

echo "🔍 Backlog View Debugger"
echo "========================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Check if servers are running
echo -e "${BLUE}1. Checking Server Status${NC}"
echo "----------------------------"

# Check MCP Server
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ MCP Server is running on port 8001${NC}"
    MCP_RUNNING=true
else
    echo -e "${RED}❌ MCP Server NOT running${NC}"
    echo "   Start with: python mcp_server.py"
    MCP_RUNNING=false
fi

# Check Next.js Server
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Next.js Server is running on port 3000${NC}"
    NEXT_RUNNING=true
else
    echo -e "${RED}❌ Next.js Server NOT running${NC}"
    echo "   Start with: npm run dev"
    NEXT_RUNNING=false
fi

echo ""

# 2. Check file structure
echo -e "${BLUE}2. Checking File Structure${NC}"
echo "----------------------------"

FILES=(
    "app/backlog/page.tsx"
    "app/backlog/components/StoryCard.tsx"
    "app/backlog/components/FilterSidebar.tsx"
    "app/api/stories/route.ts"
    "app/lib/types/story.ts"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file MISSING${NC}"
    fi
done

echo ""

# 3. Check environment variables
echo -e "${BLUE}3. Checking Environment Variables${NC}"
echo "-----------------------------------"

if [ -f ".env.local" ]; then
    echo -e "${GREEN}✅ .env.local exists${NC}"
    
    # Check for required variables (without exposing values)
    if grep -q "OPENAI_API_KEY" .env.local; then
        echo -e "${GREEN}✅ OPENAI_API_KEY configured${NC}"
    else
        echo -e "${RED}❌ OPENAI_API_KEY missing${NC}"
    fi
    
    if grep -q "NOTION_API_TOKEN" .env.local; then
        echo -e "${GREEN}✅ NOTION_API_TOKEN configured${NC}"
    else
        echo -e "${YELLOW}⚠️  NOTION_API_TOKEN not set (mock mode will be used)${NC}"
    fi
    
    if grep -q "NEXT_PUBLIC_API_URL" .env.local; then
        echo -e "${GREEN}✅ NEXT_PUBLIC_API_URL configured${NC}"
    else
        echo -e "${YELLOW}⚠️  NEXT_PUBLIC_API_URL not set (will default to localhost:8001)${NC}"
    fi
else
    echo -e "${RED}❌ .env.local MISSING${NC}"
    echo "   Copy from .env.example: cp .env.example .env.local"
fi

echo ""

# 4. Test API endpoints (only if servers are running)
if [ "$MCP_RUNNING" = true ] && [ "$NEXT_RUNNING" = true ]; then
    echo -e "${BLUE}4. Testing API Endpoints${NC}"
    echo "-------------------------"
    
    # Test MCP server list-stories endpoint
    echo "Testing MCP server endpoint..."
    MCP_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8001/api/tools/notion/list-stories \
        -H "Content-Type: application/json" \
        -d '{"limit": 5}')
    
    MCP_CODE=$(echo "$MCP_RESPONSE" | tail -n1)
    MCP_BODY=$(echo "$MCP_RESPONSE" | head -n-1)
    
    if [ "$MCP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ MCP endpoint responding (HTTP 200)${NC}"
        
        # Check if response is valid JSON
        if echo "$MCP_BODY" | jq . > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Valid JSON response${NC}"
            
            # Count stories
            STORY_COUNT=$(echo "$MCP_BODY" | jq '.stories | length' 2>/dev/null || echo "0")
            echo "   📊 Stories in response: $STORY_COUNT"
            
            if [ "$STORY_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✅ Stories data present${NC}"
                echo ""
                echo "   Sample story:"
                echo "$MCP_BODY" | jq '.stories[0] | {title, priority, status}' 2>/dev/null || echo "   Could not parse story"
            else
                echo -e "${YELLOW}⚠️  No stories returned (database might be empty)${NC}"
            fi
        else
            echo -e "${RED}❌ Invalid JSON response${NC}"
            echo "   Response: $MCP_BODY"
        fi
    else
        echo -e "${RED}❌ MCP endpoint error (HTTP $MCP_CODE)${NC}"
        echo "   Response: $MCP_BODY"
    fi
    
    echo ""
    
    # Test Next.js API route
    echo "Testing Next.js API route..."
    NEXT_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:3000/api/stories?limit=5)
    
    NEXT_CODE=$(echo "$NEXT_RESPONSE" | tail -n1)
    NEXT_BODY=$(echo "$NEXT_RESPONSE" | head -n-1)
    
    if [ "$NEXT_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Next.js API route responding (HTTP 200)${NC}"
        
        if echo "$NEXT_BODY" | jq . > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Valid JSON response${NC}"
            NEXT_STORY_COUNT=$(echo "$NEXT_BODY" | jq '.stories | length' 2>/dev/null || echo "0")
            echo "   📊 Stories in response: $NEXT_STORY_COUNT"
        else
            echo -e "${RED}❌ Invalid JSON response${NC}"
            echo "   Response: $NEXT_BODY"
        fi
    else
        echo -e "${RED}❌ Next.js API route error (HTTP $NEXT_CODE)${NC}"
        echo "   Response: $NEXT_BODY"
    fi
    
    echo ""
    
    # Test backlog page
    echo "Testing backlog page..."
    BACKLOG_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/backlog)
    
    if [ "$BACKLOG_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Backlog page responding (HTTP 200)${NC}"
    else
        echo -e "${RED}❌ Backlog page error (HTTP $BACKLOG_CODE)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping API tests - servers not running${NC}"
fi

echo ""

# 5. Check browser console
echo -e "${BLUE}5. Browser Console Check${NC}"
echo "-------------------------"
echo "If you're seeing issues in the browser:"
echo ""
echo "1. Open Chrome DevTools (F12 or Cmd+Option+I)"
echo "2. Go to Console tab"
echo "3. Look for errors (red messages)"
echo "4. Check Network tab for failed requests"
echo ""
echo "Common issues to look for:"
echo "  • CORS errors"
echo "  • 404 Not Found (API routes not registered)"
echo "  • 500 Internal Server Error (MCP server issues)"
echo "  • Type errors (TypeScript compilation issues)"
echo "  • React hydration errors"

echo ""

# 6. Check Next.js build
echo -e "${BLUE}6. Checking Next.js Build${NC}"
echo "--------------------------"

if [ -d ".next" ]; then
    echo -e "${GREEN}✅ .next directory exists${NC}"
    
    # Check if it's stale
    NEXT_MTIME=$(stat -f %m .next 2>/dev/null || stat -c %Y .next 2>/dev/null)
    CURRENT_TIME=$(date +%s)
    AGE=$((CURRENT_TIME - NEXT_MTIME))
    
    if [ $AGE -lt 3600 ]; then
        echo -e "${GREEN}✅ Build is recent (less than 1 hour old)${NC}"
    else
        echo -e "${YELLOW}⚠️  Build is older than 1 hour${NC}"
        echo "   Consider rebuilding: rm -rf .next && npm run dev"
    fi
else
    echo -e "${RED}❌ .next directory missing${NC}"
    echo "   Run: npm run dev"
fi

echo ""

# 7. Summary and recommendations
echo -e "${BLUE}7. Summary & Recommendations${NC}"
echo "------------------------------"

if [ "$MCP_RUNNING" = true ] && [ "$NEXT_RUNNING" = true ]; then
    echo -e "${GREEN}✅ Both servers are running${NC}"
    echo ""
    echo "Access the backlog at: ${BLUE}http://localhost:3000/backlog${NC}"
    echo ""
    echo "If you're still seeing issues:"
    echo "1. Check browser console for errors"
    echo "2. Review Next.js terminal for compilation errors"
    echo "3. Check MCP server terminal for API errors"
    echo "4. Try clearing Next.js cache: rm -rf .next && npm run dev"
    echo "5. Check Notion API credentials if using real data"
else
    echo -e "${RED}⚠️  One or both servers are not running${NC}"
    echo ""
    echo "To start the servers:"
    echo ""
    echo "Terminal 1 - MCP Server:"
    echo "  cd /Users/nwalker/Development/Projects/Engineering\\ Department/engineeringdepartment"
    echo "  source venv/bin/activate"
    echo "  python mcp_server.py"
    echo ""
    echo "Terminal 2 - Next.js:"
    echo "  cd /Users/nwalker/Development/Projects/Engineering\\ Department/engineeringdepartment"
    echo "  npm run dev"
fi

echo ""
echo "========================"
echo "Debug complete!"
echo ""
