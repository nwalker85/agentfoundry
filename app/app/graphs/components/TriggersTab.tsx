'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, Save, Zap, Check } from 'lucide-react';
import type { TriggerDefinition, TriggerType } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';

const TRIGGER_TYPES: { label: string; value: TriggerType }[] = [
  { label: 'Webhook', value: 'webhook' },
  { label: 'Event Bus', value: 'event' },
  { label: 'Cron / Schedule', value: 'cron' },
  { label: 'Streaming', value: 'stream' },
  { label: 'Manual', value: 'manual' },
  { label: 'Custom', value: 'custom' },
];

const CHANNELS = ['chat', 'voice', 'api', 'studio', 'any'];

interface TriggerDraft {
  id?: string;
  name: string;
  type: TriggerType;
  description?: string;
  channel?: string;
  configText: string;
  isActive: boolean;
}

const defaultTrigger: TriggerDraft = {
  name: '',
  type: 'webhook',
  description: '',
  channel: 'chat',
  configText: JSON.stringify(
    {
      method: 'POST',
      path: '/api/hooks/support',
      secret: 'changeme',
    },
    null,
    2
  ),
  isActive: true,
};

interface TriggersTabProps {
  triggers: TriggerDefinition[];
  selectedTriggerIds: string[];
  onToggleTrigger: (triggerId: string, selected: boolean) => void;
  onSaveTrigger: (trigger: any) => Promise<void>;
  onDeleteTrigger: (triggerId: string) => Promise<void>;
}

export function TriggersTab({
  triggers,
  selectedTriggerIds,
  onToggleTrigger,
  onSaveTrigger,
  onDeleteTrigger,
}: TriggersTabProps) {
  const [draft, setDraft] = useState<TriggerDraft>(defaultTrigger);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [editingTriggerId, setEditingTriggerId] = useState<string | null>(null);

  const handleSelectTrigger = (trigger: TriggerDefinition) => {
    setEditingTriggerId(trigger.id);
    setDraft({
      id: trigger.id,
      name: trigger.name,
      type: trigger.type,
      description: trigger.description,
      channel: trigger.channel ?? 'chat',
      configText: JSON.stringify(trigger.config ?? {}, null, 2),
      isActive: trigger.isActive,
    });
    setJsonError(null);
  };

  const handleCreateNew = () => {
    setEditingTriggerId(null);
    setDraft(defaultTrigger);
    setJsonError(null);
  };

  const handleSave = async () => {
    setIsSaving(true);
    setJsonError(null);
    try {
      const parsed = JSON.parse(draft.configText || '{}');
      await onSaveTrigger({
        id: draft.id,
        name: draft.name,
        type: draft.type,
        description: draft.description,
        channel: draft.channel,
        config: parsed,
        isActive: draft.isActive,
      });
      setEditingTriggerId(null);
      handleCreateNew();
    } catch (error: any) {
      setJsonError(error?.message || 'Invalid JSON');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!draft.id) return;
    if (!confirm(`Delete trigger "${draft.name}"?`)) return;
    try {
      await onDeleteTrigger(draft.id);
      handleCreateNew();
    } catch (error) {
      console.error('Failed to delete trigger:', error);
      alert('Failed to delete trigger');
    }
  };

  return (
    <div className="h-full flex">
      {/* Left sidebar - Trigger list */}
      <div className="w-80 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <Button onClick={handleCreateNew} size="sm" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            New Trigger
          </Button>
        </div>

        <div className="flex-1 overflow-auto">
          {triggers.map((trigger) => (
            <div
              key={trigger.id}
              className={`
                border-b border-gray-200 dark:border-gray-700
                hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                ${editingTriggerId === trigger.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-500' : ''}
              `}
            >
              <div className="p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={selectedTriggerIds.includes(trigger.id)}
                    onCheckedChange={(checked) => onToggleTrigger(trigger.id, !!checked)}
                    className="mt-1"
                  />
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => handleSelectTrigger(trigger)}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm text-gray-900 dark:text-gray-100">
                        {trigger.name}
                      </span>
                      {trigger.isActive && (
                        <Badge
                          variant="outline"
                          className="text-xs bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
                        >
                          Active
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <Badge variant="secondary" className="text-xs">
                        {trigger.type}
                      </Badge>
                      {trigger.channel && (
                        <Badge variant="outline" className="text-xs">
                          {trigger.channel}
                        </Badge>
                      )}
                    </div>
                    {trigger.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                        {trigger.description}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {triggers.length === 0 && (
            <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
              No triggers yet
            </div>
          )}
        </div>

        {/* Selected count */}
        {selectedTriggerIds.length > 0 && (
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20">
            <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
              <Check className="w-4 h-4" />
              <span>{selectedTriggerIds.length} trigger(s) enabled for this graph</span>
            </div>
          </div>
        )}
      </div>

      {/* Right panel - Trigger editor */}
      <div className="flex-1 overflow-auto">
        <div className="p-6 max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Zap className="w-6 h-6 text-indigo-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {editingTriggerId ? 'Edit Trigger' : 'New Trigger'}
              </h2>
            </div>
            <div className="flex gap-2">
              {editingTriggerId && (
                <Button
                  onClick={handleDelete}
                  variant="outline"
                  size="sm"
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </Button>
              )}
              <Button onClick={handleSave} size="sm" disabled={isSaving || !draft.name}>
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? 'Saving...' : 'Save Trigger'}
              </Button>
            </div>
          </div>

          {/* Trigger Details */}
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Trigger Name *</Label>
                <Input
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  placeholder="e.g., Support Webhook"
                />
              </div>
              <div>
                <Label>Type</Label>
                <Select
                  value={draft.type}
                  onValueChange={(value) => setDraft({ ...draft, type: value as TriggerType })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRIGGER_TYPES.map((tt) => (
                      <SelectItem key={tt.value} value={tt.value}>
                        {tt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Channel</Label>
                <Select
                  value={draft.channel || 'chat'}
                  onValueChange={(value) => setDraft({ ...draft, channel: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((ch) => (
                      <SelectItem key={ch} value={ch}>
                        {ch}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={draft.isActive}
                    onCheckedChange={(checked) => setDraft({ ...draft, isActive: checked })}
                  />
                  <Label>Active</Label>
                </div>
              </div>
            </div>

            <div>
              <Label>Description</Label>
              <Textarea
                value={draft.description || ''}
                onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                placeholder="Describe when this trigger should fire..."
                rows={2}
              />
            </div>

            {/* Configuration JSON */}
            <div>
              <Label>Configuration (JSON)</Label>
              <Textarea
                value={draft.configText}
                onChange={(e) => setDraft({ ...draft, configText: e.target.value })}
                placeholder="{}"
                rows={12}
                className="font-mono text-sm"
              />
              {jsonError && <p className="text-red-600 text-xs mt-2">{jsonError}</p>}
            </div>

            {/* Examples based on type */}
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                Configuration Examples
              </h3>
              <div className="text-xs text-gray-600 dark:text-gray-400 space-y-2">
                {draft.type === 'webhook' && (
                  <pre className="bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                    {JSON.stringify(
                      { method: 'POST', path: '/api/hooks/my-trigger', secret: 'your-secret-key' },
                      null,
                      2
                    )}
                  </pre>
                )}
                {draft.type === 'cron' && (
                  <pre className="bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                    {JSON.stringify({ schedule: '0 */6 * * *', timezone: 'UTC' }, null, 2)}
                  </pre>
                )}
                {draft.type === 'event' && (
                  <pre className="bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 overflow-x-auto">
                    {JSON.stringify({ eventType: 'user.created', source: 'auth-service' }, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
