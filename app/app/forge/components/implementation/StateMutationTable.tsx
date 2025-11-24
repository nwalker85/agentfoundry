'use client';

import { Database, ArrowRight } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface StateMutation {
  field: string;
  action: string;
  variable: string;
}

interface StateMutationTableProps {
  mutations: StateMutation[];
  nodeId: string;
}

export function StateMutationTable({ mutations, nodeId }: StateMutationTableProps) {
  if (!mutations || mutations.length === 0) {
    return (
      <div className="text-sm text-fg-3 italic px-3 py-2">No state mutations in this node</div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center gap-2 px-2">
        <Database className="w-4 h-4 text-green-400" />
        <span className="text-xs font-medium text-fg-1">
          State Modifications ({mutations.length})
        </span>
      </div>

      {/* Table */}
      <div className="border border-white/10 rounded-md overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-bg-3 border-white/10 hover:bg-bg-3">
              <TableHead className="text-xs text-fg-2 font-medium w-[30%]">Field</TableHead>
              <TableHead className="text-xs text-fg-2 font-medium w-[10%]"></TableHead>
              <TableHead className="text-xs text-fg-2 font-medium">Value/Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mutations.map((mutation, index) => (
              <TableRow key={index} className="border-white/5 hover:bg-bg-3/50">
                <TableCell className="font-mono text-xs text-green-300">
                  state["{mutation.field}"]
                </TableCell>
                <TableCell className="text-center">
                  <ArrowRight className="w-3 h-3 text-fg-3 mx-auto" />
                </TableCell>
                <TableCell className="font-mono text-xs text-fg-2">
                  <div className="max-w-md truncate" title={mutation.action}>
                    {mutation.action}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Info */}
      <div className="text-xs text-fg-3 px-2">These fields are modified during node execution</div>
    </div>
  );
}
