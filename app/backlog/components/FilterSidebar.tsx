'use client';

import { Priority, StoryStatus, StoriesFilters } from '@/app/lib/types/story';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface FilterSidebarProps {
  filters: StoriesFilters;
  onFiltersChange: (filters: StoriesFilters) => void;
  isOpen: boolean;
  onClose: () => void;
}

const priorityOptions: Priority[] = ['P0', 'P1', 'P2', 'P3'];
const statusOptions: StoryStatus[] = ['Backlog', 'Ready', 'In Progress', 'In Review', 'Done'];

export function FilterSidebar({ filters, onFiltersChange, isOpen, onClose }: FilterSidebarProps) {
  const togglePriority = (priority: Priority) => {
    const newPriorities = filters.priorities.includes(priority)
      ? filters.priorities.filter(p => p !== priority)
      : [...filters.priorities, priority];
    onFiltersChange({ ...filters, priorities: newPriorities });
  };

  const toggleStatus = (status: StoryStatus) => {
    const newStatuses = filters.statuses.includes(status)
      ? filters.statuses.filter(s => s !== status)
      : [...filters.statuses, status];
    onFiltersChange({ ...filters, statuses: newStatuses });
  };

  const clearFilters = () => {
    onFiltersChange({
      priorities: [],
      statuses: [],
      epicTitle: undefined,
      limit: 50,
    });
  };

  const hasActiveFilters = filters.priorities.length > 0 || filters.statuses.length > 0 || filters.epicTitle;

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky top-0 left-0 h-screen lg:h-auto
          w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
          p-6 overflow-y-auto z-50
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filters
          </h2>
          <button
            onClick={onClose}
            className="lg:hidden p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="w-full mb-6 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            Clear All Filters
          </button>
        )}

        {/* Priority Filter */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Priority
          </h3>
          <div className="space-y-2">
            {priorityOptions.map((priority) => (
              <label
                key={priority}
                className="flex items-center gap-3 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={filters.priorities.includes(priority)}
                  onChange={() => togglePriority(priority)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:focus:ring-blue-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">
                  {priority}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Status Filter */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Status
          </h3>
          <div className="space-y-2">
            {statusOptions.map((status) => (
              <label
                key={status}
                className="flex items-center gap-3 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={filters.statuses.includes(status)}
                  onChange={() => toggleStatus(status)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 dark:border-gray-600 dark:focus:ring-blue-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white">
                  {status}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Epic Filter */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Epic
          </h3>
          <input
            type="text"
            value={filters.epicTitle || ''}
            onChange={(e) => onFiltersChange({ ...filters, epicTitle: e.target.value || undefined })}
            placeholder="Filter by epic name..."
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Results Limit */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Results Limit
          </h3>
          <select
            value={filters.limit}
            onChange={(e) => onFiltersChange({ ...filters, limit: parseInt(e.target.value) })}
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={10}>10 stories</option>
            <option value={25}>25 stories</option>
            <option value={50}>50 stories</option>
          </select>
        </div>
      </aside>
    </>
  );
}
