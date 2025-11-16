# Navigation System Architecture

## Overview

The Agent Foundry platform uses a three-tier navigation system consisting of:
1. **Top Navigation Bar** - Consistent across all pages, contains branding and global controls
2. **Page-Specific Toolbar** - Optional toolbar for page-specific actions
3. **Left Sidebar** - Collapsible sidebar for platform-wide navigation

## Components

### 1. Top Navigation Bar (`TopNav`)

**Location:** `app/components/layout/TopNav.tsx`

**Layout:**
```
[Logo] Agent Foundry          [Current Page]          [Instance] | [Domain] | [Organization] | [User]
```

**Features:**
- **Left Side:** Agent Foundry logo and branding (links to home)
- **Center:** Current page name (automatically detected from route)
- **Right Side:**
  - **Instance Selector:** Switch between Dev/Staging/Prod environments
  - **Domain:** Current domain (e.g., "Retail Banking")
  - **Organization:** Current organization (e.g., "Ravenhelm AI")
  - **User Profile:** Avatar with dropdown menu

**User Profile Dropdown:**
- Displays user name and email
- Links to:
  - Profile page (`/profile`)
  - Preferences page (`/profile?tab=preferences`)
  - Logout action

**State Management:**
- Instance, domain, and organization settings are stored in `localStorage`
- User profile data is loaded from `localStorage` (key: `userProfile`)

### 2. Page-Specific Toolbar (`Toolbar`)

**Location:** `app/components/layout/Toolbar.tsx`

**Purpose:** Provides page-specific actions in a consistent, balanced layout directly under the TopNav.

**Usage Example:**
```tsx
import { Toolbar, type ToolbarAction } from "@/components/layout/Toolbar"
import { Save, Deploy, Plus } from "lucide-react"

const toolbarActions: ToolbarAction[] = [
  {
    icon: Plus,
    label: 'New',
    onClick: handleNew,
    variant: 'outline',
    tooltip: 'Create new item',
  },
  {
    icon: Save,
    label: 'Save',
    onClick: handleSave,
    disabled: !hasChanges,
    variant: 'default',
    tooltip: 'Save changes',
  },
  {
    icon: Deploy,
    label: 'Deploy',
    onClick: handleDeploy,
    variant: 'default',
    tooltip: 'Deploy to environment',
  },
]

// In your page component:
<Toolbar actions={toolbarActions} />
```

**Props:**
```tsx
interface ToolbarAction {
  icon: LucideIcon        // Icon component from lucide-react
  label: string           // Button label
  onClick?: () => void    // Click handler
  href?: string           // Optional link URL
  variant?: "default" | "ghost" | "outline" | "destructive"
  disabled?: boolean      // Disable button
  tooltip?: string        // Tooltip text
}

interface ToolbarProps {
  actions?: ToolbarAction[]
  title?: string          // Optional page title
  description?: string    // Optional page description
  className?: string
}
```

### 3. Left Navigation Sidebar (`LeftNav`)

**Location:** `app/components/layout/LeftNav.tsx`

**Features:**
- **Quant Logo** at the top
- **Collapsible:** Toggle button to collapse/expand
- **Platform Navigation:** Links to all major platform pages
- **Tooltips:** Show page names when collapsed
- **Version Info:** Shows "Agent Foundry v0.9.0-dev" at the bottom

**Navigation Items:**
- Dashboard (`/`)
- Agents (`/agents`)
- Forge (`/forge`)
- Playground (`/chat`)
- Domains (`/domains`)
- Tools (`/tools`)
- Channels (`/channels`)
- Deployments (`/deployments`)
- Monitoring (`/monitoring`)
- Datasets (`/datasets`)
- Marketplace (`/marketplace`)
- Admin (`/admin`)

**State:**
- Collapsed state is persisted in `localStorage` (key: `leftNavCollapsed`)

### 4. User Profile Page

**Location:** `app/profile/page.tsx`

**Features:**
- **Profile Tab:**
  - Avatar upload (JPG, PNG, GIF - max 2MB)
  - Full name editor
  - Email address editor
  - Auto-generated initials from name

- **Preferences Tab:**
  - Theme selector (Dark, Light, System)
  - Language selector (English, Español, Français, Deutsch, 日本語, 中文)
  - Extensible for additional preferences

**State Management:**
- Profile data stored in `localStorage` (key: `userProfile`)
- Preferences stored in `localStorage` (key: `userPreferences`)
- Save button in toolbar to persist changes

**Data Structure:**
```tsx
interface UserProfile {
  name: string
  email: string
  initials: string
  avatar?: string  // Base64 encoded image
}

interface UserPreferences {
  theme: 'dark' | 'light' | 'system'
  language: string
}
```

## Layout Structure

**Root Layout:** `app/layout.tsx`

```tsx
<div className="flex h-screen overflow-hidden">
  <LeftNav />
  <div className="flex-1 flex flex-col overflow-hidden">
    <TopNav />
    <main className="flex-1 overflow-auto">
      {children}  // Page content goes here
    </main>
  </div>
</div>
```

**Page Structure:**
```tsx
export default function YourPage() {
  const toolbarActions: ToolbarAction[] = [
    // ... your actions
  ]

  return (
    <div className="flex flex-col h-full">
      <Toolbar actions={toolbarActions} />

      <div className="flex-1 overflow-auto">
        {/* Your page content */}
      </div>
    </div>
  )
}
```

## Styling and Theme

All components use the Ravenhelm theme with consistent:
- Background colors: `bg-bg-0`, `bg-bg-1`, `bg-bg-2`
- Foreground colors: `fg-0`, `fg-1`, `fg-2`
- Border colors: `border-white/10`, `border-white/20`
- Primary accent: Blue (`blue-600`, `blue-500`)

## Migration Guide

### Updating Existing Pages

If your page currently uses the old `UnifiedHeader` or `PageHeader`:

1. **Remove the old header import:**
   ```tsx
   // Remove:
   import { UnifiedHeader } from '@/components/header/UnifiedHeader'
   // or
   import { PageHeader } from '@/components/shared'
   ```

2. **Import the new Toolbar:**
   ```tsx
   import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar'
   ```

3. **Define your toolbar actions:**
   ```tsx
   const toolbarActions: ToolbarAction[] = [
     {
       icon: YourIcon,
       label: 'Action Name',
       onClick: handleAction,
       variant: 'default',
       tooltip: 'Action description',
     },
   ]
   ```

4. **Replace the old header with the Toolbar:**
   ```tsx
   // Old:
   <PageHeader title="..." actions={...} />

   // New:
   <Toolbar actions={toolbarActions} />
   ```

## Examples

### Example 1: Agents Page
See `app/agents/page.tsx` for a complete example with:
- Refresh action
- Export action
- Create agent action

### Example 2: Forge Page
See `app/forge/page.tsx` for a complete example with:
- **File Operations:**
  - New - Create a new agent (with unsaved changes confirmation)
  - Open - Opens agent selection dialog
  - Save - Save current agent (disabled when no changes)
  - Save As - Save with a new name
  - Undo - Undo last change (with history tracking)
  - Redo - Redo last change
  - Deploy - Deploy to environment
- **Agent Selection Dialog:** (`app/forge/components/AgentOpenDialog.tsx`)
  - Search functionality
  - Shows agent status, environment, tags
  - Highlights currently open agent
  - Sortable by recent updates

### Example 3: Profile Page
See `app/profile/page.tsx` for a complete example with:
- Save changes action
- Tabs for different sections
- Form handling

## Best Practices

1. **Toolbar Actions:**
   - Keep toolbar actions to 3-5 items max for visual balance
   - Use descriptive tooltips
   - Disable actions when not applicable (e.g., save when no changes)
   - Use appropriate variants (`default` for primary actions, `ghost` for secondary)

2. **User Profile:**
   - Always load user profile from localStorage on mount
   - Provide visual feedback when saving
   - Validate image uploads (type and size)

3. **Navigation:**
   - Use the LeftNav for platform-wide navigation
   - Don't create custom navigation - use the provided components
   - Respect the collapsed state for user experience

## Advanced Features

### Forge File Operations

The Forge page demonstrates advanced file operation patterns:

**Undo/Redo System:**
- Maintains history of up to 50 states
- Tracks nodes and edges changes
- Prevents history pollution during undo/redo operations
- Keyboard shortcuts can be added (Cmd+Z, Cmd+Shift+Z)

**Unsaved Changes Tracking:**
- Automatically detects changes to nodes/edges
- Confirms before creating new agent with unsaved changes
- Auto-saves before deployment
- Save button disabled when no changes

**Agent Open Dialog:**
- Full-text search across agent name, display name, and description
- Visual indicators for current agent
- Status badges and environment tags
- Sorted by recent updates

## Future Enhancements

- [ ] Add support for breadcrumbs
- [ ] Add notification center to TopNav
- [ ] Add search functionality to TopNav
- [ ] Implement actual authentication/logout
- [ ] Add domain and organization switchers
- [ ] Add keyboard shortcuts for toolbar actions (Cmd+S for save, etc.)
- [ ] Add mobile responsive design
- [ ] Add drag-and-drop file import for Forge
- [ ] Add export functionality for agent configurations
