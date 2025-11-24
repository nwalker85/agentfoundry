# Forge Multi-Tab Implementation Plan

**Date:** 2025-11-16  
**Status:** 📝 In Progress

---

## Requirements

### 1. Multi-Tab Agent Editing

- Edit multiple agents simultaneously in separate tabs
- Switch between tabs without losing work
- Each tab has independent state (nodes, edges, history, selected node)
- Tab bar shows all open agents

### 2. Draft Agent Creation

- "New" button creates draft agent immediately
- Draft appears in new tab
- Tab shows "(Draft)" label
- Draft saved to localStorage for recovery

### 3. Unsaved Changes Protection

- Visual indicator (dot) on tabs with unsaved changes
- Warning when closing tab with unsaved changes
- Warning when navigating away from page with unsaved tabs
- Browser unload warning for unsaved work

### 4. Tab Management

- Close tabs with X button
- Maximum 10 tabs open
- Keyboard shortcuts:
  - `Cmd+T` - New tab
  - `Cmd+W` - Close active tab
  - `Cmd+1-9` - Switch to tab 1-9
  - `Cmd+Shift+[` / `]` - Navigate tabs

---

## Data Structure

### AgentTabState

```typescript
interface AgentTabState {
  id: string; // Unique tab ID
  metadata: AgentMetadata;
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  history: HistoryState[];
  historyIndex: number;
  hasUnsavedChanges: boolean;
  isDraft: boolean;
  isLoading: boolean;
  selectedAgent: Agent | null;
}
```

### State Management

```typescript
const [tabs, setTabs] = useState<AgentTabState[]>([]);
const [activeTabId, setActiveTabId] = useState<string | null>(null);

// Derived state
const activeTab = tabs.find((t) => t.id === activeTabId);
const activeNodes = activeTab?.nodes || [];
const activeEdges = activeTab?.edges || [];
```

---

## Implementation Steps

### Phase 1: Tab Infrastructure

1. **Create AgentTabs Component** ✅

   - Tab bar UI
   - Tab switching
   - Close buttons
   - Unsaved indicators

2. **Create useNavigationGuard Hook** ✅

   - Browser unload protection
   - Navigation confirmation

3. **Update State Management**
   - Convert single agent → array of tabs
   - Track active tab
   - Update helper functions

### Phase 2: Draft Creation

4. **Handle "New" Button**

   - Generate unique tab ID
   - Create draft agent metadata
   - Add to tabs array
   - Set as active tab
   - Show properties dialog (optional)

5. **Draft Persistence**
   - Save drafts to localStorage
   - Auto-recover on page load
   - Clear on successful save

### Phase 3: Tab Operations

6. **Tab Switching**

   - Update activeTabId
   - Preserve state of all tabs
   - Load active tab's state

7. **Tab Closing**

   - Check for unsaved changes
   - Show confirmation if needed
   - Remove from tabs array
   - Switch to another tab if available

8. **Save Per Tab**
   - Save only active tab
   - Update that tab's metadata
   - Mark as saved
   - Keep other tabs unchanged

### Phase 4: Keyboard Shortcuts

9. **Global Shortcuts**
   - `Cmd+T` - New draft agent
   - `Cmd+W` - Close active tab
   - `Cmd+S` - Save active agent
   - `Cmd+1-9` - Switch to tab by index

---

## File Changes Required

### New Files (2)

1. `app/app/forge/components/AgentTabs.tsx` ✅
2. `app/lib/hooks/useNavigationGuard.ts` ✅

### Modified Files (1)

3. `app/app/forge/page.tsx` - Complete refactor for tabs

---

## UI Layout

```
┌────────────────────────────────────────────────────────────┐
│ [New] [Open] [Save] [Save As] [Undo] [Redo]  [v1.0.0] [Deploy] │
├────────────────────────────────────────────────────────────┤
│ ● draft-1  x │ agent-2 ● x │ agent-3  x │  [+]           │ ← Tabs
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐        ┌──────────────────────┐  │
│  │                     │        │  Edit Node           │  │
│  │   Graph Canvas      │        │  ● Unsaved      [X]  │  │
│  │                     │        │  ─────────────────── │  │
│  │   (ReactFlow)       │        │  [💾 Save Changes]   │  │
│  │                     │        │  Label: [...]        │  │
│  └─────────────────────┘        └──────────────────────┘  │
│                                                             │
├────────────────────────────────────────────────────────────┤
│  Python Code Preview                                        │
│  ───────────────────────────────────────────────────────── │
│  # Python LangGraph code...                                 │
└────────────────────────────────────────────────────────────┘
```

---

## Key Features

### Tab Bar

- Shows all open agents
- Active tab highlighted (blue underline)
- Unsaved changes (amber dot)
- Draft label "(Draft)"
- Close button (X) per tab
- New button (+) at end
- Max 10 tabs warning

### Draft Creation

- Click "New" → Instant draft tab created
- Name: "draft-1", "draft-2", etc.
- Empty canvas ready to use
- No properties dialog required (optional)
- Saved to localStorage automatically

### Navigation Protection

- Browser close/refresh → "You have unsaved changes"
- Tab close with unsaved → Confirmation dialog
- Page navigation → Confirmation dialog (if any tab unsaved)

### Keyboard Efficiency

- `Cmd+T` → New draft
- `Cmd+W` → Close tab
- `Cmd+S` → Save active
- `Cmd+1` → Switch to tab 1
- `Cmd+2` → Switch to tab 2
- etc.

---

## Edge Cases

### Maximum Tabs

- Limit: 10 tabs
- New button disabled when at limit
- Warning message shown
- Close tabs to open new ones

### Last Tab Closing

- Always keep at least one tab
- Closing last tab → Show empty state
- Or auto-create new draft

### Duplicate Agent Names

- Append number suffix (agent, agent-2, agent-3)
- Prevent conflicts
- User can rename in properties

### Browser Refresh

- Auto-save all drafts to localStorage
- Recover on page load
- Show recovery dialog

---

## Testing Checklist

- [ ] Create new draft → Tab appears
- [ ] Switch between tabs → State preserved
- [ ] Close tab with unsaved → Warning shown
- [ ] Close tab without unsaved → No warning
- [ ] Browser refresh with drafts → Recovery works
- [ ] Save one tab → Other tabs unchanged
- [ ] Keyboard shortcuts work (Cmd+T, Cmd+W, Cmd+1-9)
- [ ] Maximum tabs → Button disabled
- [ ] Multiple unsaved tabs → Navigation warning
- [ ] Last tab → Cannot close (or empty state)

---

## Implementation Priority

### Must Have (P0)

1. ✅ AgentTabs component
2. ✅ useNavigationGuard hook
3. ⏳ Multi-tab state in ForgePage
4. ⏳ Draft creation on "New"
5. ⏳ Tab switching
6. ⏳ Tab closing with confirmation

### Should Have (P1)

7. ⏳ localStorage persistence
8. ⏳ Keyboard shortcuts
9. ⏳ Maximum tabs handling
10. ⏳ Navigation guard integration

### Nice to Have (P2)

11. ⏳ Tab reordering (drag & drop)
12. ⏳ Tab context menu (right-click)
13. ⏳ "Close others" / "Close all"
14. ⏳ Tab icons/colors by status

---

**Status:** Foundation complete, implementing multi-tab state management

**Next Step:** Refactor ForgePage.tsx for tab array state
