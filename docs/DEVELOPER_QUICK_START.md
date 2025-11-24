# Developer Quick Start - Post Migration

## Quick Reference

### Route Structure

```
/ → Public welcome page (auto-redirects if authenticated)
/login → Public login page
/app → Protected dashboard (requires auth)
/app/* → All protected application routes
```

### Adding New Routes

#### Public Route (No Auth Required)

```typescript
// app/about/page.tsx
export default function AboutPage() {
  return <div>About Us</div>
}
```

#### Protected Route (Auth Required)

```typescript
// app/app/settings/page.tsx
export default function SettingsPage() {
  return <div>Settings</div>
}
```

### Navigation Links

#### From Public Pages

```typescript
import Link from "next/link"

// Link to login
<Link href="/login">Sign In</Link>

// Link to app (will redirect to login if not authenticated)
<Link href="/app">Dashboard</Link>
```

#### From Protected Pages

```typescript
import Link from "next/link"

// Link to dashboard
<Link href="/app">Dashboard</Link>

// Link to other protected routes
<Link href="/app/agents">Agents</Link>
<Link href="/app/forge">Forge</Link>
<Link href="/app/chat">Playground</Link>
```

### Using Session

```typescript
"use client"

import { useSession } from "next-auth/react"

export default function MyComponent() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return <div>Loading...</div>
  }

  if (status === "unauthenticated") {
    return <div>Not authenticated</div>
  }

  return <div>Welcome {session?.user?.name}</div>
}
```

### Programmatic Navigation

```typescript
"use client"

import { useRouter } from "next/navigation"

export default function MyComponent() {
  const router = useRouter()

  const handleClick = () => {
    router.push("/app/agents")
  }

  return <button onClick={handleClick}>Go to Agents</button>
}
```

### Import Paths

#### Components

```typescript
// Shared components (work from anywhere)
import { Button } from '@/components/ui/button';
import { LeftNav } from '@/components/layout/LeftNav';

// App-specific components
import { AtomIndicator } from '@/app/chat/components/AtomIndicator';
```

#### Utilities

```typescript
// Shared utilities (work from anywhere)
import { cn } from '@/lib/utils';
import { usePermissions } from '@/lib/hooks/usePermissions';
```

#### Types

```typescript
// Shared types (work from anywhere)
import type { Agent } from '@/types';
```

### Common Patterns

#### Protected Page with Loading State

```typescript
"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function ProtectedPage() {
  const { status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, router])

  if (status === "loading") {
    return <div>Loading...</div>
  }

  return <div>Protected Content</div>
}
```

#### Public Page with Auto-Redirect

```typescript
"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function PublicPage() {
  const { status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "authenticated") {
      router.replace("/app")
    }
  }, [status, router])

  return <div>Public Content</div>
}
```

## Development Workflow

### Starting the Dev Server

```bash
npm run dev
# or
docker-compose up
```

### Testing Routes

1. **Public Routes**: Visit `http://localhost:3000/` (should load without auth)
2. **Login**: Visit `http://localhost:3000/login` (should show Google sign-in)
3. **Protected Routes**: Visit `http://localhost:3000/app` (should redirect to
   login if not authenticated)

### Adding to Navigation

#### Left Navigation

Edit `app/components/layout/LeftNav.tsx`:

```typescript
const navItems: NavItem[] = [
  // ... existing items
  { icon: MyIcon, label: 'My Feature', href: `${APP_BASE}/my-feature` },
];
```

#### Top Navigation Page Config

Edit `app/components/layout/TopNav.tsx`:

```typescript
const PAGE_CONFIG: Record<string, PageConfig> = {
  // ... existing pages
  '/app/my-feature': { name: 'My Feature', icon: MyIcon },
};
```

## Troubleshooting

### "useSession must be wrapped in SessionProvider"

**Cause**: Component using `useSession` is outside the SessionProvider boundary
**Fix**: Ensure component is rendered within the app tree (under
`app/layout.tsx` or `app/app/layout.tsx`)

### "Cannot GET /my-route"

**Cause**: Route doesn't exist or is in wrong location **Fix**:

- Public routes go in `app/`
- Protected routes go in `app/app/`

### Middleware Redirect Loop

**Cause**: Middleware protecting routes that should be public **Fix**: Check
`middleware.ts` matcher - should only include `/app/:path*`

### Import Path Errors

**Cause**: Importing from moved routes **Fix**: Update import paths:

- `@/chat/...` → `@/app/chat/...`
- `@/agents/...` → `@/app/agents/...`
- etc.

## Best Practices

1. **Always use `/app` prefix for protected routes**
2. **Keep shared components in `app/components/`**
3. **Keep shared utilities in `app/lib/`**
4. **Use `useSession` for auth checks**
5. **Use `useRouter` for programmatic navigation**
6. **Test both authenticated and unauthenticated flows**
7. **Add loading states for better UX**
8. **Handle errors gracefully**

## Need Help?

- Check `docs/APP_ROUTE_MIGRATION.md` for detailed migration info
- Review existing pages in `app/app/` for examples
- Check Next.js docs: https://nextjs.org/docs/app
- Check NextAuth docs: https://next-auth.js.org/
