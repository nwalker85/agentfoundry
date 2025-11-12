# Backlog View Debugging Guide

**Last Updated:** November 12, 2025  
**Version:** v0.7.0

---

## Quick Debug Checklist

Run the automated debug script first:
```bash
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
chmod +x debug_backlog.sh
./debug_backlog.sh
```

This will check:
- ✅ Server status (MCP + Next.js)
- ✅ File structure
- ✅ Environment variables
- ✅ API endpoints
- ✅ Build status

---

## Common Issues & Solutions

### 1. Blank Page / White Screen

**Symptoms:**
- Page loads but shows nothing
- No error in browser console
- Network requests show 200 OK

**Causes & Solutions:**

**A. React Component Error**
```bash
# Check browser console (F12) for:
# "Error: Minified React error #..."
# or component render errors

# Solution: Check component syntax
# Open: app/backlog/page.tsx
# Look for missing imports or JSX syntax errors
```

**B. CSS Not Loading**
```bash
# Check if Tailwind is compiling
rm -rf .next
npm run dev

# Verify tailwind.config.js exists at root
ls -la tailwind.config.js
ls -la postcss.config.js
```

**C. TypeScript Compilation Error**
```bash
# Check Next.js terminal for TypeScript errors
# Look for lines like:
# "Type error: Property 'x' does not exist"

# Fix: Check type definitions in app/lib/types/story.ts
```

---

### 2. "Failed to Fetch Stories" Error

**Symptoms:**
- Red error banner at top of page
- Browser console shows fetch error
- Network tab shows failed request

**Debugging Steps:**

**A. Check MCP Server**
```bash
# Test MCP server directly
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# Should return JSON with stories array
# If not:
# 1. Check if MCP server is running: ps aux | grep mcp_server
# 2. Check MCP server logs in terminal
# 3. Verify port 8001 is not blocked: lsof -i :8001
```

**B. Check Next.js API Route**
```bash
# Test Next.js proxy
curl http://localhost:3000/api/stories?limit=5

# Should return same JSON as MCP server
# If not:
# 1. Check Next.js terminal for errors
# 2. Verify NEXT_PUBLIC_API_URL in .env.local
# 3. Check app/api/stories/route.ts for syntax errors
```

**C. Check CORS**
```bash
# Open browser DevTools (F12)
# Go to Console tab
# Look for CORS error:
# "Access to fetch at ... has been blocked by CORS policy"

# Solution: Check MCP server CORS config in mcp_server.py
# Should include:
# allow_origins=["http://localhost:3000"]
```

**D. Check Network Tab**
```
1. Open DevTools (F12) → Network tab
2. Reload page
3. Look for /api/stories request
4. Click on it and check:
   - Status code (should be 200)
   - Response Preview (should have JSON)
   - Headers (check Content-Type)
```

---

### 3. Stories Not Displaying (Empty State)

**Symptoms:**
- Page loads successfully
- Shows "No stories found"
- But you know stories exist in Notion

**Debugging Steps:**

**A. Check Notion API Connection**
```bash
# Verify Notion token is set
grep NOTION_API_TOKEN .env.local

# Test Notion API directly from MCP server
# In Python console:
python3
>>> from mcp.tools.notion import NotionTool
>>> import asyncio
>>> tool = NotionTool()
>>> result = asyncio.run(tool.list_top_stories({"limit": 5}))
>>> print(result)

# If error, check:
# 1. NOTION_API_TOKEN is valid
# 2. NOTION_DATABASE_STORIES_ID is correct
# 3. Notion integration has access to database
```

**B. Check Notion Database Schema**
```bash
# Verify database has expected fields:
# - Title (title type)
# - Priority (select type with P0-P3 options)
# - Status (rich_text type)
# - Epic (rich_text type)

# If schema mismatch, update mcp/tools/notion.py
# or update app/lib/types/story.ts to match
```

**C. Check MCP Server Logs**
```bash
# Look at MCP server terminal output
# Should show:
# "INFO: 127.0.0.1 - POST /api/tools/notion/list-stories"

# If errors, they'll appear here
# Common: "Notion API error: invalid_request"
```

**D. Use Mock Mode**
```bash
# Test without Notion API
# In .env.local, temporarily remove:
# NOTION_API_TOKEN=
# NOTION_DATABASE_STORIES_ID=

# MCP server will use mock mode
# Should return sample stories
```

---

### 4. Filters Not Working

**Symptoms:**
- Can click filters but nothing happens
- Story count doesn't change
- No API request in Network tab

**Debugging Steps:**

**A. Check Console for Errors**
```javascript
// Open Console (F12)
// Look for errors like:
// "Cannot read property 'length' of undefined"
// "TypeError: filters.priorities.forEach is not a function"

// This indicates state management issue
```

**B. Check Filter State**
```javascript
// Add temporary debugging in app/backlog/page.tsx
// After line "const [filters, setFilters] = useState<StoriesFilters>({"

useEffect(() => {
  console.log('Filters changed:', filters);
}, [filters]);

// Reload page and check console when clicking filters
// Should log filter changes
```

**C. Verify FilterSidebar Props**
```typescript
// Check app/backlog/components/FilterSidebar.tsx
// Verify props are correctly typed:

interface FilterSidebarProps {
  filters: StoriesFilters;           // ✓ Should match
  onFiltersChange: (filters: StoriesFilters) => void;  // ✓ Should match
  isOpen: boolean;
  onClose: () => void;
}

// Common issue: prop name mismatch or wrong type
```

---

### 5. Dark Mode Not Working

**Symptoms:**
- Dark mode toggle doesn't work
- Colors don't change
- Some components light, some dark

**Debugging Steps:**

**A. Check ThemeProvider**
```typescript
// Verify app/layout.tsx has ThemeProvider wrapper
// Should look like:

import { ThemeProvider } from './components/providers/ThemeProvider'

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**B. Check Tailwind Config**
```javascript
// Verify tailwind.config.js has darkMode setting
module.exports = {
  darkMode: 'class',  // ← Must be 'class'
  // ...
}
```

**C. Test Dark Classes**
```bash
# In browser DevTools:
# 1. Inspect any element
# 2. Check if <html> has 'dark' class when in dark mode
# 3. If not, ThemeProvider isn't working

# 4. Manually add 'dark' class to test:
document.documentElement.classList.add('dark')

# If styles change, ThemeProvider is the issue
# If not, Tailwind dark: variants aren't compiled
```

---

### 6. Mobile View Issues

**Symptoms:**
- Layout broken on mobile
- Filter sidebar doesn't collapse
- Text overflows

**Debugging Steps:**

**A. Test Responsive Breakpoints**
```bash
# In DevTools:
# 1. Toggle device toolbar (Cmd+Shift+M / Ctrl+Shift+M)
# 2. Test these widths:
#    - 375px (iPhone SE)
#    - 768px (iPad portrait) 
#    - 1024px (iPad landscape)

# Filter sidebar should be:
# - Overlay on mobile (< 1024px)
# - Persistent on desktop (>= 1024px)
```

**B. Check Tailwind Breakpoints**
```typescript
// Verify responsive classes are used correctly
// In FilterSidebar.tsx:

className="
  fixed lg:sticky    // ← Fixed on mobile, sticky on lg+
  lg:translate-x-0   // ← Hidden on mobile, visible on lg+
"

// If wrong, check Tailwind breakpoints:
// sm: 640px, md: 768px, lg: 1024px, xl: 1280px
```

---

### 7. Performance Issues (Slow Loading)

**Symptoms:**
- Page takes >3 seconds to load
- Filters lag when clicking
- Scrolling is janky

**Debugging Steps:**

**A. Check API Response Time**
```bash
# Time the API request
time curl http://localhost:3000/api/stories?limit=50

# Should be < 2 seconds
# If slower:
# 1. Check Notion API performance
# 2. Reduce limit parameter
# 3. Add caching (future enhancement)
```

**B. Check Bundle Size**
```bash
# Build production bundle
npm run build

# Look for size warnings:
# "⚠ Compiled with warnings"
# "Large bundle detected"

# Check .next/standalone for large files
du -sh .next/standalone
```

**C. Profile React Performance**
```javascript
// In browser:
// 1. Open DevTools → Performance tab
// 2. Click Record
// 3. Interact with page (filters, search)
// 4. Stop recording
// 5. Look for slow renders (yellow bars)

// Common culprits:
// - Rendering all stories without virtualization
// - Re-rendering StoryCard on every filter change
// - Heavy markdown parsing in cards
```

---

## Debugging Tools

### Browser DevTools

**Console Tab:**
- JavaScript errors
- Network fetch errors
- React errors
- Custom console.log statements

**Network Tab:**
- API request/response
- Status codes
- Response times
- Request headers
- CORS errors

**Elements Tab:**
- Inspect DOM structure
- Check applied CSS classes
- Test dark mode classes
- Mobile responsive layout

**React DevTools Extension:**
```bash
# Install React DevTools
# Chrome: https://chrome.google.com/webstore/detail/react-developer-tools/...
# Firefox: https://addons.mozilla.org/en-US/firefox/addon/react-devtools/

# Use to:
# - Inspect component props
# - Check state values
# - Profile component renders
# - Debug context values
```

### Server Logs

**MCP Server Terminal:**
```bash
# Start with verbose logging
python mcp_server.py

# Look for:
# - API request logs
# - Error stack traces
# - Tool execution logs
# - Notion API responses
```

**Next.js Terminal:**
```bash
# Start dev server
npm run dev

# Look for:
# - Compilation errors
# - TypeScript errors
# - Module not found errors
# - Hot reload failures
```

### Curl Commands

**Test MCP Server:**
```bash
# Health check
curl http://localhost:8001/health

# List stories
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'

# With filters
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "priorities": ["P0", "P1"],
    "status": ["Ready"]
  }'
```

**Test Next.js API:**
```bash
# Basic request
curl http://localhost:3000/api/stories?limit=5

# With filters
curl 'http://localhost:3000/api/stories?limit=10&priorities=P0&priorities=P1&status=Ready'

# Check status
curl http://localhost:3000/api/status
```

---

## Environment Variable Issues

### Required Variables

```bash
# Check .env.local exists
ls -la .env.local

# Check required variables (don't expose values)
grep -E 'OPENAI_API_KEY|NEXT_PUBLIC_API_URL' .env.local

# Should show:
# OPENAI_API_KEY=sk-...
# NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Common Mistakes

**Wrong Variable Name:**
```bash
# WRONG (client-side variables must start with NEXT_PUBLIC_)
API_URL=http://localhost:8001

# CORRECT
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Variable Not Loading:**
```bash
# Restart dev server after changing .env.local
# Environment variables are only loaded at startup

# Stop dev server (Ctrl+C)
npm run dev
```

**Using .env instead of .env.local:**
```bash
# Next.js loads files in this order:
# 1. .env.local (highest priority, gitignored)
# 2. .env.development
# 3. .env

# Always use .env.local for local development
```

---

## Code-Level Debugging

### Add Debug Logs

**In React Components:**
```typescript
// app/backlog/page.tsx

const fetchStories = async () => {
  console.log('🔍 Fetching stories with filters:', filters);
  
  try {
    const params = new URLSearchParams();
    params.append('limit', filters.limit.toString());
    console.log('📤 Request params:', params.toString());
    
    const response = await fetch(`/api/stories?${params.toString()}`);
    console.log('📥 Response status:', response.status);
    
    const data = await response.json();
    console.log('📊 Data received:', data);
    
    setStories(data.stories);
    console.log('✅ Stories updated:', data.stories.length);
  } catch (err) {
    console.error('❌ Error:', err);
  }
};
```

**In API Routes:**
```typescript
// app/api/stories/route.ts

export async function GET(request: NextRequest) {
  console.log('🔍 API route called');
  
  const searchParams = request.nextUrl.searchParams;
  console.log('📤 Search params:', Object.fromEntries(searchParams));
  
  const requestBody = { /* ... */ };
  console.log('📤 Request body:', requestBody);
  
  const response = await fetch(url, { /* ... */ });
  console.log('📥 MCP response status:', response.status);
  
  const data = await response.json();
  console.log('📊 MCP data:', data);
  
  return NextResponse.json(data);
}
```

### TypeScript Type Checking

```bash
# Run TypeScript compiler
npx tsc --noEmit

# Should show any type errors
# Fix before running dev server
```

### React Error Boundaries

```typescript
// Add error boundary to catch React errors
// app/backlog/error.tsx

'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
      <p className="text-red-600 mb-4">{error.message}</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Try again
      </button>
    </div>
  );
}
```

---

## Getting Help

### Information to Gather

When asking for help, provide:

1. **Error Messages:**
   - Browser console errors (full stack trace)
   - Server terminal output
   - Network tab errors

2. **Environment:**
   - Node version: `node --version`
   - npm version: `npm --version`
   - Python version: `python --version`
   - OS: `uname -a`

3. **Steps to Reproduce:**
   - What you clicked/typed
   - What you expected
   - What actually happened

4. **Debug Script Output:**
   ```bash
   ./debug_backlog.sh > debug_output.txt 2>&1
   # Share debug_output.txt
   ```

### Quick Fixes to Try First

1. **Restart Everything:**
   ```bash
   # Kill servers
   pkill -f mcp_server
   pkill -f next-server
   
   # Clear cache
   rm -rf .next
   
   # Restart
   python mcp_server.py & npm run dev
   ```

2. **Rebuild Node Modules:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Check Git Status:**
   ```bash
   git status
   # Make sure all new files are committed
   
   git diff
   # Check for unintended changes
   ```

---

## Success Criteria

When backlog view is working correctly, you should see:

✅ Page loads in < 1 second  
✅ Stories display in cards  
✅ Filters can be clicked and applied  
✅ Search bar filters in real-time  
✅ Links to Notion open correctly  
✅ Dark mode toggle works  
✅ Mobile responsive (sidebar collapses)  
✅ No errors in browser console  
✅ No errors in server terminals  

---

**Last Updated:** November 12, 2025  
**Version:** v0.7.0  
**Document Owner:** Development Team
