#!/bin/bash

# Engineering Department UI Diagnostic Script
# This checks why the UI isn't rendering correctly

echo "=== Engineering Department UI Diagnostics ==="
echo ""

PROJECT_ROOT="/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
cd "$PROJECT_ROOT" || exit 1

echo "1. Checking Tailwind Configuration..."
if [ -f "tailwind.config.js" ]; then
    echo "   ✓ tailwind.config.js exists at root"
else
    echo "   ✗ tailwind.config.js MISSING at root"
fi

if [ -f "postcss.config.js" ]; then
    echo "   ✓ postcss.config.js exists"
else
    echo "   ✗ postcss.config.js MISSING"
fi

echo ""
echo "2. Checking Node Modules..."
if [ -d "node_modules" ]; then
    echo "   ✓ node_modules directory exists"
    if [ -f "node_modules/.bin/tailwindcss" ]; then
        echo "   ✓ Tailwind CLI installed"
    else
        echo "   ✗ Tailwind CLI NOT installed"
    fi
else
    echo "   ✗ node_modules MISSING - need to run npm install"
fi

echo ""
echo "3. Checking Key Files..."
[ -f "app/globals.css" ] && echo "   ✓ globals.css exists" || echo "   ✗ globals.css MISSING"
[ -f "app/layout.tsx" ] && echo "   ✓ layout.tsx exists" || echo "   ✗ layout.tsx MISSING"
[ -f "app/page.tsx" ] && echo "   ✓ page.tsx exists" || echo "   ✗ page.tsx MISSING"

echo ""
echo "4. Checking Dev Server..."
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "   ✓ Next.js dev server running on port 3000"
else
    echo "   ✗ No dev server detected on port 3000"
fi

echo ""
echo "5. Testing Tailwind Compilation..."
npx tailwindcss --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Tailwind CLI functional"
else
    echo "   ✗ Tailwind CLI not working"
fi

echo ""
echo "=== Recommended Actions ==="
echo ""
echo "If Tailwind config is missing:"
echo "  • Config files created - restart dev server"
echo ""
echo "If node_modules is incomplete:"
echo "  npm install"
echo ""
echo "If dev server not running:"
echo "  npm run dev"
echo ""
