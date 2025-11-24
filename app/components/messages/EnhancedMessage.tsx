'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { motion } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import type { ChatMessage } from '@/lib/types/chat';
import { CodeBlock } from '@/components/code/CodeBlock';
import { ToolResultCard } from './ToolResultCards';

interface EnhancedMessageProps {
  message: ChatMessage;
  isGrouped?: boolean;
  showTimestamp?: boolean;
  onRetry?: () => void;
}

export function EnhancedMessage({
  message,
  isGrouped = false,
  showTimestamp = true,
  onRetry,
}: EnhancedMessageProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const isUser = message.role === 'user';

  const messageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  };

  // Truncate message for display if collapsed
  const displayContent =
    !isExpanded && message.content.length > 500
      ? message.content.substring(0, 497) + '...'
      : message.content;

  return (
    <motion.div
      variants={messageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} ${isGrouped ? 'mt-1' : 'mt-4'}`}
    >
      <div className={`max-w-2xl ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Avatar and Name (only if not grouped) */}
        {!isGrouped && (
          <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : ''}`}>
            <div
              className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}
            `}
            >
              {isUser ? 'U' : 'PM'}
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {isUser ? 'You' : 'PM Agent'}
            </span>
            {showTimestamp && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
              </span>
            )}
          </div>
        )}

        {/* Message Content */}
        <div
          className={`
            px-4 py-3 rounded-2xl shadow-sm
            ${
              isUser
                ? 'bg-blue-600 text-white rounded-br-sm'
                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-sm'
            }
          `}
        >
          {/* Markdown Content */}
          <div
            className={`prose ${isUser ? 'prose-invert' : 'dark:prose-invert'} max-w-none prose-sm`}
          >
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              components={{
                // Enhanced headings with better hierarchy
                h1({ children }) {
                  return (
                    <h1
                      className={`text-2xl font-bold mb-3 mt-4 ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
                    >
                      {children}
                    </h1>
                  );
                },
                h2({ children }) {
                  return (
                    <h2
                      className={`text-xl font-bold mb-2 mt-3 ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
                    >
                      {children}
                    </h2>
                  );
                },
                h3({ children }) {
                  return (
                    <h3
                      className={`text-lg font-semibold mb-2 mt-3 ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
                    >
                      {children}
                    </h3>
                  );
                },
                h4({ children }) {
                  return (
                    <h4
                      className={`text-base font-semibold mb-1 mt-2 ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
                    >
                      {children}
                    </h4>
                  );
                },
                h5({ children }) {
                  return (
                    <h5
                      className={`text-sm font-semibold mb-1 mt-2 ${isUser ? 'text-white' : 'text-gray-900 dark:text-gray-100'}`}
                    >
                      {children}
                    </h5>
                  );
                },
                h6({ children }) {
                  return (
                    <h6
                      className={`text-sm font-medium mb-1 mt-2 ${isUser ? 'text-blue-100' : 'text-gray-700 dark:text-gray-300'}`}
                    >
                      {children}
                    </h6>
                  );
                },
                // Code blocks with syntax highlighting
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  const codeString = String(children).replace(/\n$/, '');
                  const language = match ? match[1] : 'text';

                  if (!inline && match) {
                    return <CodeBlock code={codeString} language={language} isUser={isUser} />;
                  }

                  return (
                    <code
                      className={`
                      px-1.5 py-0.5 rounded font-mono text-sm
                      ${isUser ? 'bg-blue-700 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}
                    `}
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
                // Enhanced links with external indicator
                a({ href, children }) {
                  const isExternal = href?.startsWith('http');
                  return (
                    <a
                      href={href}
                      target={isExternal ? '_blank' : undefined}
                      rel={isExternal ? 'noopener noreferrer' : undefined}
                      className={`
                        inline-flex items-center gap-1 underline underline-offset-2 hover:no-underline
                        ${isUser ? 'text-blue-200 hover:text-blue-100' : 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300'}
                      `}
                    >
                      {children}
                      {isExternal && <ExternalLink className="w-3 h-3" />}
                    </a>
                  );
                },
                // Prevent div inside p errors
                p({ children }) {
                  return <div className="mb-2 last:mb-0">{children}</div>;
                },
                // Enhanced tables with striped rows
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-4 rounded-lg border border-gray-200 dark:border-gray-700">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        {children}
                      </table>
                    </div>
                  );
                },
                thead({ children }) {
                  return (
                    <thead className={`${isUser ? 'bg-blue-700' : 'bg-gray-50 dark:bg-gray-800'}`}>
                      {children}
                    </thead>
                  );
                },
                tbody({ children }) {
                  return (
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {children}
                    </tbody>
                  );
                },
                tr({ children }) {
                  return (
                    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                      {children}
                    </tr>
                  );
                },
                th({ children }) {
                  return (
                    <th
                      className={`
                      px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider
                      ${isUser ? 'text-white' : 'text-gray-700 dark:text-gray-300'}
                    `}
                    >
                      {children}
                    </th>
                  );
                },
                td({ children }) {
                  return (
                    <td
                      className={`px-4 py-2 text-sm ${isUser ? 'text-blue-100' : 'text-gray-700 dark:text-gray-300'}`}
                    >
                      {children}
                    </td>
                  );
                },
                // Enhanced blockquotes
                blockquote({ children }) {
                  return (
                    <blockquote
                      className={`
                      border-l-4 pl-4 py-2 my-3 italic
                      ${
                        isUser
                          ? 'border-blue-400 bg-blue-700/30 text-blue-100'
                          : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 text-gray-700 dark:text-gray-300'
                      }
                    `}
                    >
                      {children}
                    </blockquote>
                  );
                },
                // Task lists (GFM checkboxes)
                input({ type, checked, ...props }) {
                  if (type === 'checkbox') {
                    return (
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled
                        className="mr-2 rounded"
                        {...props}
                      />
                    );
                  }
                  return <input type={type} {...props} />;
                },
                // Enhanced lists
                ul({ children, className }) {
                  // Task list detection
                  const isTaskList = className?.includes('contains-task-list');
                  return (
                    <ul
                      className={`
                      ${isTaskList ? 'space-y-1' : 'list-disc list-inside space-y-1'} 
                      my-3
                    `}
                    >
                      {children}
                    </ul>
                  );
                },
                ol({ children }) {
                  return <ol className="list-decimal list-inside space-y-1 my-3">{children}</ol>;
                },
                li({ children, className }) {
                  const isTaskItem = className?.includes('task-list-item');
                  return <li className={`${isTaskItem ? 'flex items-start' : ''}`}>{children}</li>;
                },
                // Horizontal rules
                hr() {
                  return (
                    <hr
                      className={`
                      my-4 border-t
                      ${isUser ? 'border-blue-400' : 'border-gray-300 dark:border-gray-600'}
                    `}
                    />
                  );
                },
                // Strikethrough (GFM)
                del({ children }) {
                  return (
                    <del
                      className={`${isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}`}
                    >
                      {children}
                    </del>
                  );
                },
                // Strong emphasis
                strong({ children }) {
                  return <strong className="font-bold">{children}</strong>;
                },
                // Emphasis
                em({ children }) {
                  return <em className="italic">{children}</em>;
                },
              }}
            >
              {displayContent}
            </ReactMarkdown>
          </div>

          {/* Collapsible for long messages */}
          {message.content.length > 500 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`
                mt-2 text-sm flex items-center gap-1 
                ${isUser ? 'text-blue-200' : 'text-gray-500 dark:text-gray-400'}
                hover:underline
              `}
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Show more
                </>
              )}
            </button>
          )}
        </div>

        {/* Artifacts */}
        {message.artifacts && message.artifacts.length > 0 && (
          <div className="mt-2 space-y-2">
            {message.artifacts.map((artifact, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 * idx }}
              >
                <ToolResultCard artifact={artifact} isUser={isUser} />
              </motion.div>
            ))}
          </div>
        )}

        {/* Error State */}
        {message.error && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2"
          >
            <ErrorCard error={message.error} onRetry={onRetry} isUser={isUser} />
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

// Error Card Component

function ErrorCard({ error, onRetry, isUser }: any) {
  return (
    <div
      className={`
      p-3 rounded-lg border
      ${isUser ? 'bg-red-900/20 border-red-700' : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'}
    `}
    >
      <div className="flex items-start gap-2">
        <span className="text-red-500 dark:text-red-400">⚠️</span>
        <div className="flex-1">
          <p className={`text-sm ${isUser ? 'text-red-200' : 'text-red-700 dark:text-red-300'}`}>
            {error}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className={`
                mt-2 text-sm underline
                ${isUser ? 'text-red-300' : 'text-red-600 dark:text-red-400'}
              `}
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
