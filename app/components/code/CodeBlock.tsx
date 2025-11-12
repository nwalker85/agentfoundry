'use client';

import { Highlight, themes } from 'prism-react-renderer';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface CodeBlockProps {
  code: string;
  language: string;
  isUser?: boolean;
}

export function CodeBlock({ code, language, isUser = false }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const codeString = code.replace(/\n$/, '');

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4 rounded-lg overflow-hidden">
      {/* Language label and copy button */}
      <div className={`
        flex items-center justify-between px-4 py-2 text-xs font-mono
        ${isUser ? 'bg-blue-800 text-blue-200' : 'bg-gray-800 text-gray-300'}
      `}>
        <span className="font-medium uppercase">{language}</span>
        <button
          onClick={copyToClipboard}
          className={`
            flex items-center gap-1.5 px-2 py-1 rounded transition-colors
            ${isUser 
              ? 'bg-blue-700 hover:bg-blue-600 text-white' 
              : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
            }
          `}
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Syntax highlighted code */}
      <Highlight
        theme={themes.vsDark}
        code={codeString}
        language={language as any}
      >
        {({ className, style, tokens, getLineProps, getTokenProps }) => (
          <pre
            className={`${className} p-4 text-sm overflow-x-auto`}
            style={{
              ...style,
              backgroundColor: isUser ? '#1e40af' : '#1e293b', // blue-700 or slate-800
              margin: 0
            }}
          >
            {tokens.map((line, i) => (
              <div key={i} {...getLineProps({ line })}>
                <span className="inline-block w-8 text-right mr-4 select-none opacity-50">
                  {i + 1}
                </span>
                {line.map((token, key) => (
                  <span key={key} {...getTokenProps({ token })} />
                ))}
              </div>
            ))}
          </pre>
        )}
      </Highlight>
    </div>
  );
}
