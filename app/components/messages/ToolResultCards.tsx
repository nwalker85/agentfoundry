'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, CheckCircle2, Calendar, Target, Hash, Tag } from 'lucide-react';
import type { MessageArtifact } from '@/lib/types/chat';

interface ToolResultCardProps {
  artifact: MessageArtifact;
  isUser: boolean;
}

export function ToolResultCard({ artifact, isUser }: ToolResultCardProps) {
  if (artifact.type === 'story') {
    return <StoryCard artifact={artifact} isUser={isUser} />;
  }
  
  if (artifact.type === 'issue') {
    return <IssueCard artifact={artifact} isUser={isUser} />;
  }
  
  return null;
}

// Notion Story Card
function StoryCard({ artifact, isUser }: ToolResultCardProps) {
  const { data } = artifact;
  
  // Priority color mapping
  const priorityColors = {
    P0: 'text-red-600 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    P1: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
    P2: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800',
    P3: 'text-gray-600 bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-700'
  };
  
  const priority = data?.priority || 'P3';
  const priorityStyle = priorityColors[priority as keyof typeof priorityColors] || priorityColors.P3;
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={`
        group relative overflow-hidden rounded-lg border-2 shadow-md hover:shadow-lg transition-all
        ${isUser 
          ? 'bg-blue-50/50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
        }
      `}
    >
      {/* Notion Brand Header */}
      <div className={`
        flex items-center justify-between px-4 py-3 border-b
        ${isUser 
          ? 'bg-blue-100/50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' 
          : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
        }
      `}>
        <div className="flex items-center gap-2">
          {/* Notion Logo */}
          <div className="w-6 h-6 flex items-center justify-center">
            <NotionLogo />
          </div>
          <span className={`font-semibold text-sm ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
            Story Created
          </span>
        </div>
        
        {/* Priority Badge */}
        <span className={`px-2 py-1 rounded-md text-xs font-bold border ${priorityStyle}`}>
          {priority}
        </span>
      </div>
      
      {/* Story Content */}
      <div className="p-4 space-y-3">
        {/* Story Title */}
        <div>
          <h4 className={`font-semibold text-base leading-tight ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
            {data?.title || data?.story_title || 'Untitled Story'}
          </h4>
        </div>
        
        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {/* Epic */}
          {data?.epic && (
            <div className="flex items-start gap-2">
              <Target className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Epic
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {data.epic}
                </div>
              </div>
            </div>
          )}
          
          {/* Status */}
          {data?.status && (
            <div className="flex items-start gap-2">
              <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Status
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {data.status}
                </div>
              </div>
            </div>
          )}
          
          {/* Story Points */}
          {data?.story_points && (
            <div className="flex items-start gap-2">
              <Hash className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Story Points
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {data.story_points}
                </div>
              </div>
            </div>
          )}
          
          {/* Created Date */}
          {data?.created_at && (
            <div className="flex items-start gap-2">
              <Calendar className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Created
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {new Date(data.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Acceptance Criteria Preview */}
        {data?.acceptance_criteria && data.acceptance_criteria.length > 0 && (
          <div className={`
            pt-3 border-t
            ${isUser 
              ? 'border-blue-200 dark:border-blue-800' 
              : 'border-gray-200 dark:border-gray-700'
            }
          `}>
            <div className={`text-xs font-medium mb-1 ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
              Acceptance Criteria ({data.acceptance_criteria.length})
            </div>
            <div className="space-y-1">
              {data.acceptance_criteria.slice(0, 2).map((ac: string, idx: number) => (
                <div key={idx} className={`text-xs flex items-start gap-2 ${isUser ? 'text-blue-800 dark:text-blue-200' : 'text-gray-600 dark:text-gray-300'}`}>
                  <CheckCircle2 className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <span className="line-clamp-1">{ac}</span>
                </div>
              ))}
              {data.acceptance_criteria.length > 2 && (
                <div className={`text-xs italic ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`}>
                  +{data.acceptance_criteria.length - 2} more...
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Footer with Link */}
      {data?.url && (
        <div className={`
          px-4 py-3 border-t flex items-center justify-between
          ${isUser 
            ? 'bg-blue-100/50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' 
            : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
          }
        `}>
          <a 
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              inline-flex items-center gap-2 text-sm font-medium group/link
              ${isUser 
                ? 'text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100' 
                : 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300'
              }
              transition-colors
            `}
          >
            <span>View in Notion</span>
            <ExternalLink className="w-4 h-4 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
          </a>
        </div>
      )}
    </motion.div>
  );
}

// GitHub Issue Card
function IssueCard({ artifact, isUser }: ToolResultCardProps) {
  const { data } = artifact;
  
  // Label color mapping (GitHub default colors)
  const labelColorMap: Record<string, string> = {
    'bug': 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 border-red-200 dark:border-red-800',
    'enhancement': 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200 border-blue-200 dark:border-blue-800',
    'documentation': 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 border-purple-200 dark:border-purple-800',
    'priority/P0': 'bg-red-100 dark:bg-red-900/40 text-red-800 dark:text-red-200 border-red-200 dark:border-red-800',
    'priority/P1': 'bg-orange-100 dark:bg-orange-900/40 text-orange-800 dark:text-orange-200 border-orange-200 dark:border-orange-800',
    'source/agent-pm': 'bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 border-purple-200 dark:border-purple-800',
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2 }}
      className={`
        group relative overflow-hidden rounded-lg border-2 shadow-md hover:shadow-lg transition-all
        ${isUser 
          ? 'bg-blue-50/50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
        }
      `}
    >
      {/* GitHub Brand Header */}
      <div className={`
        flex items-center justify-between px-4 py-3 border-b
        ${isUser 
          ? 'bg-blue-100/50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' 
          : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
        }
      `}>
        <div className="flex items-center gap-2">
          {/* GitHub Logo */}
          <div className="w-6 h-6 flex items-center justify-center">
            <GitHubLogo />
          </div>
          <span className={`font-semibold text-sm ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
            Issue Created
          </span>
        </div>
        
        {/* Issue Number Badge */}
        {data?.number && (
          <span className={`
            px-2 py-1 rounded-md text-xs font-mono font-bold
            ${isUser 
              ? 'bg-blue-200 dark:bg-blue-800 text-blue-900 dark:text-blue-100' 
              : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
            }
          `}>
            #{data.number}
          </span>
        )}
      </div>
      
      {/* Issue Content */}
      <div className="p-4 space-y-3">
        {/* Issue Title */}
        <div>
          <h4 className={`font-semibold text-base leading-tight ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
            {data?.title || 'Untitled Issue'}
          </h4>
        </div>
        
        {/* Labels */}
        {data?.labels && data.labels.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {data.labels.map((label: string, idx: number) => {
              const colorClass = labelColorMap[label] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-600';
              return (
                <span
                  key={idx}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${colorClass}`}
                >
                  <Tag className="w-3 h-3" />
                  {label}
                </span>
              );
            })}
          </div>
        )}
        
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {/* Assignees */}
          {data?.assignees && data.assignees.length > 0 && (
            <div className="flex items-start gap-2">
              <div className={`w-4 h-4 mt-0.5 flex-shrink-0 rounded-full ${isUser ? 'bg-blue-600 dark:bg-blue-400' : 'bg-gray-500 dark:bg-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Assigned
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {data.assignees.join(', ')}
                </div>
              </div>
            </div>
          )}
          
          {/* Created Date */}
          {data?.created_at && (
            <div className="flex items-start gap-2">
              <Calendar className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`} />
              <div className="min-w-0">
                <div className={`text-xs font-medium ${isUser ? 'text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'}`}>
                  Created
                </div>
                <div className={`truncate ${isUser ? 'text-blue-900 dark:text-blue-100' : 'text-gray-900 dark:text-gray-100'}`}>
                  {new Date(data.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Story Link (if connected to a Notion story) */}
        {data?.story_url && (
          <div className={`
            pt-3 border-t flex items-center gap-2
            ${isUser 
              ? 'border-blue-200 dark:border-blue-800' 
              : 'border-gray-200 dark:border-gray-700'
            }
          `}>
            <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              <NotionLogo size={16} />
            </div>
            <a
              href={data.story_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`
                text-xs underline
                ${isUser 
                  ? 'text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100' 
                  : 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300'
                }
                transition-colors
              `}
            >
              View related story in Notion
            </a>
          </div>
        )}
      </div>
      
      {/* Footer with Link */}
      {data?.url && (
        <div className={`
          px-4 py-3 border-t flex items-center justify-between
          ${isUser 
            ? 'bg-blue-100/50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' 
            : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
          }
        `}>
          <a 
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              inline-flex items-center gap-2 text-sm font-medium group/link
              ${isUser 
                ? 'text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100' 
                : 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300'
              }
              transition-colors
            `}
          >
            <span>View on GitHub</span>
            <ExternalLink className="w-4 h-4 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
          </a>
        </div>
      )}
    </motion.div>
  );
}

// Notion Logo Component
function NotionLogo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M6.017 4.313l55.333 -4.087c6.797 -0.583 8.543 -0.19 12.817 2.917l17.663 12.443c2.913 2.14 3.883 2.723 3.883 5.053v68.243c0 4.277 -1.553 6.807 -6.99 7.193L24.467 99.967c-4.08 0.193 -6.023 -0.39 -8.16 -3.113L3.3 79.94c-2.333 -3.113 -3.3 -5.443 -3.3 -8.167V11.113c0 -3.497 1.553 -6.413 6.017 -6.8z" fill="#fff"/>
      <path fillRule="evenodd" clipRule="evenodd" d="M61.35 0.227l-55.333 4.087C1.553 4.7 0 7.617 0 11.113v60.66c0 2.724 0.967 5.053 3.3 8.167l13.007 16.913c2.137 2.723 4.08 3.307 8.16 3.113l64.257 -3.89c5.433 -0.387 6.99 -2.917 6.99 -7.193V20.64c0 -2.21 -0.873 -2.847 -3.443 -4.733L74.167 3.143c-4.273 -3.107 -6.02 -3.5 -12.817 -2.917zM25.92 19.523c-5.247 0.353 -6.437 0.433 -9.417 -1.99L8.927 11.507c-0.77 -0.78 -0.383 -1.753 0.793 -1.847l54.920 -3.89c4.953 -0.39 7.643 1.167 10.333 3.5l8.547 5.927c0.777 0.58 1.16 1.360 0.193 1.360l-57.793 3.307zM19.803 88.3V30.367c0 -2.53 0.777 -3.697 3.103 -3.893L86 22.78c2.14 -0.193 3.107 1.167 3.107 3.693v57.547c0 2.53 -0.39 4.67 -3.883 4.863l-60.377 3.5c-3.493 0.193 -5.043 -0.97 -5.043 -4.083zm59.6 -54.827c0.387 1.75 0 3.5 -1.75 3.7l-2.91 0.577v42.773c-2.527 1.36 -4.853 2.137 -6.797 2.137 -3.107 0 -3.883 -0.973 -6.21 -3.887l-19.03 -29.94v28.967l6.02 1.363s0 3.5 -4.857 3.5l-13.39 0.777c-0.39 -0.78 0 -2.723 1.357 -3.11l3.497 -0.97v-38.3L30.48 40.667c-0.39 -1.75 0.58 -4.277 3.3 -4.473l14.367 -0.967 19.8 30.327v-26.83l-5.047 -0.58c-0.39 -2.143 1.163 -3.7 3.103 -3.89l13.4 -0.78z" fill="#000"/>
    </svg>
  );
}

// GitHub Logo Component
function GitHubLogo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 98 96" xmlns="http://www.w3.org/2000/svg">
      <path fillRule="evenodd" clipRule="evenodd" d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z" fill="currentColor"/>
    </svg>
  );
}
