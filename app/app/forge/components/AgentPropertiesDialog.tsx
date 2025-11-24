'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

export interface AgentMetadata {
  name: string;
  description: string;
  version: string;
  tags: string[];
}

interface AgentPropertiesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  metadata: AgentMetadata;
  onSave: (metadata: AgentMetadata) => void;
  mode: 'new' | 'edit';
}

export function AgentPropertiesDialog({
  open,
  onOpenChange,
  metadata,
  onSave,
  mode,
}: AgentPropertiesDialogProps) {
  const [name, setName] = useState(metadata.name);
  const [description, setDescription] = useState(metadata.description);
  const [version, setVersion] = useState(metadata.version);
  const [tagsInput, setTagsInput] = useState(metadata.tags.join(', '));

  useEffect(() => {
    setName(metadata.name);
    setDescription(metadata.description);
    setVersion(metadata.version);
    setTagsInput(metadata.tags.join(', '));
  }, [metadata, open]);

  const handleSave = () => {
    const tags = tagsInput
      .split(',')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);

    onSave({
      name,
      description,
      version,
      tags,
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>{mode === 'new' ? 'Create New Agent' : 'Agent Properties'}</DialogTitle>
          <DialogDescription>
            {mode === 'new'
              ? 'Set up your new agent with a name and description.'
              : 'Update your agent metadata and properties.'}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="name">Agent Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-awesome-agent"
              autoFocus
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this agent does..."
              rows={3}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="version">Version</Label>
            <Input
              id="version"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="1.0.0"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="customer-service, chatbot, support"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            {mode === 'new' ? 'Create Agent' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
