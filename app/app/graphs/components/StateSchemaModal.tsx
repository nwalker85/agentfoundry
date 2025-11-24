'use client';

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { StateSchemaTab } from './StateSchemaTab';

interface StateSchemaModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schemas: any[];
  activeSchemaId: string | null;
  onSelectSchema: (id: string | null) => void;
  onSaveSchema: (schema: any) => Promise<void>;
  onDeleteSchema: (schemaId: string) => Promise<void>;
}

export function StateSchemaModal({
  open,
  onOpenChange,
  schemas,
  activeSchemaId,
  onSelectSchema,
  onSaveSchema,
  onDeleteSchema,
}: StateSchemaModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[90vw] w-[1200px] h-[80vh] p-0">
        <DialogHeader className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <DialogTitle>State Schema Designer</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-hidden" style={{ height: 'calc(80vh - 60px)' }}>
          <StateSchemaTab
            schemas={schemas}
            activeSchemaId={activeSchemaId}
            onSelectSchema={onSelectSchema}
            onSaveSchema={onSaveSchema}
            onDeleteSchema={onDeleteSchema}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}
