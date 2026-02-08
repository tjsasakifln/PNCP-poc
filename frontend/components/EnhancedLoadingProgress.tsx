/**
 * EnhancedLoadingProgress Component
 * 5-stage loading progress indicator with:
 * - SSE real-time progress (Phase 2) with fallback to time-based simulation
 * - Asymptotic progress cap at 95% to avoid false "100%" display
 * - Honest overtime messaging when search takes longer than expected
 * - Cancel button for user control
 *
 * Stages:
 * 1. Connecting to PNCP API (10%)
 * 2. Fetching data from X states (40%)
 * 3. Filtering results (70%)
 * 4. Generating AI summary (90%)
 * 5. Preparing Excel report (100%)
 */

import React, { useEffect, useState, useRef } from 'react';
import type { SearchProgressEvent } from '../hooks/useSearchProgress';

export interface EnhancedLoadingProgressProps {
  currentStep: number;
  estimatedTime: number;
  stateCount: number;
  onStageChange?: (stage: number) => void;
  /** Issue #109: Show "X of Y states processed" for better feedback */
  statesProcessed?: number;
  /** Cancel button callback */
  onCancel?: () => void;
  /** SSE real-time progress event */
  sseEvent?: SearchProgressEvent | null;
  /** Whether to use real SSE data vs simulated progress */
  useRealProgress?: boolean;
}

interface Stage {
  id: number;
  label: string;
  progressTarget: number;
  description: string;
}

const STAGES: Stage[] = [
  {
    id: 1,
    label: 'Conectando ao PNCP',
    progressTarget: 10,
    description: 'Estabelecendo conexão com o Portal Nacional de Contratações Públicas',
  },
  {
    id: 2,
    label: 'Buscando dados',
    progressTarget: 40,
    description: 'Coletando licitações publicadas nos estados selecionados',
  },
  {
    id: 3,
    label: 'Filtrando resultados',
    progressTarget: 70,
    description: 'Aplicando filtros de setor, valor e relevância',
  },
  {
    id: 4,
    label: 'Gerando resumo IA',
    progressTarget: 90,
    description: 'Criando análise executiva com GPT-4',
  },
  {
    id: 5,
    label: 'Preparando Excel',
    progressTarget: 100,
    description: 'Formatando planilha para download',
  },
];

// Map SSE stage names to stage IDs
const SSE_STAGE_MAP: Record<string, number> = {
  connecting: 1,
  fetching: 2,
  filtering: 3,
  llm: 4,
  excel: 5,
  complete: 5,
};

/** Graduated honest overtime messages */
function getOvertimeMessage(overBySeconds: number): string {
  if (overBySeconds < 15) return 'Quase pronto, finalizando...';
  if (overBySeconds < 45) return 'O PNCP está mais lento que o normal. Aguarde...';
  if (overBySeconds < 90) return 'Ainda processando. Buscas com muitos estados demoram mais.';
  return 'A busca está demorando mais que o esperado. Você pode cancelar e tentar com menos estados.';
}

export function EnhancedLoadingProgress({
  currentStep,
  estimatedTime,
  stateCount,
  onStageChange,
  statesProcessed = 0,
  onCancel,
  sseEvent,
  useRealProgress = false,
}: EnhancedLoadingProgressProps) {
  const [simulatedProgress, setSimulatedProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(1);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Track last SSE progress for smooth fallback
  const lastSseProgressRef = useRef(0);

  // Refs to avoid resetting interval on stage/callback changes
  const currentStageRef = useRef(currentStage);
  const onStageChangeRef = useRef(onStageChange);

  useEffect(() => {
    currentStageRef.current = currentStage;
  }, [currentStage]);

  useEffect(() => {
    onStageChangeRef.current = onStageChange;
  }, [onStageChange]);

  // Track SSE progress in ref for fallback smoothing
  useEffect(() => {
    if (useRealProgress && sseEvent && sseEvent.progress >= 0) {
      lastSseProgressRef.current = sseEvent.progress;
    }
  }, [useRealProgress, sseEvent]);

  // Calculate simulated progress based on time elapsed
  useEffect(() => {
    const startTime = Date.now();
    const safeEstimatedTime = Math.max(2, estimatedTime);

    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setElapsedTime(Math.floor(elapsed));

      // Asymptotic progress: approaches 95% but never reaches 100% until actually done
      const rawProgress = (elapsed / safeEstimatedTime) * 100;
      const asymptotic = rawProgress <= 90
        ? rawProgress
        : 90 + (5 * (1 - Math.exp(-(rawProgress - 90) / 30)));
      setSimulatedProgress(Math.min(95, asymptotic));
    }, 500);

    return () => clearInterval(interval);
  }, [estimatedTime]);

  // Determine effective progress, stage, and message from SSE or simulation
  const effectiveProgress = useRealProgress && sseEvent && sseEvent.progress >= 0
    ? sseEvent.progress
    : Math.max(simulatedProgress, lastSseProgressRef.current); // Don't jump backwards on fallback

  // Determine stage from SSE or from simulated progress
  let effectiveStageId: number;
  if (useRealProgress && sseEvent && SSE_STAGE_MAP[sseEvent.stage]) {
    effectiveStageId = SSE_STAGE_MAP[sseEvent.stage];
  } else {
    // Derive from simulated progress
    effectiveStageId = 1;
    for (const stage of STAGES) {
      if (effectiveProgress >= stage.progressTarget) {
        effectiveStageId = stage.id;
      } else {
        break;
      }
    }
  }

  // Update stage state and fire callback
  useEffect(() => {
    if (effectiveStageId !== currentStageRef.current) {
      setCurrentStage(effectiveStageId);
      currentStageRef.current = effectiveStageId;
      onStageChangeRef.current?.(effectiveStageId);
    }
  }, [effectiveStageId]);

  const activeStage = STAGES.find(s => s.id === currentStage) || STAGES[0];

  // Use SSE message when available, otherwise stage description
  const statusDescription = useRealProgress && sseEvent
    ? sseEvent.message
    : activeStage.description;

  // States processed: from SSE detail or from prop
  const effectiveStatesProcessed = useRealProgress && sseEvent?.detail?.uf_index
    ? sseEvent.detail.uf_index
    : statesProcessed;

  const progressPercentage = Math.min(100, Math.max(0, effectiveProgress));
  const isOvertime = elapsedTime > estimatedTime;
  const overtimeSeconds = elapsedTime - estimatedTime;

  return (
    <div
      className="mt-6 sm:mt-8 p-4 sm:p-6 bg-surface-0 border border-strong rounded-card animate-fade-in-up"
      role="status"
      aria-live="polite"
      aria-label={`Buscando licitações, ${Math.floor(progressPercentage)}% completo`}
    >
      {/* Header with spinner */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <svg
            className="animate-spin h-6 w-6 text-brand-blue"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              fill="none"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <div>
            <p className="text-base sm:text-lg font-semibold text-ink">
              {activeStage.label}
            </p>
            <p className="text-xs sm:text-sm text-ink-secondary mt-0.5">
              {statusDescription}
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold font-data tabular-nums text-brand-blue">
            {Math.floor(progressPercentage)}%
          </p>
          <p className="text-xs text-ink-muted">
            {elapsedTime >= 300
              ? `${Math.floor(elapsedTime / 60)}m ${elapsedTime % 60}s`
              : `${elapsedTime}s`}
            {!isOvertime && (
              <>
                {' / '}
                {estimatedTime >= 300
                  ? `${Math.floor(estimatedTime / 60)}m ${estimatedTime % 60}s`
                  : `~${estimatedTime}s`}
              </>
            )}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="w-full bg-surface-2 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-brand-blue to-brand-blue-hover h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
            role="progressbar"
            aria-valuenow={progressPercentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {/* Stage indicators */}
      <div className="flex justify-between items-start gap-2 mb-4">
        {STAGES.map((stage) => {
          const isCompleted = currentStage > stage.id;
          const isActive = currentStage === stage.id;
          const isPending = currentStage < stage.id;

          return (
            <div
              key={stage.id}
              className="flex flex-col items-center flex-1"
            >
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300
                  ${isCompleted ? 'bg-brand-blue text-white scale-100' : ''}
                  ${isActive ? 'bg-brand-blue text-white scale-110 ring-2 ring-brand-blue ring-offset-2' : ''}
                  ${isPending ? 'bg-surface-2 text-ink-muted scale-90' : ''}
                `}
                aria-label={`Stage ${stage.id}: ${isCompleted ? 'Completed' : isActive ? 'In progress' : 'Pending'}`}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" role="img" aria-label="Completed">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  stage.id
                )}
              </div>
              <p
                className={`
                  text-[10px] sm:text-xs text-center mt-1.5 transition-colors duration-300
                  ${isActive ? 'text-brand-blue font-semibold' : 'text-ink-muted'}
                `}
              >
                {stage.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Overtime warning message */}
      {isOvertime && (
        <div className="mb-3 p-3 bg-warning-subtle border border-warning/20 rounded-lg text-sm text-warning-dark">
          {getOvertimeMessage(overtimeSeconds)}
        </div>
      )}

      {/* Meta information */}
      <div className="flex justify-between items-center text-xs text-ink-secondary pt-3 border-t border-strong">
        <span>
          {effectiveStatesProcessed > 0 ? (
            <>
              <span className="font-semibold text-brand-blue">{effectiveStatesProcessed}</span>
              {' de '}
              <span className="font-semibold">{stateCount}</span>
              {` ${stateCount === 1 ? 'estado processado' : 'estados processados'}`}
            </>
          ) : (
            `Processando ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}`
          )}
        </span>

        <div className="flex items-center gap-3">
          <span>
            {!isOvertime
              ? estimatedTime - elapsedTime >= 60
                ? `~${Math.floor((estimatedTime - elapsedTime) / 60)}m restantes`
                : `~${Math.max(0, estimatedTime - elapsedTime)}s restantes`
              : ''}
          </span>

          {/* Cancel button - shown after 10s */}
          {onCancel && elapsedTime > 10 && (
            <button
              onClick={onCancel}
              className="text-xs text-ink-muted hover:text-error transition-colors underline underline-offset-2"
              type="button"
            >
              Cancelar
            </button>
          )}
        </div>
      </div>

      {/* SSE indicator (subtle) */}
      {useRealProgress && sseEvent && (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-ink-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          Progresso em tempo real
        </div>
      )}
    </div>
  );
}
