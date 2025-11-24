'use client';

import { useMemo, useState } from 'react';
import { Node, Edge } from 'reactflow';
import Editor from '@monaco-editor/react';
import { graphToPython, validatePython } from '../lib/graph-to-python';
import { Button } from '@/components/ui/button';
import { Copy, Check, AlertCircle, FileCode } from 'lucide-react';
import type { StateSchema, TriggerDefinition } from '@/types';

interface PythonCodePreviewProps {
  nodes: Node[];
  edges: Edge[];
  agentName: string;
  stateSchema: StateSchema | null;
  triggers: TriggerDefinition[];
}

export function PythonCodePreview({
  nodes,
  edges,
  agentName,
  stateSchema,
  triggers,
}: PythonCodePreviewProps) {
  const [copied, setCopied] = useState(false);
  const [showValidation, setShowValidation] = useState(true);

  // Generate Python code from graph
  const pythonCode = useMemo(() => {
    return graphToPython(nodes, edges, agentName, {
      stateSchema,
      triggers,
    });
  }, [nodes, edges, agentName, stateSchema, triggers]);

  // Validate Python code
  const validation = useMemo(() => {
    return validatePython(pythonCode);
  }, [pythonCode]);

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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/10">
        <div className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-fg-2" />
          <span className="text-sm font-medium text-fg-1">Python LangGraph Code</span>
          {!validation.valid && (
            <div className="flex items-center gap-1 text-xs text-red-400">
              <AlertCircle className="w-3 h-3" />
              {validation.errors.length} error{validation.errors.length !== 1 ? 's' : ''}
            </div>
          )}
          {validation.valid && nodes.length > 0 && (
            <div className="flex items-center gap-1 text-xs text-green-400">
              <Check className="w-3 h-3" />
              Valid
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowValidation(!showValidation)}
            className="text-xs"
          >
            {showValidation ? 'Hide' : 'Show'} Validation
          </Button>
          <Button size="sm" variant="outline" onClick={handleDownload} className="border-white/10">
            Download
          </Button>
          <Button size="sm" variant="outline" onClick={handleCopy} className="border-white/10">
            {copied ? (
              <>
                <Check className="w-4 h-4 mr-1" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-1" />
                Copy
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Validation Errors */}
      {showValidation && !validation.valid && (
        <div className="px-4 py-2 bg-red-900/20 border-b border-red-600/30">
          <div className="text-xs font-medium text-red-400 mb-1">Validation Errors:</div>
          <ul className="text-xs text-red-300 space-y-0.5 list-disc list-inside">
            {validation.errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Monaco Editor */}
      <div className="flex-1 relative">
        {nodes.length === 0 ? (
          /* Empty State */
          <div className="absolute inset-0 flex items-center justify-center bg-bg-1">
            <div className="text-center">
              <FileCode className="w-12 h-12 text-fg-2 mx-auto mb-3" />
              <p className="text-fg-1 font-medium">No nodes yet</p>
              <p className="text-fg-2 text-sm mt-1">Add nodes to see the generated Python code</p>
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
              minimap: { enabled: true },
              scrollBeyondLastLine: false,
              fontSize: 12,
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
