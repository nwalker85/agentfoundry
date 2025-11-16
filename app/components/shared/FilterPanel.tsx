/**
 * Agent Foundry - Filter Panel Component
 * Standardized filter sidebar with multiple filter types
 */

"use client";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FilterOption {
  id: string;
  label: string;
  count?: number;
}

export interface FilterGroup {
  id: string;
  label: string;
  options: FilterOption[];
}

interface FilterPanelProps {
  groups: FilterGroup[];
  selectedFilters: Record<string, string[]>;
  onFilterChange: (groupId: string, optionId: string, checked: boolean) => void;
  onClearAll?: () => void;
  className?: string;
}

export function FilterPanel({
  groups,
  selectedFilters,
  onFilterChange,
  onClearAll,
  className,
}: FilterPanelProps) {
  const totalSelected = Object.values(selectedFilters).reduce(
    (sum, filters) => sum + filters.length,
    0
  );

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-fg-0">Filters</h3>
        {totalSelected > 0 && onClearAll && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="h-auto px-2 py-1 text-xs"
          >
            Clear all
          </Button>
        )}
      </div>

      {/* Filter Groups */}
      {groups.map((group, index) => (
        <div key={group.id}>
          {index > 0 && <Separator className="mb-6" />}
          <div className="space-y-3">
            <h4 className="text-xs font-medium text-fg-2 uppercase tracking-wide">
              {group.label}
            </h4>
            <div className="space-y-2">
              {group.options.map((option) => {
                const isChecked =
                  selectedFilters[group.id]?.includes(option.id) || false;

                return (
                  <div key={option.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={`${group.id}-${option.id}`}
                      checked={isChecked}
                      onCheckedChange={(checked) =>
                        onFilterChange(group.id, option.id, checked as boolean)
                      }
                    />
                    <Label
                      htmlFor={`${group.id}-${option.id}`}
                      className="flex-1 text-sm cursor-pointer flex items-center justify-between"
                    >
                      <span className="text-fg-1">{option.label}</span>
                      {option.count !== undefined && (
                        <span className="text-xs text-fg-2 ml-2">
                          {option.count}
                        </span>
                      )}
                    </Label>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Active filter chips display
 */
export function ActiveFilters({
  selectedFilters,
  groups,
  onRemove,
  className,
}: {
  selectedFilters: Record<string, string[]>;
  groups: FilterGroup[];
  onRemove: (groupId: string, optionId: string) => void;
  className?: string;
}) {
  const activeFilters: Array<{ groupId: string; optionId: string; label: string }> = [];

  Object.entries(selectedFilters).forEach(([groupId, optionIds]) => {
    const group = groups.find((g) => g.id === groupId);
    if (!group) return;

    optionIds.forEach((optionId) => {
      const option = group.options.find((o) => o.id === optionId);
      if (option) {
        activeFilters.push({
          groupId,
          optionId,
          label: `${group.label}: ${option.label}`,
        });
      }
    });
  });

  if (activeFilters.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {activeFilters.map((filter) => (
        <button
          key={`${filter.groupId}-${filter.optionId}`}
          onClick={() => onRemove(filter.groupId, filter.optionId)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-600/10 text-blue-500 hover:bg-blue-600/20 transition-colors"
        >
          {filter.label}
          <X className="w-3 h-3" />
        </button>
      ))}
    </div>
  );
}
