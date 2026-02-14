"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { differenceInDays, parseISO } from "date-fns";
import type { PipelineItem } from "./types";

interface PipelineCardProps {
  item: PipelineItem;
  isDragging?: boolean;
  onRemove?: () => void;
  onUpdateNotes?: (notes: string) => void;
}

export function PipelineCard({ item, isDragging, onRemove, onUpdateNotes }: PipelineCardProps) {
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState(item.notes || "");

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({ id: item.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const daysRemaining = item.data_encerramento
    ? differenceInDays(parseISO(item.data_encerramento), new Date())
    : null;

  const urgencyClass =
    daysRemaining !== null && daysRemaining <= 0
      ? "border-l-red-500"
      : daysRemaining !== null && daysRemaining <= 3
      ? "border-l-orange-500"
      : daysRemaining !== null && daysRemaining <= 7
      ? "border-l-yellow-500"
      : "border-l-transparent";

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`bg-[var(--surface-0)] rounded-lg border border-[var(--border)] border-l-4 ${urgencyClass} p-3 cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md transition-shadow ${
        isDragging || isSortableDragging ? "opacity-50 shadow-lg ring-2 ring-brand-blue" : ""
      }`}
    >
      {/* Header with UF badge */}
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <h4 className="text-xs font-semibold text-[var(--text-primary)] line-clamp-2 flex-1">
          {item.objeto.length > 80 ? item.objeto.slice(0, 80) + "..." : item.objeto}
        </h4>
        {item.uf && (
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-brand-blue/10 text-brand-blue flex-shrink-0">
            {item.uf}
          </span>
        )}
      </div>

      {/* Agency */}
      {item.orgao && (
        <p className="text-[10px] text-[var(--text-secondary)] truncate mb-2">{item.orgao}</p>
      )}

      {/* Value + Deadline row */}
      <div className="flex items-center justify-between text-[10px] mb-2">
        {item.valor_estimado != null && (
          <span className="font-semibold text-[var(--text-primary)]">
            {formatCurrency(item.valor_estimado)}
          </span>
        )}
        {daysRemaining !== null && (
          <span
            className={`font-medium ${
              daysRemaining <= 0
                ? "text-red-600 dark:text-red-400"
                : daysRemaining <= 3
                ? "text-orange-600 dark:text-orange-400"
                : "text-[var(--text-secondary)]"
            }`}
          >
            {daysRemaining <= 0 ? "Encerrado" : `${daysRemaining}d restantes`}
          </span>
        )}
      </div>

      {/* Notes */}
      {editingNotes ? (
        <div className="mt-2" onClick={(e) => e.stopPropagation()} onPointerDown={(e) => e.stopPropagation()}>
          <textarea
            value={notesValue}
            onChange={(e) => setNotesValue(e.target.value)}
            className="w-full text-[10px] p-1.5 rounded border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-primary)] resize-none"
            rows={2}
            placeholder="Suas anotações..."
            autoFocus
          />
          <div className="flex gap-1 mt-1">
            <button
              onClick={() => {
                onUpdateNotes?.(notesValue);
                setEditingNotes(false);
              }}
              className="text-[10px] px-2 py-0.5 rounded bg-brand-blue text-white hover:bg-brand-blue/90"
            >
              Salvar
            </button>
            <button
              onClick={() => {
                setNotesValue(item.notes || "");
                setEditingNotes(false);
              }}
              className="text-[10px] px-2 py-0.5 rounded text-[var(--text-secondary)] hover:bg-[var(--surface-1)]"
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : item.notes ? (
        <p
          className="text-[10px] text-[var(--text-tertiary)] italic mt-1 cursor-pointer hover:text-[var(--text-secondary)]"
          onClick={(e) => { e.stopPropagation(); setEditingNotes(true); }}
          onPointerDown={(e) => e.stopPropagation()}
        >
          {item.notes.length > 60 ? item.notes.slice(0, 60) + "..." : item.notes}
        </p>
      ) : null}

      {/* Actions */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[var(--border)]">
        <div className="flex gap-1.5">
          {item.link_pncp && (
            <a
              href={item.link_pncp}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-brand-blue hover:underline"
              onClick={(e) => e.stopPropagation()}
              onPointerDown={(e) => e.stopPropagation()}
            >
              Ver edital
            </a>
          )}
          <button
            onClick={(e) => { e.stopPropagation(); setEditingNotes(true); }}
            onPointerDown={(e) => e.stopPropagation()}
            className="text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
          >
            {item.notes ? "Editar nota" : "Anotar"}
          </button>
        </div>
        {onRemove && (
          <button
            onClick={(e) => { e.stopPropagation(); onRemove(); }}
            onPointerDown={(e) => e.stopPropagation()}
            className="text-[10px] text-red-500 hover:text-red-700"
          >
            Remover
          </button>
        )}
      </div>
    </div>
  );
}
