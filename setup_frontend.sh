#!/bin/bash

# Post Node.js Installation Setup
# Run this after installing Node.js

echo "🚀 Setting up Engineering Department Frontend"
echo ""

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed yet!"
    echo "Please install Node.js first using one of these methods:"
    echo ""
    echo "1. Download from: https://nodejs.org/en/download/"
    echo "2. Or run: brew install node@20 (if you have Homebrew)"
    echo ""
    exit 1
fi

echo "✅ Node.js detected: $(node --version)"
echo "✅ npm detected: $(npm --version)"
echo ""

# Navigate to project directory
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment" || exit

echo "📦 Installing npm packages..."
npm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development environment:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd '/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment'"
echo "  source venv/bin/activate"
echo "  python mcp_server.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd '/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment'"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:3000/chat"
echo ""
