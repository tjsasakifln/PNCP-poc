"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { STAGE_CONFIG, type PipelineItem, type PipelineStage } from "./types";
import { PipelineCard } from "./PipelineCard";

interface PipelineColumnProps {
  stage: PipelineStage;
  items: PipelineItem[];
  onRemove: (id: string) => void;
  onUpdateNotes: (id: string, notes: string) => void;
}

export function PipelineColumn({ stage, items, onRemove, onUpdateNotes }: PipelineColumnProps) {
  const config = STAGE_CONFIG[stage];
  const { setNodeRef, isOver } = useDroppable({ id: stage });

  return (
    <div
      ref={setNodeRef}
      role="group"
      aria-labelledby={`pipeline-column-heading-${stage}`}
      className={`flex-shrink-0 w-72 flex flex-col rounded-xl transition-colors ${
        isOver
          ? "bg-brand-blue/10 ring-2 ring-brand-blue/30"
          : "bg-[var(--surface-1)] border border-[var(--border-strong)]"
      }`}
    >
      {/* Column Header */}
      <div className="p-3 border-b border-[var(--border-strong)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg" aria-hidden="true">
              {config.icon}
            </span>
            <h3
              id={`pipeline-column-heading-${stage}`}
              className="font-semibold text-sm text-[var(--text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-1 rounded-sm"
            >
              {config.label}
            </h3>
          </div>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.color}`}
            aria-label={`${items.length} itens nesta etapa`}
          >
            {items.length}
          </span>
        </div>
      </div>

      {/* Items */}
      <div className="flex-1 p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-280px)]">
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          {items.map((item) => (
            <PipelineCard
              key={item.id}
              item={item}
              onRemove={() => onRemove(item.id)}
              onUpdateNotes={(notes) => onUpdateNotes(item.id, notes)}
            />
          ))}
        </SortableContext>

        {items.length === 0 && (
          <div className="text-center py-8 text-[var(--text-tertiary)] text-xs">
            Arraste itens aqui
          </div>
        )}
      </div>
    </div>
  );
}
