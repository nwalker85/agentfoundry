'use client';

import { useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { Button } from '@/components/ui/button';
import { Copy, Check, AlertCircle, FileCode, Download } from 'lucide-react';
import { useGraphCodeStore } from '@/lib/stores/graphCode.store';

// Dynamically import Monaco to avoid SSR issues
const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

/**
 * CodeTab - Shows Python LangGraph code in the bottom panel.
 * Only active when on /app/graphs/* routes.
 * Receives graph data via the graphCode store.
 */
export function CodeTab() {
  const { nodes, edges, agentName, pythonCode, isValid, errors } = useGraphCodeStore();
  const [copied, setCopied] = useState(false);
  const [showValidation, setShowValidation] = useState(false); // Start collapsed

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pythonCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([pythonCode], { type: 'text/x-python' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${agentName || 'agent'}_graph.py`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const hasNodes = nodes.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-fg-2" />
          <span className="text-sm font-medium text-fg-1">Python LangGraph Code</span>
          {!isValid && hasNodes && (
            <div className="flex items-center gap-1 text-xs text-red-400">
              <AlertCircle className="w-3 h-3" />
              {errors.length} error{errors.length !== 1 ? 's' : ''}
            </div>
          )}
          {isValid && hasNodes && (
            <div className="flex items-center gap-1 text-xs text-green-400">
              <Check className="w-3 h-3" />
              Valid
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {hasNodes && (
            <>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowValidation(!showValidation)}
                className="text-xs h-7"
              >
                {showValidation ? 'Hide' : 'Show'} Validation
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleDownload}
                className="border-white/10 h-7"
              >
                <Download className="w-3 h-3 mr-1" />
                Download
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCopy}
                className="border-white/10 h-7"
              >
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
            </>
          )}
        </div>
      </div>

      {/* Validation Errors */}
      {showValidation && !isValid && hasNodes && (
        <div className="px-4 py-2 bg-red-900/20 border-b border-red-600/30">
          <div className="text-xs font-medium text-red-400 mb-1">Validation Errors:</div>
          <ul className="text-xs text-red-300 space-y-0.5 list-disc list-inside">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Monaco Editor */}
      <div className="flex-1 relative min-h-0">
        {!hasNodes ? (
          /* Empty State */
          <div className="absolute inset-0 flex items-center justify-center bg-bg-1">
            <div className="text-center">
              <FileCode className="w-10 h-10 text-fg-3 mx-auto mb-2" />
              <p className="text-fg-2 text-sm">No graph data</p>
              <p className="text-fg-3 text-xs mt-1">Open a graph to see generated code</p>
            </div>
          </div>
        ) : (
          <Editor
            height="100%"
            language="python"
            value={pythonCode}
            theme="vs-dark"
            options={{
              readOnly: true,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              fontSize: 11,
              lineNumbers: 'on',
              renderWhitespace: 'selection',
              folding: true,
              automaticLayout: true,
              wordWrap: 'on',
            }}
          />
        )}
      </div>
    </div>
  );
}
