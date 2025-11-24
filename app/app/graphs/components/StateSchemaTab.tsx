'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, Save, Database } from 'lucide-react';
import type { StateField, StateSchema } from '@/types';
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

interface StateSchemaTabProps {
  schemas: StateSchema[];
  activeSchemaId: string | null;
  onSelectSchema: (id: string | null) => void;
  onSaveSchema: (schema: any) => Promise<void>;
  onDeleteSchema: (schemaId: string) => Promise<void>;
}

export function StateSchemaTab({
  schemas,
  activeSchemaId,
  onSelectSchema,
  onSaveSchema,
  onDeleteSchema,
}: StateSchemaTabProps) {
  const [draft, setDraft] = useState<any>({
    name: '',
    description: '',
    version: '1.0.0',
    fields: [],
    initialState: {},
  });
  const [initialStateText, setInitialStateText] = useState('{}');
  const [isSaving, setIsSaving] = useState(false);

  const activeSchema = schemas.find((s) => s.id === activeSchemaId);

  useEffect(() => {
    if (activeSchema) {
      setDraft({
        id: activeSchema.id,
        name: activeSchema.name,
        description: activeSchema.description || '',
        version: activeSchema.version || '1.0.0',
        fields: activeSchema.fields || [],
        initialState: activeSchema.initialState || {},
      });
      setInitialStateText(JSON.stringify(activeSchema.initialState || {}, null, 2));
    } else {
      // Reset to blank
      setDraft({
        name: '',
        description: '',
        version: '1.0.0',
        fields: [],
        initialState: {},
      });
      setInitialStateText('{}');
    }
  }, [activeSchema]);

  const handleSave = async () => {
    try {
      setIsSaving(true);
      let initialState = {};
      try {
        initialState = JSON.parse(initialStateText);
      } catch (e) {
        alert('Invalid JSON in initial state');
        return;
      }
      await onSaveSchema({ ...draft, initialState });
      onSelectSchema(null);
    } catch (error) {
      console.error('Failed to save schema:', error);
      alert('Failed to save schema');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!activeSchemaId) return;
    if (!confirm('Delete this state schema?')) return;
    try {
      await onDeleteSchema(activeSchemaId);
      onSelectSchema(null);
    } catch (error) {
      console.error('Failed to delete schema:', error);
      alert('Failed to delete schema');
    }
  };

  const addField = () => {
    setDraft({ ...draft, fields: [...draft.fields, createBlankField()] });
  };

  const updateField = (index: number, updates: Partial<StateField>) => {
    const newFields = [...draft.fields];
    newFields[index] = { ...newFields[index], ...updates };
    setDraft({ ...draft, fields: newFields });
  };

  const removeField = (index: number) => {
    setDraft({ ...draft, fields: draft.fields.filter((_: any, i: number) => i !== index) });
  };

  return (
    <div className="h-full flex">
      {/* Left sidebar - Schema list */}
      <div className="w-64 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <Button onClick={() => onSelectSchema(null)} size="sm" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            New Schema
          </Button>
        </div>
        <div className="flex-1 overflow-auto">
          {schemas.map((schema) => (
            <button
              key={schema.id}
              onClick={() => onSelectSchema(schema.id)}
              className={`
                w-full text-left px-4 py-3 border-b border-gray-200 dark:border-gray-700
                hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                ${activeSchemaId === schema.id ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-500' : ''}
              `}
            >
              <div className="font-medium text-sm text-gray-900 dark:text-gray-100">
                {schema.name}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {schema.fields?.length || 0} fields
              </div>
            </button>
          ))}
          {schemas.length === 0 && (
            <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
              No schemas yet
            </div>
          )}
        </div>
      </div>

      {/* Right panel - Schema editor */}
      <div className="flex-1 overflow-auto">
        <div className="p-6 max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Database className="w-6 h-6 text-blue-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {activeSchemaId ? 'Edit State Schema' : 'New State Schema'}
              </h2>
            </div>
            <div className="flex gap-2">
              {activeSchemaId && (
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
                {isSaving ? 'Saving...' : 'Save Schema'}
              </Button>
            </div>
          </div>

          {/* Schema Details */}
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Schema Name *</Label>
                <Input
                  value={draft.name}
                  onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                  placeholder="e.g., ConversationState"
                />
              </div>
              <div>
                <Label>Version</Label>
                <Input
                  value={draft.version}
                  onChange={(e) => setDraft({ ...draft, version: e.target.value })}
                  placeholder="1.0.0"
                />
              </div>
            </div>

            <div>
              <Label>Description</Label>
              <Textarea
                value={draft.description}
                onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                placeholder="Describe what this state schema represents..."
                rows={2}
              />
            </div>

            {/* Fields */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>State Fields</Label>
                <Button onClick={addField} size="sm" variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Field
                </Button>
              </div>

              <div className="space-y-3">
                {draft.fields.map((field: StateField, index: number) => (
                  <div
                    key={field.id}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900"
                  >
                    <div className="grid grid-cols-12 gap-3">
                      <div className="col-span-3">
                        <Label className="text-xs">Field Name</Label>
                        <Input
                          value={field.name}
                          onChange={(e) => updateField(index, { name: e.target.value })}
                          placeholder="field_name"
                          className="mt-1"
                        />
                      </div>
                      <div className="col-span-2">
                        <Label className="text-xs">Type</Label>
                        <Select
                          value={field.type}
                          onValueChange={(value) => updateField(index, { type: value as any })}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {FIELD_TYPES.map((ft) => (
                              <SelectItem key={ft.value} value={ft.value}>
                                {ft.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-2">
                        <Label className="text-xs">Reducer</Label>
                        <Select
                          value={field.reducer}
                          onValueChange={(value) => updateField(index, { reducer: value as any })}
                        >
                          <SelectTrigger className="mt-1">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {REDUCERS.map((r) => (
                              <SelectItem key={r.value} value={r.value}>
                                {r.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="col-span-3">
                        <Label className="text-xs">Default Value</Label>
                        <Input
                          value={field.defaultValue || ''}
                          onChange={(e) => updateField(index, { defaultValue: e.target.value })}
                          placeholder="default"
                          className="mt-1"
                        />
                      </div>
                      <div className="col-span-1 flex items-end">
                        <Button
                          onClick={() => removeField(index)}
                          variant="ghost"
                          size="sm"
                          className="text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="col-span-12">
                        <Input
                          value={field.description || ''}
                          onChange={(e) => updateField(index, { description: e.target.value })}
                          placeholder="Field description..."
                          className="text-xs"
                        />
                      </div>
                      <div className="col-span-6 flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={field.required}
                            onCheckedChange={(checked) => updateField(index, { required: checked })}
                          />
                          <Label className="text-xs">Required</Label>
                        </div>
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={field.sensitive}
                            onCheckedChange={(checked) =>
                              updateField(index, { sensitive: checked })
                            }
                          />
                          <Label className="text-xs">Sensitive</Label>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {draft.fields.length === 0 && (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                    No fields defined. Click "Add Field" to create one.
                  </div>
                )}
              </div>
            </div>

            {/* Initial State */}
            <div>
              <Label>Initial State (JSON)</Label>
              <Textarea
                value={initialStateText}
                onChange={(e) => setInitialStateText(e.target.value)}
                placeholder="{}"
                rows={6}
                className="font-mono text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
