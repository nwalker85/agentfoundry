'use client';

import { ExternalLink, FileText, Tag, Calendar, User } from 'lucide-react';

interface StoryCardProps {
  artifact: {
    type: string;
    data?: {
      title?: string;
      url?: string;
      priority?: string;
      epic?: string;
      assignee?: string;
      status?: string;
      createdAt?: string;
    };
  };
  isUser?: boolean;
}

export function StoryCard({ artifact, isUser = false }: StoryCardProps) {
  const { data } = artifact;

  const getPriorityColor = (priority?: string) => {
    switch (priority?.toLowerCase()) {
      case 'p0':
      case 'critical':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'p1':
      case 'high':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800';
      case 'p2':
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    }
  };

  return (
    <div
      className={`
      group rounded-lg border overflow-hidden transition-all duration-200
      ${
        isUser
          ? 'bg-blue-700 border-blue-500 hover:bg-blue-600'
          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md'
      }
    `}
    >
      {/* Header with Notion branding */}
      <div
        className={`
        flex items-center justify-between px-4 py-3 border-b
        ${isUser ? 'border-blue-600' : 'border-gray-100 dark:border-gray-700'}
      `}
      >
        <div className="flex items-center gap-2">
          {/* Notion Icon */}
          <div
            className={`
            p-1.5 rounded-md
            ${isUser ? 'bg-blue-600' : 'bg-black dark:bg-white'}
          `}
          >
            <svg
              className={`w-4 h-4 ${isUser ? 'text-white' : 'text-white dark:text-black'}`}
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 1.968c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.139c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z" />
            </svg>
          </div>
          <div>
            <p
              className={`text-sm font-semibold ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
            >
              Story Created
            </p>
            {data?.status && (
              <p
                className={`text-xs ${isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}
              >
                {data.status}
              </p>
            )}
          </div>
        </div>

        {data?.url && (
          <a
            href={data.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors
              ${
                isUser
                  ? 'bg-blue-600 hover:bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
              }
            `}
          >
            Open
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3 space-y-3">
        {/* Title */}
        {data?.title && (
          <div className="flex items-start gap-2">
            <FileText
              className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isUser ? 'text-blue-200' : 'text-gray-400 dark:text-gray-500'}`}
            />
            <p
              className={`text-sm font-medium ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
            >
              {data.title}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="flex flex-wrap gap-2">
          {data?.priority && (
            <span
              className={`
              inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border
              ${isUser ? 'bg-blue-600 text-white border-blue-500' : getPriorityColor(data.priority)}
            `}
            >
              <Tag className="w-3 h-3" />
              {data.priority}
            </span>
          )}

          {data?.epic && (
            <span
              className={`
              inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border
              ${
                isUser
                  ? 'bg-blue-600 text-white border-blue-500'
                  : 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border-purple-200 dark:border-purple-800'
              }
            `}
            >
              📚 {data.epic}
            </span>
          )}

          {data?.assignee && (
            <span
              className={`
              inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border
              ${
                isUser
                  ? 'bg-blue-600 text-white border-blue-500'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700'
              }
            `}
            >
              <User className="w-3 h-3" />
              {data.assignee}
            </span>
          )}

          {data?.createdAt && (
            <span
              className={`
              inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs
              ${isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}
            `}
            >
              <Calendar className="w-3 h-3" />
              {new Date(data.createdAt).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
