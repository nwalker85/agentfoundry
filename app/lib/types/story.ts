export type Priority = 'P0' | 'P1' | 'P2' | 'P3';
export type StoryStatus = 'Backlog' | 'Ready' | 'In Progress' | 'In Review' | 'Done';

export interface Story {
  id: string;
  title: string;
  epic_title: string | null;
  priority: Priority;
  status: StoryStatus;
  url: string;
  github_issue_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface StoriesResponse {
  stories: Story[];
  total_count: number;
  has_more: boolean;
}

export interface StoriesFilters {
  priorities: Priority[];
  statuses: StoryStatus[];
  epicTitle?: string;
  limit: number;
}
