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
import { usePlan } from "../../hooks/usePlan";
import { STAGES_ORDER, STAGE_CONFIG, type PipelineItem, type PipelineStage } from "./types";
import { PipelineColumn } from "./PipelineColumn";
import { PipelineCard } from "./PipelineCard";
import { PipelineMobileTabs } from "./PipelineMobileTabs";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState } from "../../components/EmptyState";
import { ErrorStateWithRetry } from "../../components/ErrorStateWithRetry";
import { AuthLoadingScreen } from "../../components/AuthLoadingScreen";
import { useAuth } from "../components/AuthProvider";
import { useIsMobile } from "../../hooks/useIsMobile";
import { getUserFriendlyError } from "../../lib/error-messages";
import { toast } from "sonner";
import { TrialUpsellCTA } from "../../components/billing/TrialUpsellCTA";
import { useShepherdTour, type TourStep } from "../../hooks/useShepherdTour";
import { OnboardingTourButton } from "../../components/OnboardingTourButton";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useRef } from "react";

// STORY-313 AC9: Pipeline tour steps
const PIPELINE_TOUR_STEPS: TourStep[] = [
  {
    id: 'pipeline-columns',
    title: 'Kanban de oportunidades',
    text: '<span class="tour-step-counter">Passo 1 de 3</span><p>Arraste oportunidades entre etapas para acompanhar seu progresso.</p>',
    attachTo: { element: '[data-tour="kanban-columns"]', on: 'top' },
  },
  {
    id: 'pipeline-card',
    title: 'Detalhes do card',
    text: '<span class="tour-step-counter">Passo 2 de 3</span><p>Clique para ver detalhes e adicionar notas.</p>',
    attachTo: { element: '[data-tour="pipeline-card"]', on: 'right' },
    showOn: () => !!document.querySelector('[data-tour="pipeline-card"]'),
  },
  {
    id: 'pipeline-alerts',
    title: 'Alertas e prazos',
    text: '<span class="tour-step-counter">Passo 3 de 3</span><p>Fique atento aos prazos — cards com borda vermelha estao proximos do encerramento.</p>',
    attachTo: { element: '[data-tour="kanban-columns"]', on: 'bottom' },
  },
];

export default function PipelinePage() {
  const { session, loading: authLoading } = useAuth();
  const { planInfo } = usePlan();
  const { trackEvent } = useAnalytics();
  const isMobile = useIsMobile();
  const { items, loading, error, fetchItems, updateItem, removeItem } = usePipeline();

  // STORY-265 AC15: Detect trial expired for read-only mode
  const isTrialExpired = planInfo?.plan_id === "free_trial" && planInfo?.subscription_status === "expired";

  // STORY-312 AC3: Track new items added (show CTA after add)
  const [showPipelineCTA, setShowPipelineCTA] = useState(false);
  const [prevItemCount, setPrevItemCount] = useState<number | null>(null);

  useEffect(() => {
    if (prevItemCount !== null && items.length > prevItemCount) {
      setShowPipelineCTA(true);
    }
    setPrevItemCount(items.length);
  }, [items.length, prevItemCount]);
  const [activeItem, setActiveItem] = useState<PipelineItem | null>(null);
  const [optimisticItems, setOptimisticItems] = useState<PipelineItem[]>([]);
  const [initialLoadFailed, setInitialLoadFailed] = useState(false);

  useEffect(() => {
    setOptimisticItems(items);
  }, [items]);

  // STORY-313 AC9-10: Pipeline tour
  const reportTourEvent = useCallback(async (tourId: string, event: string, stepsSeen: number) => {
    try {
      const token = session?.access_token;
      await fetch('/api/onboarding?endpoint=tour-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ tour_id: tourId, event, steps_seen: stepsSeen }),
      });
    } catch { /* fire-and-forget */ }
  }, [session?.access_token]);

  const {
    isCompleted: isPipelineTourCompleted,
    startTour: startPipelineTour,
    restartTour: restartPipelineTour,
  } = useShepherdTour({
    tourId: 'pipeline',
    steps: PIPELINE_TOUR_STEPS,
    onComplete: (stepsSeen) => {
      trackEvent('onboarding_tour_completed', { tour: 'pipeline', steps_seen: stepsSeen });
      reportTourEvent('pipeline', 'completed', stepsSeen);
    },
    onSkip: (stepsSeen) => {
      trackEvent('onboarding_tour_skipped', { tour: 'pipeline', skipped_at_step: stepsSeen });
      reportTourEvent('pipeline', 'skipped', stepsSeen);
    },
  });

  // Auto-start pipeline tour on first visit (AC9/AC10)
  const pipelineTourStarted = useRef(false);
  useEffect(() => {
    if (!loading && !pipelineTourStarted.current && !isPipelineTourCompleted()) {
      pipelineTourStarted.current = true;
      const timer = setTimeout(() => {
        startPipelineTour();
        trackEvent('onboarding_tour_started', { tour: 'pipeline' });
      }, 800);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

  const wrappedFetchItems = useCallback(async () => {
    setInitialLoadFailed(false);
    await fetchItems();
  }, [fetchItems]);

  // Track initial load failure: if fetchItems finishes with an error
  // and there are no items loaded, the initial load failed.
  useEffect(() => {
    if (error && !loading && items.length === 0) {
      setInitialLoadFailed(true);
    } else if (!error || items.length > 0) {
      setInitialLoadFailed(false);
    }
  }, [error, loading, items.length]);

  useEffect(() => {
    if (session?.access_token) {
      wrappedFetchItems();
    }
  }, [session?.access_token, wrappedFetchItems]);

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
        await updateItem(activeId, { stage: item.stage, version: originalItem.version });
      } catch (err: any) {
        setOptimisticItems(items);
        // STORY-307 AC11: On 409 conflict, show specific toast and reload
        if (err?.isConflict) {
          toast.error("Item foi atualizado por outra operação. Recarregando...");
          fetchItems();
        } else {
          toast.error(getUserFriendlyError(err));
        }
      }
    }
  };

  // Determine if we are in read-only error mode (stale data visible but API errored)
  const isReadOnlyError = Boolean(error) && optimisticItems.length > 0;

  // STORY-265 AC15: Trial expired = read-only mode (no drag, no add, no delete)
  const isTrialReadOnly = isTrialExpired && optimisticItems.length > 0;

  // GTM-POLISH-001 AC1-AC3: Unified auth loading
  if (authLoading) {
    return <AuthLoadingScreen />;
  }

  if (!session?.access_token) {
    return (
      <>
        <PageHeader title="Pipeline" />
        <div className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h1 className="text-2xl font-bold mb-4">Pipeline de Oportunidades</h1>
          <p className="text-[var(--text-secondary)]">Fa\u00e7a login para acessar seu pipeline.</p>
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
              Arraste as licita\u00e7\u00f5es entre os est\u00e1gios para acompanhar seu progresso.
            </p>
          </div>
          <div className="text-sm text-[var(--text-secondary)]">
            {optimisticItems.length} {optimisticItems.length === 1 ? "item" : "itens"} no pipeline
          </div>
        </div>

        {/* STORY-312 AC3: Post-add-to-pipeline CTA for trial users */}
        {showPipelineCTA && (
          <div className="mb-4" data-tour="pipeline-alerts">
            <TrialUpsellCTA
              variant="post-pipeline"
              planId={planInfo?.plan_id}
              subscriptionStatus={planInfo?.subscription_status}
              contextData={{ pipelineLimit: 1000 }}
            />
          </div>
        )}

        {/* AC8+AC14: Error state with retry when initial load fails (no data at all) */}
        {initialLoadFailed && !loading && optimisticItems.length === 0 ? (
          <ErrorStateWithRetry
            message="N\u00e3o foi poss\u00edvel carregar seu pipeline."
            onRetry={wrappedFetchItems}
          />
        ) : loading && optimisticItems.length === 0 ? (
          /* GTM-POLISH-001 AC4: Skeleton cards in kanban columns during loading */
          <div className="flex gap-4 overflow-x-auto pb-4" data-testid="pipeline-skeleton">
            {STAGES_ORDER.map((stage) => (
              <div key={stage} className="flex-shrink-0 w-72 rounded-xl bg-[var(--surface-0)] border border-[var(--border)]">
                <div className="p-3 border-b border-[var(--border)]">
                  <div className="flex items-center gap-2">
                    <div className="h-5 w-5 bg-[var(--surface-1)] rounded animate-pulse" />
                    <div className="h-4 w-24 bg-[var(--surface-1)] rounded animate-pulse" />
                  </div>
                </div>
                <div className="p-2 space-y-2">
                  {[1, 2].map((i) => (
                    <div key={i} className="h-24 bg-[var(--surface-1)] rounded-lg animate-pulse" style={{ animationDelay: `${i * 150}ms` }} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : !loading && optimisticItems.length === 0 && !error ? (
          /* GTM-POLISH-001 AC10: Pipeline empty state with visual drag hint */
          <EmptyState
            icon={
              <svg aria-hidden="true" className="w-8 h-8 text-[var(--brand-blue)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
              </svg>
            }
            title="Seu Pipeline de Oportunidades"
            description="Arraste licita\u00e7\u00f5es para c\u00e1 e acompanhe do in\u00edcio ao fim."
            steps={[
              'Busque licita\u00e7\u00f5es em "Buscar"',
              'Clique em "Acompanhar" numa oportunidade',
              "Arraste entre as colunas conforme avan\u00e7a",
            ]}
            ctaLabel="Buscar oportunidades"
            ctaHref="/buscar"
          />
        ) : isTrialReadOnly ? (
          /* STORY-265 AC15: Trial expired read-only mode */
          <>
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800 rounded-card flex items-center justify-between" role="alert">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
                <p className="text-sm text-amber-800 dark:text-amber-200">
                  Seu trial expirou. O pipeline est\u00e1 em modo leitura. Ative um plano para continuar gerenciando suas oportunidades.
                </p>
              </div>
              <a
                href="/planos"
                className="text-sm font-medium text-[var(--brand-blue)] hover:underline whitespace-nowrap ml-3"
              >
                Ver planos
              </a>
            </div>
            <DndContext>
              <div className="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-200px)]">
                {STAGES_ORDER.map((stage) => (
                  <PipelineColumn
                    key={stage}
                    stage={stage}
                    items={getItemsByStage(stage)}
                    onRemove={() => {}}
                    onUpdateNotes={() => {}}
                  />
                ))}
              </div>
            </DndContext>
          </>
        ) : isReadOnlyError ? (
          /* AC9: Read-only mode when error occurs but stale data exists.
             DndContext with no sensors disables drag-and-drop while still
             providing context for useDroppable inside PipelineColumn. */
          <>
            <div className="mb-4 p-3 bg-[var(--error-subtle)] border border-[var(--error)]/20 rounded-card flex items-center justify-between" role="alert">
              <p className="text-sm text-[var(--error)]">
                Pipeline em modo leitura. Arraste desabilitado temporariamente.
              </p>
              <button
                onClick={wrappedFetchItems}
                className="text-sm font-medium text-[var(--brand-blue)] hover:underline"
              >
                Tentar novamente
              </button>
            </div>
            <DndContext>
              <div className="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-200px)]">
                {STAGES_ORDER.map((stage) => (
                  <PipelineColumn
                    key={stage}
                    stage={stage}
                    items={getItemsByStage(stage)}
                    onRemove={() => {}}
                    onUpdateNotes={() => {}}
                  />
                ))}
              </div>
            </DndContext>
          </>
        ) : (
          /* GTM-POLISH-002 AC5-AC8: Mobile tabs, Desktop kanban */
          isMobile ? (
            <PipelineMobileTabs
              items={optimisticItems}
              onUpdateItem={updateItem}
              onRemoveItem={removeItem}
            />
          ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-200px)]" data-tour="kanban-columns">
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
          )
        )}
      </main>

      {/* STORY-313 AC15: Floating guide button */}
      <OnboardingTourButton
        availableTours={{
          pipeline: restartPipelineTour,
        }}
      />
    </>
  );
}
