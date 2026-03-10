/**
 * EnhancedLoadingProgress Component
 * Educational carousel loading with:
 * - SSE real-time progress (primary) or polling progress (fallback)
 * - B2G educational carousel replacing technical stage indicators
 * - Honest overtime messaging when search takes longer than expected
 * - Cancel button for user control
 *
 * UX-411: Replaced 5-stage technical indicators and countdown with
 * educational B2G carousel that reduces perceived wait time.
 * DEBT-111: Removed time-based simulation path — only SSE/polling progress used.
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import type { SearchProgressEvent } from '../../../hooks/useSearchSSE';

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
  /** @deprecated DEBT-111: Simulation removed. Prop kept for API compatibility but ignored. */
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
  /** CRIT-052 AC2: Show reconnecting indicator during SSE reconnection */
  isReconnecting?: boolean;
}

// Internal stages for progress logic (not displayed to user)
interface Stage {
  id: number;
  progressTarget: number;
}

const STAGES: Stage[] = [
  { id: 1, progressTarget: 10 },
  { id: 2, progressTarget: 10 },
  { id: 3, progressTarget: 70 },
  { id: 4, progressTarget: 90 },
  { id: 5, progressTarget: 100 },
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

/** UX-411 AC5: Educational B2G carousel tips */
const B2G_TIPS = [
  'O Brasil homologou mais de R$ 1 trilhão em contratações públicas em 2025. Sua empresa pode capturar parte desse mercado.',
  'Empate ficto (5%): No pregão eletrônico, se sua proposta estiver até 5% acima e você for ME/EPP, você pode cobrir o lance vencedor.',
  'Licitações exclusivas até R$ 80 mil podem ser reservadas para micro e pequenas empresas (LC 123/2006).',
  'Desde a Lei 14.133/2021, o PNCP é o canal oficial obrigatório para publicação de editais de todos os entes federativos.',
  'Inversão de fases: Na nova lei, propostas são julgadas ANTES da habilitação — agilizando o processo decisivamente.',
  'Pregão eletrônico é a modalidade mais usada no Brasil, representando mais de 60% das contratações públicas.',
  'Você pode participar de licitações em qualquer estado do Brasil, independente de onde sua empresa está sediada.',
  'Contratos públicos costumam ter pagamento garantido por dotação orçamentária — menor risco de inadimplência que o setor privado.',
  'A margem de preferência para produtos nacionais pode chegar a 25% em determinados setores estratégicos.',
  'Consórcio de empresas: Pequenas empresas podem se unir em consórcio para participar de licitações maiores.',
  'O prazo médio para pagamento em contratos públicos é de 30 dias após a entrega — preveja isso no fluxo de caixa.',
  'Atestados de capacidade técnica são o documento mais importante na habilitação. Mantenha-os sempre atualizados.',
  'Inexigibilidade de licitação: Se sua empresa oferece serviço exclusivo, pode contratar diretamente com o órgão público.',
  'A pesquisa de preços no PNCP permite consultar valores históricos para formar preço competitivo nas suas propostas.',
  'Certidões negativas (FGTS, INSS, Fazenda) são exigidas em praticamente todas as licitações. Mantenha-as em dia.',
];

const CAROUSEL_INTERVAL_MS = 6000;

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
    return 'Esta busca está demorando mais que o normal. Pode ficar nesta página — os resultados serão exibidos automaticamente.';
  }
  if (overBySeconds < 15) return 'Quase pronto, finalizando...';
  if (overBySeconds < 45) return 'Estamos trabalhando nisso, só mais um instante!';
  if (overBySeconds < 90) {
    return stateCount > 10
      ? 'Ainda processando. Buscas com muitos estados demoram mais.'
      : 'Processando, aguarde mais um momento.';
  }
  return 'Esta busca está demorando mais que o normal. Pode ficar nesta página — os resultados serão exibidos automaticamente.';
}

export function EnhancedLoadingProgress({
  currentStep,
  estimatedTime,
  stateCount,
  onStageChange,
  statesProcessed = 0,
  onCancel,
  sseEvent,
  // useRealProgress is deprecated (DEBT-111) — simulation removed, prop ignored
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  useRealProgress: _useRealProgress,
  sseDisconnected = false,
  ufAllComplete = false,
  isDegraded = false,
  degradedMessage,
  showTimeoutOverlay = false,
  isReconnecting = false,
}: EnhancedLoadingProgressProps) {
  const [currentStage, setCurrentStage] = useState(1);
  const [elapsedTime, setElapsedTime] = useState(0);

  // UX-411: Carousel state
  const [currentTipIndex, setCurrentTipIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const carouselIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Refs to avoid resetting interval on stage/callback changes
  const currentStageRef = useRef(currentStage);
  const onStageChangeRef = useRef(onStageChange);

  useEffect(() => {
    currentStageRef.current = currentStage;
  }, [currentStage]);

  useEffect(() => {
    onStageChangeRef.current = onStageChange;
  }, [onStageChange]);

  // Track elapsed time for overtime messaging (independent of progress source)
  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      setElapsedTime(Math.floor(elapsed));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // UX-411 AC5: Carousel auto-rotation with hover pause (AC11)
  const advanceTip = useCallback(() => {
    setIsFading(true);
    // After fade-out, switch tip and fade-in
    setTimeout(() => {
      setCurrentTipIndex(prev => (prev + 1) % B2G_TIPS.length);
      setIsFading(false);
    }, 300);
  }, []);

  useEffect(() => {
    if (isHovered) {
      if (carouselIntervalRef.current) {
        clearInterval(carouselIntervalRef.current);
        carouselIntervalRef.current = null;
      }
      return;
    }

    carouselIntervalRef.current = setInterval(advanceTip, CAROUSEL_INTERVAL_MS);

    return () => {
      if (carouselIntervalRef.current) {
        clearInterval(carouselIntervalRef.current);
        carouselIntervalRef.current = null;
      }
    };
  }, [isHovered, advanceTip]);

  // GTM-FIX-035 AC3: Compute UF-aware progress from real SSE/polling data only
  // STORY-329 AC6: Fetch stage caps at 60%
  // DEBT-111: No simulation fallback — progress is 0 until SSE/polling provides data.
  const ufBasedProgress = (() => {
    if (stateCount <= 0) return 0;
    const sseUfIndex = sseEvent?.detail?.uf_index;
    const effectiveStatesProcessed = (typeof sseUfIndex === 'number' && sseUfIndex > 0)
      ? sseUfIndex
      : statesProcessed;
    if (effectiveStatesProcessed <= 0 && !ufAllComplete) return 0;
    const ufRatio = ufAllComplete ? 1 : Math.min(effectiveStatesProcessed / stateCount, 1);
    return 10 + (ufRatio * 50);
  })();

  // Determine effective progress from SSE or polling data only
  let effectiveProgress: number;
  if (sseEvent && sseEvent.progress >= 0) {
    if (sseEvent.stage === 'fetching' || (!sseEvent.stage && sseEvent.progress < 60)) {
      effectiveProgress = Math.max(sseEvent.progress, ufBasedProgress);
    } else {
      effectiveProgress = sseEvent.progress;
    }
  } else {
    effectiveProgress = ufBasedProgress;
  }

  // Determine stage from SSE or from effective progress (internal logic only)
  let effectiveStageId: number;
  if (sseEvent && SSE_STAGE_MAP[sseEvent.stage]) {
    effectiveStageId = SSE_STAGE_MAP[sseEvent.stage];
  } else {
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

  // States processed display
  const sseUfIndexForDisplay = sseEvent?.detail?.uf_index;
  const effectiveStatesProcessed = (typeof sseUfIndexForDisplay === 'number' && sseUfIndexForDisplay > 0)
    ? sseUfIndexForDisplay
    : statesProcessed;

  const progressPercentage = Math.min(100, Math.max(0, effectiveProgress));
  const isOvertime = elapsedTime > estimatedTime;
  const overtimeSeconds = elapsedTime - estimatedTime;

  // CRIT-006 AC20: Get current SSE progress for overtime message
  const currentSseProgress = sseEvent && sseEvent.progress >= 0
    ? sseEvent.progress
    : undefined;

  // A-02 AC9: Amber color scheme for degraded state
  const progressBarColor = isDegraded
    ? 'bg-gradient-to-r from-amber-500 to-amber-600'
    : 'bg-gradient-to-r from-brand-blue to-brand-blue-hover';

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
        ? 'Resultados disponíveis com ressalvas'
        : 'Analisando oportunidades'}
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

      {/* AC4: Header with spinner and "Analisando oportunidades..." */}
      <div className="flex items-center gap-3 mb-4">
        <svg
          className={`animate-spin h-6 w-6 ${isDegraded ? 'text-amber-500' : 'text-brand-blue'}`}
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
        <p className="text-base sm:text-lg font-semibold text-ink">
          Analisando oportunidades...
        </p>
      </div>

      {/* AC3: Progress bar — animated, no percentage */}
      <div className="mb-5">
        <div className="w-full bg-surface-2 rounded-full h-2.5 overflow-hidden">
          <div
            className={`${progressBarColor} h-2.5 rounded-full transition-all duration-700 ease-out`}
            style={{ width: `${progressPercentage}%` }}
            role="progressbar"
            aria-valuenow={progressPercentage}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {/* AC5 + AC10 + AC11: Educational B2G carousel */}
      <div
        className="mb-4 p-4 bg-surface-1 dark:bg-surface-2 rounded-lg min-h-[80px] flex flex-col justify-between"
        data-testid="b2g-carousel"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="flex items-start gap-3">
          <span className="text-lg flex-shrink-0 mt-0.5" aria-hidden="true">💡</span>
          <p
            className={`text-sm text-ink-secondary leading-relaxed transition-opacity duration-300 ${
              isFading ? 'opacity-0' : 'opacity-100'
            }`}
            data-testid="carousel-tip"
          >
            {B2G_TIPS[currentTipIndex]}
          </p>
        </div>

        {/* AC10: Dot indicators */}
        <div className="flex justify-center gap-1.5 mt-3" data-testid="carousel-dots">
          {B2G_TIPS.map((_, index) => (
            <button
              key={index}
              type="button"
              className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                index === currentTipIndex
                  ? (isDegraded ? 'bg-amber-500 w-3' : 'bg-brand-blue w-3')
                  : 'bg-ink-muted/30'
              }`}
              onClick={() => {
                setIsFading(true);
                setTimeout(() => {
                  setCurrentTipIndex(index);
                  setIsFading(false);
                }, 300);
              }}
              aria-label={`Dica ${index + 1} de ${B2G_TIPS.length}`}
            />
          ))}
        </div>
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
          {degradedMessage || 'Resultados disponíveis com ressalvas'}
        </div>
      )}

      {/* STORY-329 AC4: Long-running filter message */}
      {sseEvent?.detail?.is_long_running && !isOvertime && !isDegraded && (
        <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700/40 rounded-lg text-sm text-blue-800 dark:text-blue-200" data-testid="long-running-message">
          Volume grande, pode levar até 2 min
        </div>
      )}

      {/* AC7: Overtime warning message — CRIT-006 AC20-21 */}
      {isOvertime && !isDegraded && (
        <div className="mb-3 p-3 bg-warning-subtle border border-warning/20 rounded-lg text-sm text-warning-dark" data-testid="overtime-message">
          {getOvertimeMessage(overtimeSeconds, stateCount, estimatedTime, elapsedTime, currentSseProgress)}
        </div>
      )}

      {/* AC6: Meta information — states processed + cancel */}
      <div className="flex justify-between items-center text-xs text-ink-secondary pt-3 border-t border-strong">
        <span>
          {effectiveStatesProcessed > 0 ? (
            stateCount >= 27 ? (
              <>Analisando em todo o Brasil...</>
            ) : (
              <>
                <span className="font-semibold text-brand-blue">{effectiveStatesProcessed}</span>
                {' de '}
                <span className="font-semibold">{stateCount}</span>
                {` ${stateCount === 1 ? 'estado processado' : 'estados processados'}`}
              </>
            )
          ) : (
            stateCount >= 27 ? 'Analisando em todo o Brasil...' : `Processando ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}`
          )}
        </span>

        {/* AC8: Cancel button */}
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

      {/* STORY-359/CRIT-052: SSE status indicator */}
      {isReconnecting ? (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-amber-600 dark:text-amber-400" data-testid="sse-reconnecting-indicator">
          <svg className="w-3.5 h-3.5 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Reconectando...</span>
        </div>
      ) : sseDisconnected ? (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-ink-muted" data-testid="sse-fallback-indicator">
          <svg className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span title="A conexão em tempo real não está disponível. O progresso exibido é uma estimativa baseada no tempo. A busca continua no servidor.">
            Progresso estimado (conexão em tempo real indisponível)
          </span>
        </div>
      ) : sseEvent ? (
        <div className="mt-2 flex items-center gap-1.5 text-[10px] text-ink-muted" data-testid="sse-realtime-indicator">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          Progresso em tempo real
        </div>
      ) : null}
    </div>
  );
}
