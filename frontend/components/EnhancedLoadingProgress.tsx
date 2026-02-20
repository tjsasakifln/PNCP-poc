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
  /** GTM-FIX-033 AC3: SSE disconnected — show informative message */
  sseDisconnected?: boolean;
  /** GTM-FIX-035 AC3: Whether all UFs have completed fetching (from useUfProgress) */
  ufAllComplete?: boolean;
  /** A-02 AC9: Search completed with degraded data (cache/partial) */
  isDegraded?: boolean;
  /** A-02 AC9: Human-readable freshness message from SSE degraded event */
  degradedMessage?: string;
  /** CRIT-005 AC22: Show timeout overlay before switching to error */
  showTimeoutOverlay?: boolean;
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
    label: 'Consultando fontes oficiais',
    progressTarget: 10,
    description: 'Consultando fontes oficiais de contratacoes publicas',
  },
  {
    id: 2,
    label: 'Buscando dados',
    progressTarget: 10,
    description: 'Coletando licitacoes dos estados selecionados',
  },
  {
    id: 3,
    label: 'Filtrando resultados',
    progressTarget: 70,
    description: 'Aplicando filtros de setor, valor e relevancia',
  },
  {
    id: 4,
    label: 'Avaliando oportunidades',
    progressTarget: 90,
    description: 'Gerando avaliacao estrategica por IA',
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

/** CRIT-006 AC20-21: Graduated honest overtime messages with SSE progress awareness */
function getOvertimeMessage(overBySeconds: number, stateCount: number, estimatedTime: number, elapsedTime: number, sseProgress?: number): string {
  // CRIT-006 AC20: Messages tied to REAL progress, not just time
  if (sseProgress !== undefined && sseProgress >= 0) {
    if (sseProgress > 80) return 'Quase pronto, finalizando...';
    if (sseProgress >= 50) return 'Processando resultados...';
    // CRIT-006 AC21: If progress stale (overtime but < 50%), different message
    return 'Aguardando resposta das fontes...';
  }

  // Fallback for no SSE
  if (elapsedTime > estimatedTime * 2) {
    return 'Esta busca esta demorando mais que o normal. Pode ficar nesta pagina — os resultados serao exibidos automaticamente.';
  }
  if (overBySeconds < 15) return 'Quase pronto, finalizando...';
  if (overBySeconds < 45) return 'Estamos trabalhando nisso, so mais um instante!';
  if (overBySeconds < 90) {
    return stateCount > 10
      ? 'Ainda processando. Buscas com muitos estados demoram mais.'
      : 'Processando, aguarde mais um momento.';
  }
  return 'Esta busca esta demorando mais que o normal. Pode ficar nesta pagina — os resultados serao exibidos automaticamente.';
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
  sseDisconnected = false,
  ufAllComplete = false,
  isDegraded = false,
  degradedMessage,
  showTimeoutOverlay = false,
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

  // GTM-FIX-035 AC3: Compute UF-aware progress that syncs states processed with percentage.
  // Fetch stage (10%-70%) is proportional to UF completion. Post-fetch stages use SSE or simulation.
  const ufBasedProgress = (() => {
    if (stateCount <= 0) return simulatedProgress;
    const effectiveStatesProcessed = useRealProgress && sseEvent?.detail?.uf_index
      ? sseEvent.detail.uf_index
      : statesProcessed;
    if (effectiveStatesProcessed <= 0 && !ufAllComplete) return Math.min(simulatedProgress, 10); // Cap at connecting stage
    const ufRatio = ufAllComplete ? 1 : Math.min(effectiveStatesProcessed / stateCount, 1);
    // Map UF ratio to 10%-70% range (fetch stage)
    return 10 + (ufRatio * 60);
  })();

  // Determine effective progress, stage, and message from SSE or simulation
  let effectiveProgress: number;
  if (useRealProgress && sseEvent && sseEvent.progress >= 0) {
    // SSE has real progress — but reconcile with UF data if in fetch stage
    if (sseEvent.stage === 'fetching' || (!sseEvent.stage && sseEvent.progress < 70)) {
      // Use the higher of SSE progress and UF-based progress to avoid contradictions
      effectiveProgress = Math.max(sseEvent.progress, ufBasedProgress);
    } else {
      effectiveProgress = sseEvent.progress;
    }
  } else {
    // No SSE — use UF-aware progress (better than pure time simulation)
    effectiveProgress = Math.max(ufBasedProgress, lastSseProgressRef.current);
  }

  // Determine stage from SSE or from effective progress
  let effectiveStageId: number;
  if (useRealProgress && sseEvent && SSE_STAGE_MAP[sseEvent.stage]) {
    effectiveStageId = SSE_STAGE_MAP[sseEvent.stage];
  } else {
    // Derive from effective progress
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

  // GTM-FIX-035 AC4: Contextual status description with source count and time estimate
  const statusDescription = (() => {
    if (useRealProgress && sseEvent) return sseEvent.message;
    if (currentStage === 1) {
      return `Consultando fontes oficiais. Resultados em aproximadamente ${estimatedTime}s.`;
    }
    if (currentStage === 2 && stateCount > 0) {
      const remaining = Math.max(0, estimatedTime - elapsedTime);
      return remaining > 0
        ? `Coletando dados de ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}. ~${remaining}s restantes.`
        : `Coletando dados de ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}.`;
    }
    return activeStage.description;
  })();

  // States processed: from SSE detail or from prop
  const effectiveStatesProcessed = useRealProgress && sseEvent?.detail?.uf_index
    ? sseEvent.detail.uf_index
    : statesProcessed;

  const progressPercentage = Math.min(100, Math.max(0, effectiveProgress));
  const isOvertime = elapsedTime > estimatedTime;
  const overtimeSeconds = elapsedTime - estimatedTime;

  // CRIT-006 AC20: Get current SSE progress for overtime message
  const currentSseProgress = useRealProgress && sseEvent && sseEvent.progress >= 0
    ? sseEvent.progress
    : undefined;

  // A-02 AC9: Amber color scheme for degraded state
  const progressBarColor = isDegraded
    ? 'bg-gradient-to-r from-amber-500 to-amber-600'
    : 'bg-gradient-to-r from-brand-blue to-brand-blue-hover';
  const accentTextColor = isDegraded ? 'text-amber-600 dark:text-amber-400' : 'text-brand-blue';

  return (
    <div
      className={`relative mt-6 sm:mt-8 p-4 sm:p-6 rounded-card animate-fade-in-up ${
        isDegraded
          ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40'
          : 'bg-surface-0 border border-strong'
      }`}
      role="status"
      aria-live="polite"
      aria-label={isDegraded
        ? `Resultados disponiveis com ressalvas`
        : `Buscando licitacoes, ${Math.floor(progressPercentage)}% completo`}
      data-testid={isDegraded ? 'degraded-progress' : 'loading-progress'}
    >
      {/* CRIT-005 AC22: Timeout overlay */}
      {showTimeoutOverlay && (
        <div className="absolute inset-0 bg-amber-50/80 dark:bg-amber-900/40 rounded-card flex items-center justify-center z-10 animate-fade-in">
          <p className="text-amber-700 dark:text-amber-300 font-medium text-sm">
            Busca expirou — preparando resultados...
          </p>
        </div>
      )}

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
          <p className={`text-2xl font-bold font-data tabular-nums ${accentTextColor}`}>
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
            className={`${progressBarColor} h-3 rounded-full transition-all duration-500 ease-out`}
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
                  ${isCompleted ? (isDegraded ? 'bg-amber-500 text-white scale-100' : 'bg-brand-blue text-white scale-100') : ''}
                  ${isActive ? (isDegraded ? 'bg-amber-500 text-white scale-110 ring-2 ring-amber-500 ring-offset-2' : 'bg-brand-blue text-white scale-110 ring-2 ring-brand-blue ring-offset-2') : ''}
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
                  ${isActive ? (isDegraded ? 'text-amber-600 dark:text-amber-400 font-semibold' : 'text-brand-blue font-semibold') : 'text-ink-muted'}
                `}
              >
                {stage.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* A-02 AC9: Degraded state amber message */}
      {isDegraded && (
        <div
          className="mb-3 p-3 bg-amber-100 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700/50 rounded-lg text-sm text-amber-800 dark:text-amber-200 flex items-center gap-2"
          data-testid="degraded-message"
        >
          <svg className="w-4 h-4 flex-shrink-0 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {degradedMessage || 'Resultados disponiveis com ressalvas'}
        </div>
      )}

      {/* Overtime warning message — CRIT-006 AC20-21: uses SSE progress */}
      {isOvertime && !isDegraded && (
        <div className="mb-3 p-3 bg-warning-subtle border border-warning/20 rounded-lg text-sm text-warning-dark">
          {getOvertimeMessage(overtimeSeconds, stateCount, estimatedTime, elapsedTime, currentSseProgress)}
        </div>
      )}

      {/* Meta information */}
      <div className="flex justify-between items-center text-xs text-ink-secondary pt-3 border-t border-strong">
        <span>
          {effectiveStatesProcessed > 0 ? (
            stateCount >= 27 ? (
              <>Buscando em todo o Brasil...</>
            ) : (
              <>
                <span className="font-semibold text-brand-blue">{effectiveStatesProcessed}</span>
                {' de '}
                <span className="font-semibold">{stateCount}</span>
                {` ${stateCount === 1 ? 'estado processado' : 'estados processados'}`}
              </>
            )
          ) : (
            stateCount >= 27 ? 'Buscando em todo o Brasil...' : `Processando ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}`
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

          {/* CRIT-006 AC15: Cancel button visible from start (no delay) */}
          {onCancel && (
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

      {/* CRIT-006 AC13-14: SSE disconnect message — informative, not misleading */}
      {sseDisconnected && (
        <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/40 rounded-lg text-sm text-blue-800 dark:text-blue-200 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin flex-shrink-0" />
          O progresso em tempo real foi interrompido. A busca continua no servidor e os resultados serao exibidos quando prontos.
        </div>
      )}

      {/* SSE indicator (subtle) */}
      {useRealProgress && sseEvent && !sseDisconnected && (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-ink-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          Progresso em tempo real
        </div>
      )}
    </div>
  );
}
