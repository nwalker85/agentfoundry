'use client';

import { useState } from 'react';
import { Code, Database, Zap } from 'lucide-react';
import type { Node, Edge } from 'reactflow';
import { PythonCodePreview } from '@/app/forge/components/PythonCodePreview';
import { StateSchemaTab } from './StateSchemaTab';
import { TriggersTab } from './TriggersTab';

type TabType = 'code' | 'state' | 'triggers';

interface EditorBottomPanelProps {
  nodes: Node[];
  edges: Edge[];
  stateSchemas: any[];
  triggers: any[];
  selectedStateSchema: string | null;
  selectedTriggers: string[];
  onSelectStateSchema: (id: string | null) => void;
  onToggleTrigger: (triggerId: string, selected: boolean) => void;
  onSaveSchema: (schema: any) => Promise<void>;
  onDeleteSchema: (schemaId: string) => Promise<void>;
  onSaveTrigger: (trigger: any) => Promise<void>;
  onDeleteTrigger: (triggerId: string) => Promise<void>;
}

export function EditorBottomPanel({
  nodes,
  edges,
  stateSchemas,
  triggers,
  selectedStateSchema,
  selectedTriggers,
  onSelectStateSchema,
  onToggleTrigger,
  onSaveSchema,
  onDeleteSchema,
  onSaveTrigger,
  onDeleteTrigger,
}: EditorBottomPanelProps) {
  const [activeTab, setActiveTab] = useState<TabType>('code');

  const tabs = [
    { id: 'code' as TabType, label: 'Python Code', icon: Code },
    { id: 'state' as TabType, label: 'State Schema', icon: Database },
    { id: 'triggers' as TabType, label: 'Triggers', icon: Zap },
  ];

  return (
    <div className="h-full flex flex-col border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors
                ${
                  activeTab === tab.id
                    ? 'bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'code' && (
          <div className="h-full">
            <PythonCodePreview
              nodes={nodes}
              edges={edges}
              agentName="agent-preview"
              stateSchema={null}
              triggers={[]}
            />
          </div>
        )}

        {activeTab === 'state' && (
          <StateSchemaTab
            schemas={stateSchemas}
            activeSchemaId={selectedStateSchema}
            onSelectSchema={onSelectStateSchema}
            onSaveSchema={onSaveSchema}
            onDeleteSchema={onDeleteSchema}
          />
        )}

        {activeTab === 'triggers' && (
          <TriggersTab
            triggers={triggers}
            selectedTriggerIds={selectedTriggers}
            onToggleTrigger={onToggleTrigger}
            onSaveTrigger={onSaveTrigger}
            onDeleteTrigger={onDeleteTrigger}
          />
        )}
      </div>
    </div>
  );
}
