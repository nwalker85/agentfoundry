'use client';

import React, { useState } from 'react';
import {
  GitBranch,
  Calendar,
  Search,
  Plus,
  Trash2,
  Copy,
  ExternalLink,
  Workflow,
  Shield,
} from 'lucide-react';
import { GraphType } from './GraphTypeSelector';

interface Graph {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  graph_type: GraphType;
  channel?: string;
  organization_id?: string;
  domain_id?: string;
  version: string;
  status: string;
  updated_at: string;
  yaml_content?: string;
}

interface GraphGalleryProps {
  graphs: Graph[];
  selectedType: GraphType;
  onOpenGraph: (graph: Graph) => void;
  onNewGraph: () => void;
  onDuplicateGraph: (graph: Graph) => void;
  onDeleteGraph: (graph: Graph) => void;
}

export default function GraphGallery({
  graphs,
  selectedType,
  onOpenGraph,
  onNewGraph,
  onDuplicateGraph,
  onDeleteGraph,
}: GraphGalleryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'updated'>('updated');

  // Filter graphs by search query
  const filteredGraphs = graphs.filter((graph) => {
    const matchesSearch =
      graph.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      graph.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  // Sort graphs
  const sortedGraphs = [...filteredGraphs].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    }
    // Sort by updated_at descending
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  });

  const getGraphIcon = (type: GraphType) => {
    switch (type) {
      case 'user':
        return <GitBranch className="w-5 h-5" />;
      case 'channel':
        return <Workflow className="w-5 h-5" />;
      case 'system':
        return <Shield className="w-5 h-5" />;
    }
  };

  const getGraphBadgeColor = (type: GraphType) => {
    switch (type) {
      case 'user':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
      case 'channel':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300';
      case 'system':
        return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300';
    }
  };

  const getChannelBadgeColor = (channel?: string) => {
    switch (channel) {
      case 'chat':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';
      case 'voice':
        return 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300';
      case 'api':
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-300';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getNodeCount = (graph: Graph): number => {
    try {
      if (graph.yaml_content) {
        const yaml = JSON.parse(graph.yaml_content);
        return yaml?.spec?.graph?.nodes?.length || 0;
      }
    } catch (e) {
      // Ignore parse errors
    }
    return 0;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with search and controls */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search graphs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'name' | 'updated')}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
        >
          <option value="updated">Recently Updated</option>
          <option value="name">Name</option>
        </select>

        <button
          onClick={onNewGraph}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Graph
        </button>
      </div>

      {/* Graph cards grid */}
      {sortedGraphs.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <GitBranch className="w-16 h-16 mb-4 opacity-30" />
          <p className="text-lg font-medium">No graphs found</p>
          <p className="text-sm">
            {searchQuery
              ? 'Try a different search query'
              : `Create your first ${selectedType} graph to get started`}
          </p>
          {!searchQuery && (
            <button
              onClick={onNewGraph}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              Create New Graph
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedGraphs.map((graph) => (
            <div
              key={graph.id}
              className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-lg transition-shadow bg-white dark:bg-gray-800 group"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="text-gray-600 dark:text-gray-400">
                    {getGraphIcon(graph.graph_type)}
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                    {graph.display_name || graph.name}
                  </h3>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDuplicateGraph(graph);
                    }}
                    className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400"
                    title="Duplicate"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteGraph(graph);
                    }}
                    className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-600 dark:text-red-400"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2 h-10">
                {graph.description || 'No description'}
              </p>

              {/* Badges */}
              <div className="flex flex-wrap gap-2 mb-3">
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${getGraphBadgeColor(
                    graph.graph_type
                  )}`}
                >
                  {graph.graph_type}
                </span>
                {graph.channel && (
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${getChannelBadgeColor(
                      graph.channel
                    )}`}
                  >
                    {graph.channel}
                  </span>
                )}
                <span className="text-xs px-2 py-1 rounded-full font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                  {getNodeCount(graph)} nodes
                </span>
              </div>

              {/* Metadata */}
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-3">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{formatDate(graph.updated_at)}</span>
                </div>
                <span className="font-mono text-xs">v{graph.version}</span>
              </div>

              {/* Open button */}
              <button
                onClick={() => onOpenGraph(graph)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded-lg font-medium transition-colors text-sm"
              >
                <ExternalLink className="w-4 h-4" />
                Open Graph
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
