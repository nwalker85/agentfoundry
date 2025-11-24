'use client';

import { useEffect, useMemo, useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { TriggerDefinition, TriggerType } from '@/types';
import { Plug, Plus, Zap, X } from 'lucide-react';

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

interface TriggerRegistryDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  triggers: TriggerDefinition[];
  selectedTriggerIds: string[];
  onToggleTriggerSelection: (triggerId: string, selected: boolean) => void;
  onSaveTrigger: (
    trigger: Omit<TriggerDraft, 'configText'> & { config: Record<string, any> }
  ) => Promise<void>;
  onDeleteTrigger: (triggerId: string) => Promise<void>;
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

export function TriggerRegistryDrawer({
  open,
  onOpenChange,
  triggers,
  selectedTriggerIds,
  onToggleTriggerSelection,
  onSaveTrigger,
  onDeleteTrigger,
}: TriggerRegistryDrawerProps) {
  const [draft, setDraft] = useState<TriggerDraft>(defaultTrigger);
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const activeTrigger = useMemo(
    () => triggers.find((trigger) => trigger.id === draft.id) ?? null,
    [triggers, draft.id]
  );

  useEffect(() => {
    if (!open) return;
    if (triggers.length === 0) {
      setDraft(defaultTrigger);
      return;
    }
    if (!draft.id) {
      setDraft(defaultTrigger);
    }
  }, [open, triggers.length, draft.id]);

  const handleSelectTrigger = (trigger: TriggerDefinition) => {
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
    } catch (error: any) {
      setJsonError(error?.message || 'Invalid JSON');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!draft.id) return;
    if (!confirm(`Delete trigger "${draft.name}"?`)) return;
    setIsDeleting(true);
    try {
      await onDeleteTrigger(draft.id);
      setDraft(defaultTrigger);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[840px] max-w-full p-0 flex flex-col bg-bg-0">
        <SheetHeader className="px-6 py-4 border-b border-white/5 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10">
              <Plug className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <SheetTitle className="text-left">Trigger Registry</SheetTitle>
              <p className="text-sm text-fg-3">
                Define how graphs start (webhook, schedules, events)
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="w-4 h-4" />
          </Button>
        </SheetHeader>

        <div className="flex flex-1 overflow-hidden">
          {/* List */}
          <div className="w-72 border-r border-white/5 p-4 flex flex-col gap-3 bg-bg-1">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wide text-fg-3">Available Triggers</span>
              <Button variant="ghost" size="icon" onClick={handleCreateNew}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              <div className="flex flex-col gap-2 pr-2">
                {triggers.map((trigger) => {
                  const selected = trigger.id ? selectedTriggerIds.includes(trigger.id) : false;
                  return (
                    <div
                      key={trigger.id}
                      className={`rounded-lg border px-3 py-2 text-left cursor-pointer transition ${
                        draft.id === trigger.id
                          ? 'border-indigo-500/60 bg-indigo-500/10'
                          : 'border-white/5'
                      }`}
                      onClick={() => trigger.id && handleSelectTrigger(trigger)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{trigger.name}</div>
                        <Checkbox
                          checked={selected}
                          onCheckedChange={(checked) =>
                            trigger.id && onToggleTriggerSelection(trigger.id, Boolean(checked))
                          }
                        />
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-fg-3">
                        <Badge variant="outline" className="text-[10px] uppercase tracking-wider">
                          {trigger.type}
                        </Badge>
                        {trigger.channel && <span>{trigger.channel}</span>}
                      </div>
                    </div>
                  );
                })}
                {triggers.length === 0 && (
                  <div className="text-xs text-fg-3">
                    No triggers yet. Create webhook/event triggers and attach them to START nodes.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Editor */}
          <div className="flex-1 flex flex-col">
            <div className="p-6 space-y-4 overflow-auto">
              <div className="flex items-center gap-3">
                <Input
                  value={draft.name}
                  onChange={(e) => setDraft((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Support Webhook"
                />
                <Select
                  value={draft.type}
                  onValueChange={(value) =>
                    setDraft((prev) => ({ ...prev, type: value as TriggerType }))
                  }
                >
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRIGGER_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={draft.channel ?? 'any'}
                  onValueChange={(value) => setDraft((prev) => ({ ...prev, channel: value }))}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHANNELS.map((channel) => (
                      <SelectItem key={channel} value={channel}>
                        {channel}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Textarea
                value={draft.description}
                onChange={(e) => setDraft((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Trigger fires when customer submits a support ticket via webhook."
                rows={2}
              />

              <div className="flex items-center gap-2 text-sm">
                <Switch
                  checked={draft.isActive}
                  onCheckedChange={(checked) =>
                    setDraft((prev) => ({ ...prev, isActive: checked }))
                  }
                />
                <span>Active</span>
              </div>

              <div className="border border-white/5 rounded-xl">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                  <div>
                    <div className="font-medium text-sm">Configuration</div>
                    <p className="text-xs text-fg-3">
                      JSON payload describing webhook/event metadata
                    </p>
                  </div>
                  <Zap className="w-4 h-4 text-amber-400" />
                </div>
                <Textarea
                  value={draft.configText}
                  onChange={(e) => {
                    setDraft((prev) => ({ ...prev, configText: e.target.value }));
                    setJsonError(null);
                  }}
                  className="min-h-[220px] font-mono text-xs"
                />
                {jsonError && <div className="px-4 py-2 text-xs text-red-400">{jsonError}</div>}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
              <div className="text-xs text-fg-3">
                Select triggers with the checkbox to attach them to the START node.
              </div>
              <div className="flex items-center gap-2">
                {draft.id && (
                  <Button variant="ghost" disabled={isDeleting} onClick={handleDelete}>
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                )}
                <Button onClick={handleSave} disabled={isSaving || !draft.name}>
                  {isSaving ? 'Saving...' : 'Save Trigger'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
