'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { TriggersTab } from './TriggersTab';

interface TriggerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  triggers: any[];
  selectedTriggerIds: string[];
  onToggleTrigger: (triggerId: string, selected: boolean) => void;
  onSaveTrigger: (trigger: any) => Promise<void>;
  onDeleteTrigger: (triggerId: string) => Promise<void>;
}

export function TriggerModal({
  open,
  onOpenChange,
  triggers,
  selectedTriggerIds,
  onToggleTrigger,
  onSaveTrigger,
  onDeleteTrigger,
}: TriggerModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[90vw] w-[1200px] h-[80vh] p-0">
        <DialogHeader className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <DialogTitle>Trigger Registry</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-hidden" style={{ height: 'calc(80vh - 60px)' }}>
          <TriggersTab
            triggers={triggers}
            selectedTriggerIds={selectedTriggerIds}
            onToggleTrigger={onToggleTrigger}
            onSaveTrigger={onSaveTrigger}
            onDeleteTrigger={onDeleteTrigger}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
