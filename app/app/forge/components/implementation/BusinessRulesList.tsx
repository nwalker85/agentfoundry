'use client';

import { useState } from 'react';
import { Lightbulb, GitBranch, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { CodeBlock } from './CodeBlock';

interface Condition {
  type: string;
  test: string;
  branch: string;
}

interface BusinessRulesListProps {
  rules: string[];
  conditions: Condition[];
  functionCalls: string[];
  nodeId: string;
}

export function BusinessRulesList({
  rules,
  conditions,
  functionCalls,
  nodeId,
}: BusinessRulesListProps) {
  const [expandedMethod, setExpandedMethod] = useState<string | null>(null);
  const [methodSource, setMethodSource] = useState<Record<string, string>>({});
  const [loadingMethod, setLoadingMethod] = useState<string | null>(null);

  const hasRules = rules && rules.length > 0;
  const hasConditions = conditions && conditions.length > 0;
  const hasFunctionCalls = functionCalls && functionCalls.length > 0;
  const hasAny = hasRules || hasConditions || hasFunctionCalls;

  const fetchMethodSource = async (methodName: string) => {
    if (methodSource[methodName]) {
      // Already loaded, just toggle
      setExpandedMethod(expandedMethod === methodName ? null : methodName);
      return;
    }

    setLoadingMethod(methodName);
    try {
      const agentId = 'cibc-card-activation'; // TODO: Get from props/context
      const response = await fetch(
        `http://localhost:8000/api/agents/${agentId}/logic/business/${methodName}`
      );
      if (!response.ok) throw new Error('Failed to fetch method');

      const data = await response.json();
      setMethodSource((prev) => ({ ...prev, [methodName]: data.source_code }));
      setExpandedMethod(methodName);
    } catch (error) {
      console.error('Failed to fetch method source:', error);
    } finally {
      setLoadingMethod(null);
    }
  };

  if (!hasAny) {
    return (
      <div className="text-sm text-fg-3 italic px-3 py-2">
        No business rules or conditions found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Conditions */}
      {hasConditions && (
        <Card className="p-3 bg-bg-3 border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <GitBranch className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-medium text-fg-1">
              Conditional Logic ({conditions.length})
            </span>
          </div>

          <div className="space-y-2">
            {conditions.map((condition, index) => (
              <div key={index} className="p-2 bg-bg-4 border border-white/5 rounded">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-purple-300 font-medium uppercase">
                    {condition.type.replace('_', ' ')}
                  </span>
                </div>
                <code className="text-xs text-fg-2 font-mono block">{condition.test}</code>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Business Rules (Docstrings & Comments) */}
      {hasRules && (
        <Card className="p-3 bg-bg-3 border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-yellow-400" />
            <span className="text-xs font-medium text-fg-1">Business Rules & Notes</span>
          </div>

          <div className="space-y-2">
            {rules.map((rule, index) => (
              <div key={index} className="p-2 bg-bg-4 border border-white/5 rounded">
                <p className="text-xs text-fg-2 leading-relaxed">{rule}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Function Calls (Business Methods) */}
      {hasFunctionCalls &&
        functionCalls.some((call) =>
          [
            'evaluate_verification',
            'calculate_replacement_fees',
            'route_after_check_continue',
          ].includes(call)
        ) && (
          <Card className="p-3 bg-bg-3 border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-medium text-fg-1">Business Method Calls</span>
            </div>

            <div className="space-y-2">
              {functionCalls
                .filter((call) =>
                  [
                    'evaluate_verification',
                    'calculate_replacement_fees',
                    'route_after_check_continue',
                  ].includes(call)
                )
                .map((call, index) => (
                  <div key={index}>
                    <div
                      onClick={() => fetchMethodSource(call)}
                      className="flex items-center gap-2 p-2 bg-bg-4 border border-white/5 rounded hover:border-blue-400/30 transition-colors cursor-pointer"
                    >
                      {expandedMethod === call ? (
                        <ChevronDown className="w-3 h-3 text-fg-2" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-fg-2" />
                      )}
                      <code className="text-xs text-blue-300 font-mono flex-1">self.{call}()</code>
                      {loadingMethod === call ? (
                        <span className="text-xs text-fg-3 animate-pulse">Loading...</span>
                      ) : (
                        <span className="text-xs text-fg-3">
                          {methodSource[call] ? 'View' : 'Click to view'}
                        </span>
                      )}
                    </div>

                    {/* Expanded method source */}
                    {expandedMethod === call && methodSource[call] && (
                      <div className="mt-2 ml-5">
                        <CodeBlock
                          code={methodSource[call]}
                          language="python"
                          title={`${call}() Implementation`}
                          readonly={true}
                          maxHeight="300px"
                        />
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </Card>
        )}
    </div>
  );
}
