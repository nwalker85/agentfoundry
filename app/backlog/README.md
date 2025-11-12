# Backlog View

The `/backlog` route provides a comprehensive view of all stories in your Notion workspace.

## Features

### Story Cards
- **Priority badges**: Visual indicators for P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- **Status badges**: Color-coded status (Backlog, Ready, In Progress, In Review, Done)
- **Epic association**: Shows which epic each story belongs to
- **Direct links**: Quick access to both Notion pages and GitHub issues
- **Metadata**: Created date and last updated information

### Filtering & Search
- **Priority filter**: Select one or more priorities (P0-P3)
- **Status filter**: Filter by workflow status
- **Epic filter**: Search for stories within specific epics
- **Text search**: Client-side search across title, epic, priority, and status
- **Results limit**: Adjustable (10, 25, or 50 stories)

### UI/UX
- **Responsive design**: Works on desktop and mobile
- **Dark mode support**: Matches application theme
- **Smooth animations**: Framer Motion for polished interactions
- **Loading states**: Clear feedback during data fetching
- **Empty states**: Helpful messages when no stories found
- **Mobile sidebar**: Collapsible filter sidebar on mobile devices

## Usage

1. Navigate to http://localhost:3000/backlog
2. Use filters on the left sidebar to narrow down stories
3. Use the search bar to find specific stories
4. Click story links to open in Notion or GitHub
5. Click refresh button to reload latest stories

## API Integration

The backlog view integrates with the MCP server's `/api/tools/notion/list-stories` endpoint:

```typescript
// Request filters
{
  limit: 50,
  priorities: ['P0', 'P1'],
  status: ['Ready', 'In Progress'],
  epic_title: 'Platform Hardening'
}

// Response
{
  stories: Story[],
  total_count: number,
  has_more: boolean
}
```

## Components

- **`page.tsx`**: Main page component with state management
- **`StoryCard.tsx`**: Individual story display card
- **`FilterSidebar.tsx`**: Filter controls sidebar

## Types

See `app/lib/types/story.ts` for TypeScript definitions:
- `Story`: Complete story data structure
- `Priority`: P0 | P1 | P2 | P3
- `StoryStatus`: Backlog | Ready | In Progress | In Review | Done
- `StoriesFilters`: Filter configuration
- `StoriesResponse`: API response structure
