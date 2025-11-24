'use client';

import { MessageSquare, GitBranch } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface Prompt {
  type: string;
  condition: string | null;
  text: string;
}

interface PromptViewerProps {
  prompts: Prompt[];
  nodeId: string;
}

export function PromptViewer({ prompts, nodeId }: PromptViewerProps) {
  if (!prompts || prompts.length === 0) {
    return <div className="text-sm text-fg-3 italic px-3 py-2">No prompts found for this node</div>;
  }

  return (
    <div className="space-y-3">
      {prompts.map((prompt, index) => (
        <Card key={index} className="p-3 bg-bg-3 border-white/10">
          {/* Header */}
          <div className="flex items-start gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-blue-400 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-fg-1">
                  System Prompt {prompts.length > 1 ? `#${index + 1}` : ''}
                </span>
                {prompt.condition && (
                  <div className="flex items-center gap-1 text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded">
                    <GitBranch className="w-3 h-3" />
                    <span>Conditional</span>
                  </div>
                )}
              </div>

              {/* Condition */}
              {prompt.condition && (
                <div className="mb-2 p-2 bg-bg-4 border border-white/5 rounded text-xs">
                  <span className="text-fg-3">When: </span>
                  <code className="text-purple-300 font-mono">{prompt.condition}</code>
                </div>
              )}

              {/* Prompt Text */}
              <div className="text-sm text-fg-2 whitespace-pre-wrap font-mono bg-bg-4 p-3 rounded border border-white/5 leading-relaxed">
                {prompt.text}
              </div>
            </div>
          </div>
        </Card>
      ))}

      {/* Summary */}
      {prompts.length > 1 && (
        <div className="text-xs text-fg-3 px-2">
          {prompts.length} conditional prompts - behavior varies based on state
        </div>
      )}
    </div>
  );
}
