'use client';

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { X, Trash2, Plus } from 'lucide-react';

interface NodeEditorProps {
  node: Node;
  onNodeUpdate: (node: Node) => void;
  onClose: () => void;
}

export function NodeEditor({ node, onNodeUpdate, onClose }: NodeEditorProps) {
  const [label, setLabel] = useState(node.data.label || '');
  const [description, setDescription] = useState(node.data.description || '');
  const [model, setModel] = useState(node.data.model || 'gpt-4o-mini');
  const [temperature, setTemperature] = useState(node.data.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(node.data.maxTokens || 1000);
  const [tool, setTool] = useState(node.data.tool || '');
  const [conditions, setConditions] = useState(node.data.conditions || []);

  useEffect(() => {
    // Reset form when node changes
    setLabel(node.data.label || '');
    setDescription(node.data.description || '');
    setModel(node.data.model || 'gpt-4o-mini');
    setTemperature(node.data.temperature || 0.7);
    setMaxTokens(node.data.maxTokens || 1000);
    setTool(node.data.tool || '');
    setConditions(node.data.conditions || []);
  }, [node.id]);

  const handleUpdate = () => {
    const updatedData = {
      ...node.data,
      label,
      description,
      ...(node.type === 'process' && { model, temperature, maxTokens }),
      ...(node.type === 'toolCall' && { tool }),
      ...(node.type === 'decision' && { conditions }),
    };

    onNodeUpdate({
      ...node,
      data: updatedData,
    });
  };

  const addCondition = () => {
    setConditions([...conditions, { field: '', operator: '==', value: '', target: '' }]);
  };

  const updateCondition = (index: number, updates: any) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], ...updates };
    setConditions(newConditions);
  };

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-fg-0">Edit Node</h3>
          <p className="text-xs text-fg-2 mt-1">{node.type}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Label */}
        <div>
          <label className="text-sm font-medium text-fg-1 mb-1.5 block">Label</label>
          <Input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onBlur={handleUpdate}
            placeholder="Node label..."
            className="bg-bg-2 border-white/10"
          />
        </div>

        {/* Description */}
        <div>
          <label className="text-sm font-medium text-fg-1 mb-1.5 block">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onBlur={handleUpdate}
            placeholder="Describe what this node does..."
            rows={3}
            className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        {/* Process Node Fields */}
        {node.type === 'process' && (
          <>
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Model</label>
              <select
                value={model}
                onChange={(e) => {
                  setModel(e.target.value);
                  handleUpdate();
                }}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
                <option value="claude-3-opus-20240229">claude-3-opus</option>
                <option value="claude-3-sonnet-20240229">claude-3-sonnet</option>
                <option value="claude-3-haiku-20240307">claude-3-haiku</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                Temperature ({temperature})
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                onMouseUp={handleUpdate}
                className="w-full"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Tokens</label>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                onBlur={handleUpdate}
                className="bg-bg-2 border-white/10"
              />
            </div>
          </>
        )}

        {/* Tool Call Node Fields */}
        {node.type === 'toolCall' && (
          <div>
            <label className="text-sm font-medium text-fg-1 mb-1.5 block">Tool Name</label>
            <Input
              value={tool}
              onChange={(e) => setTool(e.target.value)}
              onBlur={handleUpdate}
              placeholder="e.g., web_search, calculator"
              className="bg-bg-2 border-white/10"
            />
          </div>
        )}

        {/* Decision Node Fields */}
        {node.type === 'decision' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-fg-1">Conditions</label>
              <Button size="sm" variant="outline" onClick={addCondition} className="border-white/10">
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
            <div className="space-y-2">
              {conditions.map((condition: any, index: number) => (
                <Card key={index} className="p-3 bg-bg-2 border-white/10">
                  <div className="space-y-2">
                    <Input
                      placeholder="Field"
                      value={condition.field}
                      onChange={(e) => updateCondition(index, { field: e.target.value })}
                      onBlur={handleUpdate}
                      className="bg-bg-0 border-white/10 text-sm"
                    />
                    <select
                      value={condition.operator}
                      onChange={(e) => {
                        updateCondition(index, { operator: e.target.value });
                        handleUpdate();
                      }}
                      className="w-full bg-bg-0 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm"
                    >
                      <option value="==">equals</option>
                      <option value="!=">not equals</option>
                      <option value=">">greater than</option>
                      <option value="<">less than</option>
                      <option value=">=">greater or equal</option>
                      <option value="<=">less or equal</option>
                      <option value="contains">contains</option>
                    </select>
                    <Input
                      placeholder="Value"
                      value={condition.value}
                      onChange={(e) => updateCondition(index, { value: e.target.value })}
                      onBlur={handleUpdate}
                      className="bg-bg-0 border-white/10 text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        removeCondition(index);
                        handleUpdate();
                      }}
                      className="w-full border-red-600/30 text-red-400 hover:bg-red-600/10"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Remove
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/10">
        <Button
          variant="outline"
          className="w-full border-red-600/30 text-red-400 hover:bg-red-600/10"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete Node
        </Button>
      </div>
    </div>
  );
}
