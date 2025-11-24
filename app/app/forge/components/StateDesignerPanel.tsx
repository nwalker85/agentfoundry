'use client';

import { useEffect, useMemo, useState } from 'react';
import { X, Plus, Trash2, Database } from 'lucide-react';
import type { StateField, StateSchema } from '@/types';
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
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';

const FIELD_TYPES: { label: string; value: StateField['type'] }[] = [
  { label: 'String', value: 'string' },
  { label: 'Number', value: 'int' },
  { label: 'Float', value: 'float' },
  { label: 'Boolean', value: 'bool' },
  { label: 'List', value: 'list' },
  { label: 'Dictionary', value: 'dict' },
  { label: 'JSON', value: 'json' },
  { label: 'Message', value: 'message' },
  { label: 'Custom', value: 'custom' },
];

const REDUCERS = [
  { label: 'Add / Append', value: 'add' },
  { label: 'Replace', value: 'replace' },
  { label: 'Merge', value: 'merge' },
  { label: 'Sum', value: 'sum' },
  { label: 'Max', value: 'max' },
  { label: 'Min', value: 'min' },
  { label: 'Custom', value: 'custom' },
];

export interface StateSchemaDraft {
  id?: string;
  name: string;
  description?: string;
  version?: string;
  fields: StateField[];
  initialState: Record<string, any>;
  tags?: string[];
}

interface StateDesignerPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schemas: StateSchema[];
  activeSchemaId: string | null;
  onSelectSchema: (id: string) => void;
  onSaveSchema: (schema: StateSchemaDraft) => Promise<void>;
  onDeleteSchema: (schemaId: string) => Promise<void>;
}

const createBlankField = (): StateField => ({
  id: `field-${Date.now()}`,
  name: '',
  type: 'string',
  reducer: 'replace',
  description: '',
  defaultValue: '',
  required: true,
  sensitive: false,
});

const defaultSchema: StateSchemaDraft = {
  name: '',
  description: '',
  version: '1.0.0',
  fields: [],
  initialState: {},
  tags: [],
};

export function StateDesignerPanel({
  open,
  onOpenChange,
  schemas,
  activeSchemaId,
  onSelectSchema,
  onSaveSchema,
  onDeleteSchema,
}: StateDesignerPanelProps) {
  const [draft, setDraft] = useState<StateSchemaDraft>(defaultSchema);
  const [initialStateText, setInitialStateText] = useState('{}');
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const activeSchema = useMemo(
    () => schemas.find((schema) => schema.id === activeSchemaId) ?? null,
    [schemas, activeSchemaId]
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    if (activeSchema) {
      setDraft({
        id: activeSchema.id,
        name: activeSchema.name,
        description: activeSchema.description,
        version: activeSchema.version,
        fields: activeSchema.fields ?? [],
        initialState: activeSchema.initialState ?? {},
        tags: activeSchema.tags,
      });
      setInitialStateText(JSON.stringify(activeSchema.initialState ?? {}, null, 2));
    } else {
      setDraft(defaultSchema);
      setInitialStateText('{}');
    }
    setJsonError(null);
    setMessage(null);
  }, [open, activeSchema]);

  const handleFieldChange = (index: number, field: Partial<StateField>) => {
    setDraft((prev) => {
      const nextFields = [...(prev.fields ?? [])];
      nextFields[index] = { ...nextFields[index], ...field };
      return { ...prev, fields: nextFields };
    });
  };

  const handleAddField = () => {
    setDraft((prev) => ({
      ...prev,
      fields: [...(prev.fields ?? []), createBlankField()],
    }));
  };

  const handleRemoveField = (index: number) => {
    setDraft((prev) => ({
      ...prev,
      fields: prev.fields.filter((_, idx) => idx !== index),
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const parsed = JSON.parse(initialStateText || '{}');
      await onSaveSchema({
        ...draft,
        initialState: parsed,
      });
      setMessage('State schema saved successfully');
    } catch (error: any) {
      setJsonError(error?.message || 'Invalid JSON in initial state');
    } finally {
      setIsSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleDelete = async () => {
    if (!draft.id) return;
    if (!confirm(`Delete state schema "${draft.name}"?`)) return;

    setIsDeleting(true);
    try {
      await onDeleteSchema(draft.id);
      onSelectSchema('');
      setDraft(defaultSchema);
      setInitialStateText('{}');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-[960px] max-w-full p-0 flex flex-col bg-bg-0 text-fg-1"
      >
        <SheetHeader className="px-6 py-4 border-b border-white/5 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10">
              <Database className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <SheetTitle className="text-left">State Schema Designer</SheetTitle>
              <p className="text-sm text-fg-3">Define initial state objects and reducers</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => onOpenChange(false)}>
            <X className="w-4 h-4" />
          </Button>
        </SheetHeader>

        <div className="flex flex-1 overflow-hidden">
          {/* Schema List */}
          <div className="w-64 border-r border-white/5 p-4 flex flex-col gap-3 bg-bg-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-fg-3 uppercase tracking-wide">Schemas</span>
              <Button size="icon" variant="ghost" onClick={() => onSelectSchema('')}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              <div className="flex flex-col gap-2 pr-2">
                {schemas.map((schema) => (
                  <button
                    key={schema.id}
                    className={`text-left rounded-lg border px-3 py-2 transition ${
                      schema.id === activeSchemaId
                        ? 'border-emerald-500/60 bg-emerald-500/10 text-emerald-200'
                        : 'border-white/5 bg-transparent hover:border-white/20'
                    }`}
                    onClick={() => onSelectSchema(schema.id)}
                  >
                    <div className="text-sm font-medium">{schema.name}</div>
                    <div className="text-xs text-fg-3">{schema.version}</div>
                  </button>
                ))}
                {schemas.length === 0 && (
                  <div className="text-xs text-fg-3">
                    No schemas yet. Click + to create your first initial state.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Editor */}
          <div className="flex-1 flex flex-col">
            <div className="p-6 space-y-6 overflow-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Name</Label>
                  <Input
                    value={draft.name}
                    onChange={(e) => setDraft((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="ConversationState"
                  />
                </div>
                <div>
                  <Label>Version</Label>
                  <Input
                    value={draft.version}
                    onChange={(e) => setDraft((prev) => ({ ...prev, version: e.target.value }))}
                  />
                </div>
              </div>
              <div>
                <Label>Description</Label>
                <Textarea
                  value={draft.description}
                  onChange={(e) => setDraft((prev) => ({ ...prev, description: e.target.value }))}
                  rows={2}
                  placeholder="State used to track conversation context, last user input, etc."
                />
              </div>

              {/* Fields */}
              <div className="border border-white/5 rounded-xl">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                  <div>
                    <div className="font-medium text-sm">Fields</div>
                    <p className="text-xs text-fg-3">Define fields, types and reducers</p>
                  </div>
                  <Button size="sm" onClick={handleAddField}>
                    <Plus className="w-4 h-4 mr-1" /> Add Field
                  </Button>
                </div>
                <div className="divide-y divide-white/5">
                  {draft.fields.length === 0 && (
                    <div className="px-4 py-6 text-sm text-fg-3 text-center">
                      No fields yet. Add a field to describe your state.
                    </div>
                  )}
                  {draft.fields.map((field, index) => (
                    <div key={field.id ?? index} className="p-4 flex flex-col gap-3">
                      <div className="flex items-center gap-3">
                        <Input
                          className="flex-1"
                          value={field.name}
                          onChange={(e) => handleFieldChange(index, { name: e.target.value })}
                          placeholder="messages"
                        />
                        <Select
                          value={field.type}
                          onValueChange={(value) =>
                            handleFieldChange(index, { type: value as StateField['type'] })
                          }
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {FIELD_TYPES.map((item) => (
                              <SelectItem key={item.value} value={item.value}>
                                {item.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Select
                          value={field.reducer ?? 'replace'}
                          onValueChange={(value) =>
                            handleFieldChange(index, { reducer: value as StateField['reducer'] })
                          }
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {REDUCERS.map((item) => (
                              <SelectItem key={item.value} value={item.value}>
                                {item.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveField(index)}
                        >
                          <Trash2 className="w-4 h-4 text-red-400" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <Textarea
                          value={field.description}
                          onChange={(e) =>
                            handleFieldChange(index, { description: e.target.value })
                          }
                          placeholder="Purpose of this field"
                          rows={2}
                        />
                        <Input
                          value={field.defaultValue ?? ''}
                          onChange={(e) =>
                            handleFieldChange(index, { defaultValue: e.target.value })
                          }
                          placeholder="Default / initial value"
                        />
                      </div>
                      <div className="flex items-center gap-6 text-sm">
                        <label className="flex items-center gap-2">
                          <Switch
                            checked={field.required ?? true}
                            onCheckedChange={(checked) =>
                              handleFieldChange(index, { required: checked })
                            }
                          />
                          <span>Required</span>
                        </label>
                        <label className="flex items-center gap-2">
                          <Switch
                            checked={field.sensitive ?? false}
                            onCheckedChange={(checked) =>
                              handleFieldChange(index, { sensitive: checked })
                            }
                          />
                          <span>Sensitive</span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Initial State */}
              <div className="border border-white/5 rounded-xl">
                <div className="px-4 py-3 border-b border-white/5">
                  <div className="font-medium text-sm">Initial State Preview</div>
                  <p className="text-xs text-fg-3">JSON payload passed into LangGraph on start</p>
                </div>
                <Textarea
                  value={initialStateText}
                  onChange={(e) => {
                    setInitialStateText(e.target.value);
                    setJsonError(null);
                  }}
                  className="min-h-[200px] font-mono text-xs"
                />
                {jsonError && <p className="text-red-400 text-xs px-4 py-2">{jsonError}</p>}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
              <div className="text-sm text-fg-3">
                {message || 'Changes are saved per schema. Remember to bind schema to your agent.'}
              </div>
              <div className="flex items-center gap-2">
                {draft.id && (
                  <Button variant="ghost" disabled={isDeleting} onClick={handleDelete}>
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                )}
                <Button onClick={handleSave} disabled={isSaving || !draft.name}>
                  {isSaving ? 'Saving...' : 'Save Schema'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
