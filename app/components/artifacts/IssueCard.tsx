'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  GitBranch, 
  GitPullRequest,
  MessageCircle,
  ExternalLink,
  Calendar,
  User,
  Tag,
  CheckCircle,
  Circle,
  Clock
} from 'lucide-react';

interface IssueData {
  id?: string;
  number?: number;
  title: string;
  description?: string;
  state?: 'open' | 'closed';
  labels?: string[];
  assignees?: string[];
  milestone?: string;
  url?: string;
  createdAt?: string;
  updatedAt?: string;
  comments?: number;
  linkedPR?: boolean;
}

interface IssueCardProps {
  data: IssueData;
  variant?: 'compact' | 'full';
  isUser?: boolean;
}

export function IssueCard({ data, variant = 'full', isUser = false }: IssueCardProps) {
  const labelColors: Record<string, string> = {
    'bug': 'bg-red-100 text-red-800 border-red-300',
    'enhancement': 'bg-blue-100 text-blue-800 border-blue-300',
    'documentation': 'bg-purple-100 text-purple-800 border-purple-300',
    'feature': 'bg-green-100 text-green-800 border-green-300',
    'help wanted': 'bg-yellow-100 text-yellow-800 border-yellow-300',
    'question': 'bg-pink-100 text-pink-800 border-pink-300',
    'wontfix': 'bg-gray-100 text-gray-800 border-gray-300',
    'duplicate': 'bg-gray-100 text-gray-800 border-gray-300',
    'invalid': 'bg-gray-100 text-gray-800 border-gray-300'
  };

  const getIssueBadge = () => {
    if (data.state === 'closed') {
      return (
        <div className="flex items-center gap-1.5 text-purple-600">
          <CheckCircle className="w-4 h-4" />
          <span className="text-sm font-medium">Closed</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 text-green-600">
        <Circle className="w-4 h-4" />
        <span className="text-sm font-medium">Open</span>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`
        rounded-xl overflow-hidden shadow-sm
        ${isUser 
          ? 'bg-blue-700/20 border border-blue-500' 
          : 'bg-white border border-gray-200'
        }
        hover:shadow-md transition-shadow duration-200
      `}
    >
      {/* Header */}
      <div className={`
        px-4 py-3 border-b flex items-center justify-between
        ${isUser ? 'border-blue-600 bg-blue-700/30' : 'border-gray-100 bg-gray-50'}
      `}>
        <div className="flex items-center gap-2">
          <div className={`
            p-1.5 rounded-lg
            ${isUser ? 'bg-blue-600' : 'bg-gray-900'}
          `}>
            <svg className="w-4 h-4 text-white" viewBox="0 0 16 16" fill="currentColor">
              <path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
            </svg>
          </div>
          <div>
            <span className={`text-xs ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>
              GitHub Issue
            </span>
            {data.number && (
              <span className={`
                ml-2 text-xs font-mono
                ${isUser ? 'text-blue-300' : 'text-gray-400'}
              `}>
                #{data.number}
              </span>
            )}
          </div>
        </div>
        {data.url && (
          <a
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              flex items-center gap-1 text-sm font-medium
              ${isUser 
                ? 'text-blue-200 hover:text-blue-100' 
                : 'text-gray-700 hover:text-gray-900'
              }
              transition-colors
            `}
          >
            Open in GitHub
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3 space-y-3">
        {/* Title and State */}
        <div className="flex items-start justify-between gap-3">
          <h3 className={`
            font-semibold text-lg flex-1
            ${isUser ? 'text-white' : 'text-gray-900'}
          `}>
            {data.title}
          </h3>
          {variant === 'full' && getIssueBadge()}
        </div>

        {/* Description */}
        {variant === 'full' && data.description && (
          <p className={`
            text-sm line-clamp-3
            ${isUser ? 'text-blue-100' : 'text-gray-600'}
          `}>
            {data.description}
          </p>
        )}

        {/* Labels */}
        {data.labels && data.labels.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {data.labels.map((label, idx) => (
              <span
                key={idx}
                className={`
                  px-2 py-0.5 rounded-full text-xs font-medium border
                  ${labelColors[label.toLowerCase()] || 'bg-gray-100 text-gray-700 border-gray-300'}
                `}
              >
                {label}
              </span>
            ))}
          </div>
        )}

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2">
          {/* Milestone */}
          {data.milestone && (
            <div className="flex items-center gap-2">
              <Clock className={`w-4 h-4 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
              <span className={`
                text-xs font-medium
                ${isUser ? 'text-blue-200' : 'text-gray-700'}
              `}>
                {data.milestone}
              </span>
            </div>
          )}

          {/* Assignees */}
          {data.assignees && data.assignees.length > 0 && (
            <div className="flex items-center gap-2">
              <User className={`w-4 h-4 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
              <span className={`
                text-xs
                ${isUser ? 'text-blue-200' : 'text-gray-600'}
              `}>
                {data.assignees.join(', ')}
              </span>
            </div>
          )}

          {/* Comments */}
          {data.comments !== undefined && (
            <div className="flex items-center gap-2">
              <MessageCircle className={`w-4 h-4 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
              <span className={`
                text-xs
                ${isUser ? 'text-blue-200' : 'text-gray-600'}
              `}>
                {data.comments} comments
              </span>
            </div>
          )}

          {/* Linked PR */}
          {data.linkedPR && (
            <div className="flex items-center gap-2">
              <GitPullRequest className={`w-4 h-4 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
              <span className={`
                text-xs
                ${isUser ? 'text-blue-200' : 'text-gray-600'}
              `}>
                PR linked
              </span>
            </div>
          )}

          {/* Created Date */}
          {data.createdAt && (
            <div className="flex items-center gap-2">
              <Calendar className={`w-4 h-4 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
              <span className={`
                text-xs
                ${isUser ? 'text-blue-200' : 'text-gray-500'}
              `}>
                {new Date(data.createdAt).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Footer with Branch Info */}
      {variant === 'full' && (
        <div className={`
          px-4 py-2 border-t flex items-center justify-between
          ${isUser ? 'border-blue-600 bg-blue-700/20' : 'border-gray-100 bg-gray-50'}
        `}>
          <div className="flex items-center gap-2">
            <GitBranch className={`w-3 h-3 ${isUser ? 'text-blue-300' : 'text-gray-400'}`} />
            <span className={`
              text-xs font-mono
              ${isUser ? 'text-blue-300' : 'text-gray-500'}
            `}>
              main
            </span>
          </div>
          <span className={`
            text-xs
            ${isUser ? 'text-blue-300' : 'text-gray-500'}
          `}>
            Created via Engineering Department
          </span>
        </div>
      )}
    </motion.div>
  );
}
