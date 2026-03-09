"use client";

import { useState } from "react";
import { STAGES_ORDER, STAGE_CONFIG, type PipelineItem, type PipelineStage } from "./types";
import { toast } from "sonner";
import { formatCurrencyBR } from "../../lib/format-currency";

interface PipelineMobileTabsProps {
  items: PipelineItem[];
  onUpdateItem: (id: string, updates: { stage?: PipelineStage; notes?: string; version?: number }) => Promise<unknown>;
  onRemoveItem: (id: string) => void;
}

/**
 * GTM-POLISH-002 AC5-AC8: Mobile pipeline view with tabs.
 * Replaces horizontal kanban scroll with vertical tab-based list.
 * "Mover para..." button replaces drag-and-drop on mobile.
 */
export function PipelineMobileTabs({ items, onUpdateItem, onRemoveItem }: PipelineMobileTabsProps) {
  const [activeTab, setActiveTab] = useState<PipelineStage>("descoberta");
  const [movingItemId, setMovingItemId] = useState<string | null>(null);

  const getItemsByStage = (stage: PipelineStage) => items.filter((i) => i.stage === stage);

  const handleMove = async (itemId: string, targetStage: PipelineStage) => {
    setMovingItemId(null);
    try {
      // STORY-307 AC11: Send version for optimistic locking
      const item = items.find((i) => i.id === itemId);
      await onUpdateItem(itemId, { stage: targetStage, version: item?.version });
      toast.success(`Movido para ${STAGE_CONFIG[targetStage].label}`);
    } catch (err: unknown) {
      // STORY-307 AC11: Show conflict-specific message on 409
      const isConflict = err !== null && typeof err === 'object' && 'isConflict' in err && (err as { isConflict: boolean }).isConflict;
      if (isConflict) {
        toast.error("Item foi atualizado por outra operação. Recarregue a página.");
      } else {
        toast.error("Erro ao mover item");
      }
    }
  };

  /** UX-401 AC5+AC7: Unified currency formatting with abbreviations */
  const formatCurrency = (value: number) => formatCurrencyBR(value);

  const tabItems = getItemsByStage(activeTab);

  return (
    <div data-testid="pipeline-mobile-tabs">
      {/* AC5/AC8: Tabs with badge count */}
      <div className="flex overflow-x-auto gap-1 pb-3 -mx-1 px-1 scrollbar-hide" role="tablist">
        {STAGES_ORDER.map((stage) => {
          const count = getItemsByStage(stage).length;
          const config = STAGE_CONFIG[stage];
          const isActive = activeTab === stage;
          return (
            <button
              key={stage}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveTab(stage)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-button whitespace-nowrap transition-colors ${
                isActive
                  ? "bg-[var(--brand-navy)] text-white"
                  : "bg-[var(--surface-1)] text-[var(--ink-secondary)] hover:bg-[var(--surface-2)]"
              }`}
              data-testid={`pipeline-tab-${stage}`}
            >
              <span>{config.icon}</span>
              <span>{config.label}</span>
              <span
                className={`inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 rounded-full text-[10px] font-bold ${
                  isActive
                    ? "bg-white/20 text-white"
                    : "bg-[var(--surface-2)] text-[var(--ink-muted)]"
                }`}
                data-testid={`pipeline-tab-count-${stage}`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* AC6: Vertical list of cards for active tab */}
      <div className="space-y-3 mt-2" role="tabpanel">
        {tabItems.length === 0 ? (
          <div className="py-12 text-center text-[var(--ink-muted)] text-sm">
            Nenhum item em {STAGE_CONFIG[activeTab].label}
          </div>
        ) : (
          tabItems.map((item) => (
            <div
              key={item.id}
              className="p-4 bg-[var(--surface-0)] border border-[var(--border)] rounded-card"
              data-testid="pipeline-mobile-card"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <h4 className="text-sm font-semibold text-[var(--ink)] line-clamp-2 flex-1">
                  {item.objeto}
                </h4>
                {item.uf && (
                  <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-[var(--brand-blue-subtle)] text-[var(--brand-blue)] flex-shrink-0">
                    {item.uf}
                  </span>
                )}
              </div>

              {/* Agency */}
              {item.orgao && (
                <p className="text-xs text-[var(--ink-secondary)] truncate mb-2">{item.orgao}</p>
              )}

              {/* Value + Deadline */}
              <div className="flex items-center gap-3 text-xs mb-3">
                {item.valor_estimado != null && (
                  <span className="font-semibold text-[var(--ink)]">
                    {formatCurrency(item.valor_estimado)}
                  </span>
                )}
                {item.data_encerramento && (
                  <span className="text-[var(--ink-muted)]">
                    Enc: {new Date(item.data_encerramento).toLocaleDateString("pt-BR")}
                  </span>
                )}
              </div>

              {/* Notes */}
              {item.notes && (
                <p className="text-xs text-[var(--ink-muted)] italic mb-3 line-clamp-2">
                  {item.notes}
                </p>
              )}

              {/* AC7: "Mover para..." + actions */}
              <div className="flex items-center gap-2 pt-2 border-t border-[var(--border)]">
                {/* Move dropdown */}
                <div className="relative flex-1">
                  <button
                    onClick={() => setMovingItemId(movingItemId === item.id ? null : item.id)}
                    className="w-full px-3 py-1.5 text-xs font-medium text-[var(--brand-blue)] border border-[var(--brand-blue)]/30 rounded-button hover:bg-[var(--brand-blue-subtle)] transition-colors text-left flex items-center justify-between"
                    data-testid="move-to-button"
                  >
                    <span>Mover para...</span>
                    <svg
                      className={`w-3 h-3 transition-transform ${movingItemId === item.id ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {movingItemId === item.id && (
                    <div className="absolute left-0 right-0 top-full mt-1 bg-[var(--surface-elevated)] border border-[var(--border)] rounded-card shadow-lg z-10 overflow-hidden">
                      {STAGES_ORDER.filter((s) => s !== item.stage).map((stage) => (
                        <button
                          key={stage}
                          onClick={() => handleMove(item.id, stage)}
                          className="w-full px-3 py-2 text-xs text-left hover:bg-[var(--surface-1)] transition-colors flex items-center gap-2"
                          data-testid={`move-to-${stage}`}
                        >
                          <span>{STAGE_CONFIG[stage].icon}</span>
                          <span>{STAGE_CONFIG[stage].label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* View edital */}
                {item.link_pncp && (
                  <a
                    href={item.link_pncp}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1.5 text-xs text-[var(--brand-blue)] hover:underline"
                  >
                    Ver edital
                  </a>
                )}

                {/* Remove */}
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="px-2 py-1.5 text-xs text-red-500 hover:text-red-700"
                >
                  Remover
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
