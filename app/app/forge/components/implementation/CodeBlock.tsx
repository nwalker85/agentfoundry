'use client';

import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import { Copy, Check, Code2 } from 'lucide-react';

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  readonly?: boolean;
  maxHeight?: string;
}

export function CodeBlock({
  code,
  language = 'python',
  title = 'Source Code',
  readonly = true,
  maxHeight = '400px',
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  return (
    <div className="flex flex-col border border-white/10 rounded-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-bg-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-fg-2" />
          <span className="text-xs font-medium text-fg-1">{title}</span>
          {readonly && (
            <span className="text-xs text-fg-3 bg-bg-4 px-2 py-0.5 rounded">Read-only</span>
          )}
        </div>

        <Button variant="ghost" size="sm" onClick={handleCopy} className="h-6 px-2 text-xs">
          {copied ? (
            <>
              <Check className="w-3 h-3 mr-1" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Code Editor */}
      <div style={{ height: maxHeight }}>
        <Editor
          value={code}
          language={language}
          theme="vs-dark"
          options={{
            readOnly: readonly,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 12,
            lineNumbers: 'on',
            renderWhitespace: 'selection',
            folding: true,
            wordWrap: 'on',
          }}
        />
      </div>
    </div>
  );
}
