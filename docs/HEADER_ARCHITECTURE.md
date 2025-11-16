# Header Architecture Guide

**Version**: v0.9.0-dev
**Date**: January 16, 2025

---

## Overview

Agent Foundry uses two header systems depending on the page type:

1. **UnifiedHeader** - For full-screen specialized pages
2. **TopNav + LeftNav** - For standard application pages

---

## 1. UnifiedHeader

**File**: `app/components/header/UnifiedHeader.tsx`

### When to Use
- Full-screen editor pages (e.g., Forge)
- Pages that don't use the left sidebar
- Pages that need custom context-specific controls

### Features
- **Dual branding**: Quant Platform + Agent Foundry logos
- **Agent selector**: Dropdown with search for switching between agents
- **Environment selector**: Dev/Staging/Prod switcher
- **Custom actions**: Page-specific toolbar buttons
- **Organization switcher**: Quick org selection
- **User menu**: Profile and settings dropdown

### Structure
```
┌─────────────────────────────────────────────────────────────┐
│ [Quant Logo] | [Agent Foundry]  [Context Bar]  [Org] [User] │
└─────────────────────────────────────────────────────────────┘
```

### Usage Example
```tsx
import { UnifiedHeader } from '@/components/header/UnifiedHeader';
import { type HeaderAction } from '@/components/header/ActionButtons';

const actions: HeaderAction[] = [
  {
    id: 'save',
    label: 'Save',
    icon: Save,
    onClick: handleSave,
    loading: isSaving,
  },
  {
    id: 'deploy',
    label: 'Deploy',
    icon: Rocket,
    onClick: handleDeploy,
    variant: 'primary',
  },
];

<UnifiedHeader
  currentPage="Forge"
  agents={mockAgents}
  selectedAgent={selectedAgent}
  showAgentSelector={true}
  onAgentSelect={handleLoadAgent}
  onCreateAgent={handleCreateAgent}
  actions={actions}
/>
```

### Props
```typescript
interface UnifiedHeaderProps {
  currentPage?: string;              // Page identifier
  agents?: Agent[];                  // Available agents for dropdown
  selectedAgent?: Agent | null;      // Currently selected agent
  showAgentSelector?: boolean;       // Show/hide agent dropdown
  actions?: HeaderAction[];          // Custom action buttons
  onAgentSelect?: (agent: Agent) => void;  // Agent selection callback
  onCreateAgent?: () => void;        // Create new agent callback
}
```

---

## 2. TopNav + LeftNav

**Files**:
- `app/components/layout/TopNav.tsx`
- `app/components/layout/LeftNav.tsx`

### When to Use
- Standard application pages (Dashboard, Agents, Tools, etc.)
- Pages with left sidebar navigation
- List/detail pages

### Features
- **Agent Foundry branding**: Logo and name
- **Environment selector**: Dev/Staging/Prod with color coding
- **Organization switcher**: Org selection modal
- **App menu**: Quick access to Forge, Playground, DIS
- **User menu**: Profile and settings
- **Left sidebar**: Main navigation with collapsible mode

### Structure
```
┌─────────────────────────────────────────────────────────────┐
│ [AF Logo] [Env] ... [Apps] [Org] [User]                    │
└─────────────────────────────────────────────────────────────┘
┌─────┬───────────────────────────────────────────────────────┐
│     │                                                        │
│ Nav │  Page Content                                         │
│     │                                                        │
└─────┴───────────────────────────────────────────────────────┘
```

### Usage
TopNav and LeftNav are included in the root layout automatically.
No need to import on individual pages.

---

## Components

### AgentSelector
**File**: `app/components/header/AgentSelector.tsx`

Dropdown with search for selecting agents.

```tsx
<AgentSelector
  agents={mockAgents}
  selectedAgent={selectedAgent}
  onSelect={handleLoadAgent}
  onCreateNew={handleCreateAgent}
/>
```

**Features**:
- Searchable dropdown
- Status indicators (active/inactive)
- Create new agent button
- Click-outside to close

---

### EnvironmentSelector
**File**: `app/components/header/EnvironmentSelector.tsx`

Environment switcher with persistence.

```tsx
<EnvironmentSelector
  current={environment}
  onChange={handleEnvironmentChange}
/>
```

**Features**:
- Dev (blue), Staging (yellow), Prod (green) color coding
- Persists to localStorage
- Dropdown with all options

---

### ActionButtons
**File**: `app/components/header/ActionButtons.tsx`

Toolbar action buttons with consistent styling.

```tsx
const actions: HeaderAction[] = [
  {
    id: 'save',
    label: 'Save',
    icon: Save,
    onClick: handleSave,
    loading: isSaving,
    variant: 'default',  // default | primary | danger
  },
];

<ActionButtons actions={actions} />
```

**Features**:
- Loading states
- Disabled states
- Variant styling (default, primary, danger)
- Icon support

---

### Logos

#### AgentFoundryLogo
**File**: `app/components/logo/AgentFoundryLogo.tsx`

SVG logo with hexagonal forge symbol and blue-purple gradient.

```tsx
<AgentFoundryLogo className="h-8 w-8" />
```

#### QuantLogo
**File**: `app/components/logo/QuantLogo.tsx`

Placeholder Quant platform logo. Replace with official logo.

```tsx
<QuantLogo className="h-8 w-auto" />
```

**To use official Quant logo**:
1. Obtain logo from Quant team or https://quant.ai
2. Save to `public/logos/quant-logo.svg`
3. Update `QuantLogo.tsx` to use:
   ```tsx
   <img src="/logos/quant-logo.svg" alt="Quant" className={className} />
   ```

---

## Visual Specifications

### Sizing
- Header height: `56px` (h-14) - **Consistent with TopNav**
- Logo area (left): `320px` min-width
- User area (right): `200px` min-width
- Center toolbar: Flexible, centered
- Button height: `36px` (h-9)
- Logo height: `24px` (h-6)

### Colors
```css
--header-bg: #030712;        /* gray-950 */
--header-border: #1f2937;    /* gray-800 */
--toolbar-bg: #111827;       /* gray-900 */
--button-hover: #1f2937;     /* gray-800 */
```

### Spacing
- Tight: `8px` (gap-2)
- Normal: `12px` (gap-3)
- Loose: `16px` (gap-4, gap-6)

---

## Decision Guide

### Use UnifiedHeader when:
- ✅ Building a full-screen editor or specialized tool
- ✅ Need agent selection dropdown
- ✅ Need custom page-specific actions in toolbar
- ✅ Don't need left sidebar navigation
- ✅ Want dual Quant + Agent Foundry branding

**Examples**: Forge, Future visual editors

### Use TopNav + LeftNav when:
- ✅ Building standard CRUD pages
- ✅ Need left sidebar navigation
- ✅ List/detail page patterns
- ✅ Dashboard and management pages
- ✅ Following established app patterns

**Examples**: Dashboard, Agents, Tools, Deployments, Monitoring

---

## Migration Checklist

### Adding UnifiedHeader to a new page:

1. Import components:
```tsx
import { UnifiedHeader } from '@/components/header/UnifiedHeader';
import { type HeaderAction } from '@/components/header/ActionButtons';
```

2. Define actions array:
```tsx
const actions: HeaderAction[] = useMemo(() => [
  { id: 'save', label: 'Save', icon: Save, onClick: handleSave },
], [dependencies]);
```

3. Add header to page:
```tsx
<div className="flex flex-col h-screen">
  <UnifiedHeader
    currentPage="PageName"
    actions={actions}
  />
  {/* Page content */}
</div>
```

4. Remove old PageHeader if present

5. Update page container to `h-screen` instead of `h-full`

---

## Best Practices

### 1. Action Buttons
- Use clear, action-oriented labels ("Save", "Deploy", not "Click here")
- Show loading states during async operations
- Disable when action isn't available
- Use `variant: 'primary'` for primary actions
- Use `variant: 'danger'` for destructive actions

### 2. Agent Selection
- Only show agent selector when relevant (e.g., Forge, agent-specific tools)
- Handle loading states during agent switch
- Update page URL/state when agent changes
- Provide "Create New" option when applicable

### 3. Environment
- Environment is global (stored in localStorage)
- Changes affect all pages
- Use color coding for quick visual identification
- Consider adding environment-specific warnings for prod

### 4. Responsive Design
- UnifiedHeader is optimized for desktop (min-width: 1024px)
- Mobile users should use TopNav + LeftNav pattern
- Consider showing simplified header on smaller screens

---

## Examples

### Full Forge Implementation
See `app/forge/page.tsx` for complete example with:
- Agent selection
- Save/Deploy actions
- Error/success messaging
- Loading states
- Empty states

### Simple Page with Actions
```tsx
export default function MyPage() {
  const [isSaving, setIsSaving] = useState(false);

  const actions: HeaderAction[] = [
    {
      id: 'export',
      label: 'Export',
      icon: Download,
      onClick: () => console.log('Export'),
    },
  ];

  return (
    <div className="flex flex-col h-screen">
      <UnifiedHeader
        currentPage="My Page"
        actions={actions}
      />
      <div className="flex-1 p-8">
        {/* Content */}
      </div>
    </div>
  );
}
```

---

## Future Enhancements

### Planned
- [ ] Global search in header
- [ ] Notifications dropdown
- [ ] Quick command palette (Cmd+K)
- [ ] Breadcrumb navigation in header
- [ ] Workspace switcher (multi-tenant)

### Under Consideration
- [ ] Header customization per organization
- [ ] Keyboard shortcuts display
- [ ] Dark/light theme toggle
- [ ] Compact mode for smaller screens

---

*Last Updated: January 16, 2025*
*Version: v0.9.0-dev*
