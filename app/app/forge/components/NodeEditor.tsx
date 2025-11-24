'use client';

import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';
import { Trash2, Plus, Save, Code2, ChevronDown, ChevronRight } from 'lucide-react';
import { CodeBlock, PromptViewer, StateMutationTable, BusinessRulesList } from './implementation';

interface NodeEditorProps {
  node: Node;
  onNodeUpdate: (node: Node) => void;
  onNodeDelete?: (nodeId: string) => void;
  onClose: () => void;
  triggers?: any[]; // Available triggers for entry point nodes
}

export function NodeEditor({
  node,
  onNodeUpdate,
  onNodeDelete,
  onClose,
  triggers = [],
}: NodeEditorProps) {
  const [label, setLabel] = useState(node.data.label || '');
  const [description, setDescription] = useState(node.data.description || '');
  const [llmInstructions, setLlmInstructions] = useState(node.data.llmInstructions || '');
  const [model, setModel] = useState(node.data.model || 'gpt-4o-mini');
  const [temperature, setTemperature] = useState(node.data.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(node.data.maxTokens || 1000);
  const [tool, setTool] = useState(node.data.tool || '');
  const [triggerId, setTriggerId] = useState(node.data.trigger_id || '');
  const [conditions, setConditions] = useState(node.data.conditions || []);
  const [routes, setRoutes] = useState(node.data.routes || []);
  const [routingLogic, setRoutingLogic] = useState(node.data.routing_logic || 'conditional');
  const [prompt, setPrompt] = useState(node.data.prompt || 'Please provide input...');
  const [tools, setTools] = useState(node.data.tools || []);
  const [maxIterations, setMaxIterations] = useState(node.data.max_iterations || 10);
  const [earlyStopping, setEarlyStopping] = useState(node.data.early_stopping || 'force');

  // Deep Agent state variables
  const [strategy, setStrategy] = useState(node.data.strategy || 'hierarchical');
  const [maxSubtasks, setMaxSubtasks] = useState(node.data.max_subtasks || 10);
  const [enableTodos, setEnableTodos] = useState(node.data.enable_todos ?? true);
  const [enableFilesystem, setEnableFilesystem] = useState(node.data.enable_filesystem ?? true);
  const [enableSubagents, setEnableSubagents] = useState(node.data.enable_subagents ?? false);
  const [enableSummarization, setEnableSummarization] = useState(
    node.data.enable_summarization ?? true
  );
  const [validationCriteria, setValidationCriteria] = useState(
    node.data.validation_criteria || ['completeness', 'accuracy', 'clarity']
  );
  const [qualityThreshold, setQualityThreshold] = useState(node.data.quality_threshold || 0.8);
  const [autoReplan, setAutoReplan] = useState(node.data.auto_replan ?? true);
  const [specialization, setSpecialization] = useState(node.data.specialization || 'Research');
  const [maxDepth, setMaxDepth] = useState(node.data.max_depth || 3);
  const [sizeThreshold, setSizeThreshold] = useState(node.data.size_threshold || 170000);
  const [offloadStrategy, setOffloadStrategy] = useState(node.data.offload_strategy || 'auto');
  const [autoSummarize, setAutoSummarize] = useState(node.data.auto_summarize ?? true);

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [showCloseConfirm, setShowCloseConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Implementation logic state
  const [nodeLogic, setNodeLogic] = useState<any>(null);
  const [loadingLogic, setLoadingLogic] = useState(false);
  const [showImplementation, setShowImplementation] = useState(false);

  useEffect(() => {
    // Reset form when node changes
    setIsInitialized(false); // Prevent auto-save during reset
    setLabel(node.data.label || '');
    setDescription(node.data.description || '');
    setLlmInstructions(node.data.llmInstructions || '');
    setModel(node.data.model || 'gpt-4o-mini');
    setTemperature(node.data.temperature || 0.7);
    setMaxTokens(node.data.maxTokens || 1000);
    setTool(node.data.tool || '');
    setTriggerId(node.data.trigger_id || '');
    setConditions(node.data.conditions || []);
    setRoutes(node.data.routes || []);
    setRoutingLogic(node.data.routing_logic || 'conditional');
    setPrompt(node.data.prompt || 'Please provide input...');
    setTools(node.data.tools || []);
    setMaxIterations(node.data.max_iterations || 10);
    setEarlyStopping(node.data.early_stopping || 'force');

    // Deep Agent fields
    setStrategy(node.data.strategy || 'hierarchical');
    setMaxSubtasks(node.data.max_subtasks || 10);
    setEnableTodos(node.data.enable_todos ?? true);
    setEnableFilesystem(node.data.enable_filesystem ?? true);
    setEnableSubagents(node.data.enable_subagents ?? false);
    setEnableSummarization(node.data.enable_summarization ?? true);
    setValidationCriteria(node.data.validation_criteria || ['completeness', 'accuracy', 'clarity']);
    setQualityThreshold(node.data.quality_threshold || 0.8);
    setAutoReplan(node.data.auto_replan ?? true);
    setSpecialization(node.data.specialization || 'Research');
    setMaxDepth(node.data.max_depth || 3);
    setSizeThreshold(node.data.size_threshold || 170000);
    setOffloadStrategy(node.data.offload_strategy || 'auto');
    setAutoSummarize(node.data.auto_summarize ?? true);

    setHasUnsavedChanges(false);

    // Mark as initialized after state updates are applied
    // Use setTimeout to ensure this runs after React batches the state updates
    setTimeout(() => setIsInitialized(true), 0);
  }, [node.id]);

  // Track unsaved changes (but don't auto-save - that causes flickering)
  useEffect(() => {
    // Don't check until initialized
    if (!isInitialized) return;

    const hasChanges =
      label !== (node.data.label || '') ||
      description !== (node.data.description || '') ||
      llmInstructions !== (node.data.llmInstructions || '') ||
      model !== (node.data.model || 'gpt-4o-mini') ||
      temperature !== (node.data.temperature || 0.7) ||
      maxTokens !== (node.data.maxTokens || 1000) ||
      tool !== (node.data.tool || '') ||
      triggerId !== (node.data.trigger_id || '') ||
      prompt !== (node.data.prompt || 'Please provide input...') ||
      routingLogic !== (node.data.routing_logic || 'conditional') ||
      maxIterations !== (node.data.max_iterations || 10) ||
      earlyStopping !== (node.data.early_stopping || 'force') ||
      JSON.stringify(conditions) !== JSON.stringify(node.data.conditions || []) ||
      JSON.stringify(routes) !== JSON.stringify(node.data.routes || []) ||
      JSON.stringify(tools) !== JSON.stringify(node.data.tools || []);

    setHasUnsavedChanges(hasChanges);
    // Note: We don't auto-save here. User must click Save or press Cmd+S.
    // This prevents render loops and flickering.
  }, [
    isInitialized,
    label,
    description,
    llmInstructions,
    model,
    temperature,
    maxTokens,
    tool,
    triggerId,
    conditions,
    routes,
    routingLogic,
    prompt,
    tools,
    maxIterations,
    earlyStopping,
    strategy,
    maxSubtasks,
    enableTodos,
    enableFilesystem,
    enableSubagents,
    enableSummarization,
    validationCriteria,
    qualityThreshold,
    autoReplan,
    specialization,
    maxDepth,
    sizeThreshold,
    offloadStrategy,
    autoSummarize,
    node.data,
  ]);

  const handleSave = () => {
    // Get trigger name if a trigger is selected
    const selectedTrigger = triggers.find((t: any) => t.id === triggerId);

    const updatedData = {
      ...node.data,
      label,
      description,
      ...(node.type === 'process' && { model, temperature, maxTokens, llmInstructions }),
      ...(node.type === 'toolCall' && { tool }),
      ...(node.type === 'entryPoint' && {
        trigger_id: triggerId || undefined,
        triggerName: selectedTrigger?.name || undefined,
      }),
      ...(node.type === 'decision' && { conditions }),
      ...(node.type === 'router' && { routing_logic: routingLogic, routes }),
      ...(node.type === 'human' && { prompt }),
      ...(node.type === 'reactAgent' && {
        model,
        tools,
        max_iterations: maxIterations,
        early_stopping: earlyStopping,
      }),
      ...(node.type === 'deepPlanner' && { strategy, max_subtasks: maxSubtasks }),
      ...(node.type === 'deepExecutor' && {
        model,
        enable_todos: enableTodos,
        enable_filesystem: enableFilesystem,
        enable_subagents: enableSubagents,
        enable_summarization: enableSummarization,
        max_iterations: maxIterations,
      }),
      ...(node.type === 'deepCritic' && {
        validation_criteria: validationCriteria,
        quality_threshold: qualityThreshold,
        auto_replan: autoReplan,
      }),
      ...(node.type === 'subAgent' && {
        specialization,
        tools,
        max_depth: maxDepth,
      }),
      ...(node.type === 'contextManager' && {
        size_threshold: sizeThreshold,
        offload_strategy: offloadStrategy,
        auto_summarize: autoSummarize,
      }),
    };

    onNodeUpdate({
      ...node,
      data: updatedData,
    });

    setHasUnsavedChanges(false);
  };

  // Handle close with unsaved changes check
  const handleClose = () => {
    if (hasUnsavedChanges) {
      setShowCloseConfirm(true);
    } else {
      onClose();
    }
  };

  // Keyboard shortcut: Cmd/Ctrl + S to save
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (hasUnsavedChanges) {
          handleSave();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hasUnsavedChanges, label, description, model, temperature, maxTokens, tool, conditions]);

  // Fetch node implementation logic from API
  useEffect(() => {
    const fetchNodeLogic = async () => {
      // Only fetch for nodes that have a handler (Python implementation)
      if (!node.data.handler) {
        setNodeLogic(null);
        return;
      }

      // Extract agent ID from node data or use CIBC as default
      // TODO: Get agentId from page context/props when available
      const agentId = node.data.agent_id || 'cibc-card-activation';

      setLoadingLogic(true);
      try {
        const response = await fetch(
          `http://localhost:8000/api/agents/${agentId}/logic/node/${node.id}`
        );
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        const data = await response.json();
        setNodeLogic(data);
      } catch (error) {
        console.error('Failed to fetch node logic:', error);
        setNodeLogic(null);
      } finally {
        setLoadingLogic(false);
      }
    };

    fetchNodeLogic();
  }, [node.id, node.data.handler]);

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
    <div
      className={`flex flex-col h-full ${hasUnsavedChanges ? 'border-l-2 border-l-amber-400' : ''}`}
    >
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-fg-0">Edit Node</h3>
            {hasUnsavedChanges && (
              <div className="flex items-center gap-1.5 text-xs text-amber-400">
                <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span>Unsaved</span>
              </div>
            )}
          </div>
        </div>
        <p className="text-xs text-fg-2 mb-3">{node.type}</p>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={handleSave}
            disabled={!hasUnsavedChanges}
            size="sm"
            variant={hasUnsavedChanges ? 'default' : 'outline'}
            className="flex-1"
          >
            <Save className="w-4 h-4 mr-2" />
            Save
          </Button>
          <Button
            onClick={handleClose}
            size="sm"
            variant="outline"
            className="flex-1"
          >
            Close
          </Button>
        </div>
        {hasUnsavedChanges && (
          <p className="text-xs text-fg-3 mt-2 text-center">
            Press{' '}
            <kbd className="px-1.5 py-0.5 bg-bg-2 border border-white/10 rounded text-fg-2">
              ⌘S
            </kbd>{' '}
            to save
          </p>
        )}
      </div>

      {/* Confirm close dialog */}
      <ConfirmDialog
        open={showCloseConfirm}
        onOpenChange={setShowCloseConfirm}
        title="Unsaved Changes"
        description="You have unsaved changes. Are you sure you want to close without saving?"
        confirmLabel="Discard Changes"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={onClose}
        onCancel={() => setShowCloseConfirm(false)}
      />

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Label */}
        <div>
          <label className="text-sm font-medium text-fg-1 mb-1.5 block">Label</label>
          <Input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
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
            placeholder="Describe what this node does..."
            rows={3}
            className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        {/* Entry Point Node Fields */}
        {node.type === 'entryPoint' && (
          <div>
            <label className="text-sm font-medium text-fg-1 mb-1.5 block">Trigger</label>
            <select
              value={triggerId}
              onChange={(e) => setTriggerId(e.target.value)}
              className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="">No trigger (manual start)</option>
              {triggers.map((trigger: any) => (
                <option key={trigger.id} value={trigger.id}>
                  {trigger.name} ({trigger.type})
                </option>
              ))}
            </select>
            {triggerId && (
              <p className="text-xs text-fg-3 mt-1.5">
                This entry point will be activated when the selected trigger fires.
              </p>
            )}
          </div>
        )}

        {/* Process Node Fields */}
        {node.type === 'process' && (
          <>
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">LLM Instructions</label>
              <textarea
                value={llmInstructions}
                onChange={(e) => setLlmInstructions(e.target.value)}
                placeholder="Enter the instructions/prompt that will be sent to the LLM..."
                rows={6}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500 resize-y font-mono"
              />
              <p className="text-xs text-fg-3 mt-1">
                These instructions define how the LLM should process this node. Use specific,
                detailed prompts.
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <optgroup label="OpenAI">
                  <option value="gpt-5.1">GPT-5.1 (Best for coding/agentic)</option>
                  <option value="gpt-5-pro">GPT-5 Pro (Smartest)</option>
                  <option value="gpt-5">GPT-5</option>
                  <option value="gpt-5-mini">GPT-5 Mini (Fast)</option>
                  <option value="gpt-5-nano">GPT-5 Nano (Fastest)</option>
                  <option value="gpt-4.1">GPT-4.1 (Non-reasoning)</option>
                </optgroup>
                <optgroup label="Anthropic">
                  <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5 (Latest)</option>
                  <option value="claude-3-7-sonnet-20250219">Claude 3.7 Sonnet</option>
                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                  <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku</option>
                  <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                </optgroup>
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
                className="w-full"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Tokens</label>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
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
              <Button
                size="sm"
                variant="outline"
                onClick={addCondition}
                className="border-white/10"
              >
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
                      className="bg-bg-0 border-white/10 text-sm"
                    />
                    <select
                      value={condition.operator}
                      onChange={(e) => updateCondition(index, { operator: e.target.value })}
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
                      className="bg-bg-0 border-white/10 text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => removeCondition(index)}
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

        {/* Router Node Fields */}
        {node.type === 'router' && (
          <div>
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Routing Logic</label>
              <select
                value={routingLogic}
                onChange={(e) => setRoutingLogic(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="conditional">Conditional (if/else)</option>
                <option value="llm">LLM-based</option>
                <option value="intent">Intent Classification</option>
              </select>
            </div>
            <div className="mt-3">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-fg-1">Routes</label>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setRoutes([...routes, { name: '', condition: '', target: '' }])}
                  className="border-white/10"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Route
                </Button>
              </div>
              <div className="space-y-2">
                {routes.map((route: any, index: number) => (
                  <Card key={index} className="p-3 bg-bg-2 border-white/10">
                    <div className="space-y-2">
                      <Input
                        placeholder="Route Name"
                        value={route.name}
                        onChange={(e) => {
                          const newRoutes = [...routes];
                          newRoutes[index] = { ...route, name: e.target.value };
                          setRoutes(newRoutes);
                        }}
                        className="bg-bg-0 border-white/10 text-sm"
                      />
                      <Input
                        placeholder="Condition (e.g., intent == 'support')"
                        value={route.condition}
                        onChange={(e) => {
                          const newRoutes = [...routes];
                          newRoutes[index] = { ...route, condition: e.target.value };
                          setRoutes(newRoutes);
                        }}
                        className="bg-bg-0 border-white/10 text-sm"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setRoutes(routes.filter((_: any, i: number) => i !== index))}
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
          </div>
        )}

        {/* Human Input Node Fields */}
        {node.type === 'human' && (
          <div>
            <label className="text-sm font-medium text-fg-1 mb-1.5 block">User Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="What should we ask the user?"
              rows={3}
              className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500 resize-none"
            />
            <p className="text-xs text-fg-3 mt-1">
              Workflow will pause here and wait for human input
            </p>
          </div>
        )}

        {/* ReAct Agent Node Fields */}
        {node.type === 'reactAgent' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <optgroup label="OpenAI">
                  <option value="gpt-5.1">GPT-5.1 (Best for coding/agentic)</option>
                  <option value="gpt-5-pro">GPT-5 Pro (Smartest)</option>
                  <option value="gpt-5">GPT-5</option>
                  <option value="gpt-5-mini">GPT-5 Mini (Fast)</option>
                  <option value="gpt-5-nano">GPT-5 Nano (Fastest)</option>
                  <option value="gpt-4.1">GPT-4.1 (Non-reasoning)</option>
                </optgroup>
                <optgroup label="Anthropic">
                  <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5 (Latest)</option>
                  <option value="claude-3-7-sonnet-20250219">Claude 3.7 Sonnet</option>
                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                  <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Iterations</label>
              <Input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                className="bg-bg-2 border-white/10"
                min={1}
                max={100}
              />
              <p className="text-xs text-fg-3 mt-1">
                Maximum reasoning/action cycles before stopping
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Early Stopping</label>
              <select
                value={earlyStopping}
                onChange={(e) => setEarlyStopping(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="force">Force (stop at max iterations)</option>
                <option value="generate">Generate (allow final response)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-fg-1">Tools</label>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setTools([...tools, { name: '', description: '' }])}
                  className="border-white/10"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Tool
                </Button>
              </div>
              <div className="space-y-2">
                {tools.map((toolItem: any, index: number) => (
                  <Card key={index} className="p-3 bg-bg-2 border-white/10">
                    <div className="space-y-2">
                      <Input
                        placeholder="Tool Name (e.g., web_search)"
                        value={toolItem.name}
                        onChange={(e) => {
                          const newTools = [...tools];
                          newTools[index] = { ...toolItem, name: e.target.value };
                          setTools(newTools);
                        }}
                        className="bg-bg-0 border-white/10 text-sm"
                      />
                      <Input
                        placeholder="Description"
                        value={toolItem.description}
                        onChange={(e) => {
                          const newTools = [...tools];
                          newTools[index] = { ...toolItem, description: e.target.value };
                          setTools(newTools);
                        }}
                        className="bg-bg-0 border-white/10 text-sm"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setTools(tools.filter((_: any, i: number) => i !== index))}
                        className="w-full border-red-600/30 text-red-400 hover:bg-red-600/10"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Remove
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
              <p className="text-xs text-fg-3 mt-2">
                ReAct agent will reason, select tools, and take actions in a loop
              </p>
            </div>
          </div>
        )}

        {/* Deep Planner Node Fields */}
        {node.type === 'deepPlanner' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                Planning Strategy
              </label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="hierarchical">Hierarchical (top-down)</option>
                <option value="sequential">Sequential (step-by-step)</option>
                <option value="adaptive">Adaptive (dynamic)</option>
              </select>
              <p className="text-xs text-fg-3 mt-1">How the planner breaks down complex tasks</p>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Subtasks</label>
              <Input
                type="number"
                value={maxSubtasks}
                onChange={(e) => setMaxSubtasks(parseInt(e.target.value))}
                className="bg-bg-2 border-white/10"
                min={1}
                max={50}
              />
              <p className="text-xs text-fg-3 mt-1">Maximum number of subtasks to decompose into</p>
            </div>
          </div>
        )}

        {/* Deep Executor Node Fields */}
        {node.type === 'deepExecutor' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <optgroup label="Anthropic (Recommended for Deep Execution)">
                  <option value="claude-sonnet-4-5-20250929">Claude Sonnet 4.5 (Latest)</option>
                  <option value="claude-3-7-sonnet-20250219">Claude 3.7 Sonnet</option>
                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                  <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                </optgroup>
                <optgroup label="OpenAI">
                  <option value="gpt-5.1">GPT-5.1 (Best for coding/agentic)</option>
                  <option value="gpt-5-pro">GPT-5 Pro (Smartest)</option>
                  <option value="gpt-5">GPT-5</option>
                  <option value="gpt-5-mini">GPT-5 Mini (Fast)</option>
                  <option value="gpt-5-nano">GPT-5 Nano (Fastest)</option>
                  <option value="gpt-4.1">GPT-4.1 (Non-reasoning)</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Middleware</label>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableTodos}
                    onChange={(e) => setEnableTodos(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-fg-1">TodoList (task planning)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableFilesystem}
                    onChange={(e) => setEnableFilesystem(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-fg-1">Filesystem (file operations)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableSubagents}
                    onChange={(e) => setEnableSubagents(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-fg-1">SubAgent (delegation)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableSummarization}
                    onChange={(e) => setEnableSummarization(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm text-fg-1">Summarization (context mgmt)</span>
                </label>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Iterations</label>
              <Input
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                className="bg-bg-2 border-white/10"
                min={1}
                max={20}
              />
              <p className="text-xs text-fg-3 mt-1">Maximum execution cycles before stopping</p>
            </div>
          </div>
        )}

        {/* Deep Critic Node Fields */}
        {node.type === 'deepCritic' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                Validation Criteria
              </label>
              <div className="space-y-2">
                {['completeness', 'accuracy', 'clarity', 'relevance', 'efficiency'].map(
                  (criterion) => (
                    <label key={criterion} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={validationCriteria.includes(criterion)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setValidationCriteria([...validationCriteria, criterion]);
                          } else {
                            setValidationCriteria(
                              validationCriteria.filter((c) => c !== criterion)
                            );
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <span className="text-sm text-fg-1 capitalize">{criterion}</span>
                    </label>
                  )
                )}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                Quality Threshold ({qualityThreshold})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={qualityThreshold}
                onChange={(e) => setQualityThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-fg-3 mt-1">Minimum quality score to pass validation</p>
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoReplan}
                  onChange={(e) => setAutoReplan(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm text-fg-1">Auto-replan on failure</span>
              </label>
              <p className="text-xs text-fg-3 mt-1">
                Automatically trigger replanning if quality is below threshold
              </p>
            </div>
          </div>
        )}

        {/* Sub-Agent Node Fields */}
        {node.type === 'subAgent' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Specialization</label>
              <Input
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                placeholder="e.g., Research, Analysis, Writing"
                className="bg-bg-2 border-white/10"
              />
              <p className="text-xs text-fg-3 mt-1">The sub-agent's area of expertise</p>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Max Depth</label>
              <Input
                type="number"
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                className="bg-bg-2 border-white/10"
                min={1}
                max={10}
              />
              <p className="text-xs text-fg-3 mt-1">
                Maximum delegation depth (prevents infinite recursion)
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-fg-1">Available Tools</label>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setTools([...tools, { name: '', description: '' }])}
                  className="border-white/10"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Tool
                </Button>
              </div>
              <div className="space-y-2">
                {tools.map((toolItem: any, index: number) => (
                  <Card key={index} className="p-3 bg-bg-2 border-white/10">
                    <div className="space-y-2">
                      <Input
                        placeholder="Tool Name"
                        value={toolItem.name}
                        onChange={(e) => {
                          const newTools = [...tools];
                          newTools[index] = { ...toolItem, name: e.target.value };
                          setTools(newTools);
                        }}
                        className="bg-bg-0 border-white/10 text-sm"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setTools(tools.filter((_: any, i: number) => i !== index))}
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
          </div>
        )}

        {/* Context Manager Node Fields */}
        {node.type === 'contextManager' && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                Size Threshold (chars)
              </label>
              <Input
                type="number"
                value={sizeThreshold}
                onChange={(e) => setSizeThreshold(parseInt(e.target.value))}
                className="bg-bg-2 border-white/10"
                min={1000}
                max={500000}
                step={1000}
              />
              <p className="text-xs text-fg-3 mt-1">Content larger than this will be offloaded</p>
            </div>

            <div>
              <label className="text-sm font-medium text-fg-1 mb-1.5 block">Offload Strategy</label>
              <select
                value={offloadStrategy}
                onChange={(e) => setOffloadStrategy(e.target.value)}
                className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="auto">Auto (intelligent)</option>
                <option value="aggressive">Aggressive (offload early)</option>
                <option value="conservative">Conservative (keep in memory)</option>
              </select>
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSummarize}
                  onChange={(e) => setAutoSummarize(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm text-fg-1">Auto-summarize offloaded content</span>
              </label>
              <p className="text-xs text-fg-3 mt-1">
                Generate summaries of offloaded content for reference
              </p>
            </div>
          </div>
        )}

        {/* Implementation Details - Python source analysis */}
        {node.data.handler && (
          <div className="mt-4 border-t border-white/10 pt-4">
            <button
              onClick={() => setShowImplementation(!showImplementation)}
              className="flex items-center gap-2 w-full text-left p-2 hover:bg-bg-3 rounded transition-colors"
            >
              {showImplementation ? (
                <ChevronDown className="w-4 h-4 text-fg-2" />
              ) : (
                <ChevronRight className="w-4 h-4 text-fg-2" />
              )}
              <Code2 className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-fg-1">Implementation Details</span>
              {nodeLogic && !loadingLogic && (
                <span className="text-xs text-fg-3 ml-auto">Python Source</span>
              )}
            </button>

            {showImplementation && (
              <div className="mt-3 space-y-4 px-2">
                {loadingLogic ? (
                  <div className="text-sm text-fg-3 py-8 text-center">
                    <div className="animate-pulse">Loading implementation details...</div>
                  </div>
                ) : nodeLogic ? (
                  <>
                    {/* System Prompts */}
                    {nodeLogic.prompts && nodeLogic.prompts.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-fg-1 mb-2 uppercase tracking-wide">
                          System Prompts
                        </h4>
                        <PromptViewer prompts={nodeLogic.prompts} nodeId={node.id} />
                      </div>
                    )}

                    {/* Business Logic & Conditional Rules */}
                    {(nodeLogic.conditions?.length > 0 ||
                      nodeLogic.business_rules?.length > 0 ||
                      nodeLogic.function_calls?.length > 0) && (
                      <div>
                        <h4 className="text-xs font-semibold text-fg-1 mb-2 uppercase tracking-wide">
                          Logic & Business Rules
                        </h4>
                        <BusinessRulesList
                          rules={nodeLogic.business_rules || []}
                          conditions={nodeLogic.conditions || []}
                          functionCalls={nodeLogic.function_calls || []}
                          nodeId={node.id}
                        />
                      </div>
                    )}

                    {/* State Mutations */}
                    {nodeLogic.state_mutations && nodeLogic.state_mutations.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-fg-1 mb-2 uppercase tracking-wide">
                          State Modifications
                        </h4>
                        <StateMutationTable
                          mutations={nodeLogic.state_mutations}
                          nodeId={node.id}
                        />
                      </div>
                    )}

                    {/* LLM Configuration */}
                    {nodeLogic.llm_config && Object.keys(nodeLogic.llm_config).length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-fg-1 mb-2 uppercase tracking-wide">
                          LLM Configuration
                        </h4>
                        <Card className="p-3 bg-bg-3 border-white/10">
                          <div className="space-y-1 text-xs">
                            {nodeLogic.llm_config.model && (
                              <div className="flex items-center gap-2">
                                <span className="text-fg-3">Model:</span>
                                <code className="text-blue-300 font-mono">
                                  {nodeLogic.llm_config.model}
                                </code>
                              </div>
                            )}
                            {nodeLogic.llm_config.temperature !== undefined && (
                              <div className="flex items-center gap-2">
                                <span className="text-fg-3">Temperature:</span>
                                <code className="text-blue-300 font-mono">
                                  {nodeLogic.llm_config.temperature}
                                </code>
                              </div>
                            )}
                          </div>
                        </Card>
                      </div>
                    )}

                    {/* Python Source Code */}
                    {nodeLogic.source_code && (
                      <div>
                        <h4 className="text-xs font-semibold text-fg-1 mb-2 uppercase tracking-wide">
                          Python Implementation
                        </h4>
                        <CodeBlock
                          code={nodeLogic.source_code}
                          language="python"
                          title={`${node.id} Implementation`}
                          readonly={true}
                          maxHeight="400px"
                        />
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-sm text-fg-3 italic py-4 text-center">
                    No Python implementation found for this node
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/10">
        <Button
          variant="outline"
          className="w-full border-red-600/30 text-red-400 hover:bg-red-600/10"
          onClick={() => onNodeDelete && setShowDeleteConfirm(true)}
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete Node
        </Button>
      </div>

      {/* Confirm delete dialog */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete Node"
        description={`Are you sure you want to delete "${label || node.type}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="destructive"
        onConfirm={() => {
          if (onNodeDelete) {
            onNodeDelete(node.id);
            onClose();
          }
        }}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}
