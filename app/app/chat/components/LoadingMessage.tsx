'use client';

export function LoadingMessage() {
  return (
    <div className="flex justify-start">
      <div className="max-w-2xl px-4 py-3 rounded-lg bg-white border border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
            />
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
            />
            <div
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
            />
          </div>
          <span className="text-sm text-gray-500">PM Agent is thinking...</span>
        </div>
      </div>
    </div>
  );
}
