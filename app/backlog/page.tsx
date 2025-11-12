'use client';

import { useState, useEffect } from 'react';
import { Story, StoriesFilters, StoriesResponse } from '@/app/lib/types/story';
import { StoryCard } from './components/StoryCard';
import { FilterSidebar } from './components/FilterSidebar';
import { 
  FunnelIcon, 
  ArrowPathIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

export default function BacklogPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSidebarOpen, setFilterSidebarOpen] = useState(false);
  const [filters, setFilters] = useState<StoriesFilters>({
    priorities: [],
    statuses: [],
    limit: 50,
  });

  const fetchStories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      params.append('limit', filters.limit.toString());
      
      if (filters.priorities.length > 0) {
        filters.priorities.forEach(p => params.append('priorities', p));
      }
      
      if (filters.statuses.length > 0) {
        filters.statuses.forEach(s => params.append('status', s));
      }
      
      if (filters.epicTitle) {
        params.append('epic_title', filters.epicTitle);
      }
      
      const response = await fetch(`/api/stories?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch stories: ${response.status}`);
      }
      
      const data: StoriesResponse = await response.json();
      setStories(data.stories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stories');
      console.error('Error fetching stories:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStories();
  }, [filters]);

  // Client-side search filtering
  const filteredStories = stories.filter(story => {
    if (!searchQuery) return true;
    
    const query = searchQuery.toLowerCase();
    return (
      story.title.toLowerCase().includes(query) ||
      story.epic_title?.toLowerCase().includes(query) ||
      story.priority.toLowerCase().includes(query) ||
      story.status.toLowerCase().includes(query)
    );
  });

  const activeFilterCount = 
    filters.priorities.length + 
    filters.statuses.length + 
    (filters.epicTitle ? 1 : 0);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Story Backlog
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {loading ? 'Loading...' : `${filteredStories.length} ${filteredStories.length === 1 ? 'story' : 'stories'}`}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Refresh Button */}
              <button
                onClick={fetchStories}
                disabled={loading}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
                title="Refresh stories"
              >
                <ArrowPathIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </button>
              
              {/* Filter Toggle (Mobile) */}
              <button
                onClick={() => setFilterSidebarOpen(!filterSidebarOpen)}
                className="lg:hidden relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <FunnelIcon className="w-5 h-5" />
                {activeFilterCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">
                    {activeFilterCount}
                  </span>
                )}
              </button>
            </div>
          </div>
          
          {/* Search Bar */}
          <div className="mt-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search stories by title, epic, priority, or status..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Filter Sidebar */}
          <FilterSidebar
            filters={filters}
            onFiltersChange={setFilters}
            isOpen={filterSidebarOpen}
            onClose={() => setFilterSidebarOpen(false)}
          />

          {/* Story List */}
          <main className="flex-1 min-w-0">
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-200">
                  {error}
                </p>
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : filteredStories.length === 0 ? (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
                  <FunnelIcon className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No stories found
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {searchQuery || activeFilterCount > 0
                    ? 'Try adjusting your filters or search query'
                    : 'No stories have been created yet'}
                </p>
                {(searchQuery || activeFilterCount > 0) && (
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setFilters({
                        priorities: [],
                        statuses: [],
                        limit: 50,
                      });
                    }}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                  >
                    Clear all filters
                  </button>
                )}
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredStories.map((story) => (
                  <StoryCard key={story.id} story={story} />
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
