"use client";

import { useEffect, useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { usePipeline } from "../../hooks/usePipeline";
import { STAGES_ORDER, STAGE_CONFIG, type PipelineItem, type PipelineStage } from "./types";
import { PipelineColumn } from "./PipelineColumn";
import { PipelineCard } from "./PipelineCard";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState } from "../../components/EmptyState";
import { useAuth } from "../components/AuthProvider";
import { getUserFriendlyError } from "../../lib/error-messages";
import { toast } from "sonner";

export default function PipelinePage() {
  const { session } = useAuth();
  const { items, loading, error, fetchItems, updateItem, removeItem } = usePipeline();
  const [activeItem, setActiveItem] = useState<PipelineItem | null>(null);
  const [optimisticItems, setOptimisticItems] = useState<PipelineItem[]>([]);

  useEffect(() => {
    setOptimisticItems(items);
  }, [items]);

  useEffect(() => {
    if (session?.access_token) {
      fetchItems();
    }
  }, [session?.access_token, fetchItems]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const getItemsByStage = useCallback(
    (stage: PipelineStage) => optimisticItems.filter((item) => item.stage === stage),
    [optimisticItems]
  );

  const handleDragStart = (event: DragStartEvent) => {
    const item = optimisticItems.find((i) => i.id === event.active.id);
    if (item) setActiveItem(item);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    const activeItemData = optimisticItems.find((i) => i.id === activeId);
    if (!activeItemData) return;

    // Check if dragging over a column
    const targetStage = STAGES_ORDER.includes(overId as PipelineStage)
      ? (overId as PipelineStage)
      : optimisticItems.find((i) => i.id === overId)?.stage;

    if (targetStage && targetStage !== activeItemData.stage) {
      setOptimisticItems((prev) =>
        prev.map((i) => (i.id === activeId ? { ...i, stage: targetStage } : i))
      );
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveItem(null);

    if (!over) return;

    const activeId = active.id as string;
    const item = optimisticItems.find((i) => i.id === activeId);
    const originalItem = items.find((i) => i.id === activeId);

    if (!item || !originalItem) return;

    if (item.stage !== originalItem.stage) {
      try {
        await updateItem(activeId, { stage: item.stage });
      } catch (err) {
        setOptimisticItems(items);
        toast.error(getUserFriendlyError(err));
      }
    }
  };

  if (!session?.access_token) {
    return (
      <>
        <PageHeader title="Pipeline" />
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-4">Pipeline de Oportunidades</h1>
          <p className="text-[var(--text-secondary)]">Faça login para acessar seu pipeline.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Pipeline" />
      <main className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Pipeline de Oportunidades</h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              Arraste as licitações entre os estágios para acompanhar seu progresso.
            </p>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">
            {optimisticItems.length} {optimisticItems.length === 1 ? "item" : "itens"} no pipeline
          </div>
        </div>

        {error && (
          <div className="bg-red-50/80 dark:bg-red-900/20 backdrop-blur-sm border border-red-200/50 dark:border-red-800/50 rounded-lg p-4 mb-6">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        )}

        {loading && optimisticItems.length === 0 ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-blue" />
            <span className="ml-3 text-[var(--text-secondary)]">Carregando pipeline...</span>
          </div>
        ) : !loading && optimisticItems.length === 0 ? (
          <EmptyState
            icon={
              <svg aria-hidden="true" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
              </svg>
            }
            title="Seu Pipeline de Oportunidades"
            description="Aqui voce acompanha licitacoes do inicio ao fim."
            steps={[
              'Busque licitacoes em "Buscar"',
              'Clique em "Acompanhar" numa oportunidade',
              "Arraste entre as colunas conforme avanca",
            ]}
            ctaLabel="Buscar oportunidades"
            ctaHref="/buscar"
          />
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-200px)]">
              {STAGES_ORDER.map((stage) => (
                <PipelineColumn
                  key={stage}
                  stage={stage}
                  items={getItemsByStage(stage)}
                  onRemove={removeItem}
                  onUpdateNotes={(id, notes) => updateItem(id, { notes })}
                />
              ))}
            </div>

            <DragOverlay>
              {activeItem ? <PipelineCard item={activeItem} isDragging /> : null}
            </DragOverlay>
          </DndContext>
        )}
      </main>
    </>
  );
}
