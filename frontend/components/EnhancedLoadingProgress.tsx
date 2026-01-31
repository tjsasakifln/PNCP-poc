/**
 * EnhancedLoadingProgress Component - Feature #2
 * 5-stage loading progress indicator with performance feedback
 * Phase 3 - Day 8 Implementation
 *
 * Stages:
 * 1. Connecting to PNCP API (10%)
 * 2. Fetching data from X states (40%)
 * 3. Filtering results (70%)
 * 4. Generating AI summary (90%)
 * 5. Preparing Excel report (100%)
 */

import React, { useEffect, useState } from 'react';

export interface EnhancedLoadingProgressProps {
  currentStep: number;
  estimatedTime: number;
  stateCount: number;
  onStageChange?: (stage: number) => void;
  /** Issue #109: Show "X of Y states processed" for better feedback */
  statesProcessed?: number;
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

export function EnhancedLoadingProgress({
  currentStep,
  estimatedTime,
  stateCount,
  onStageChange,
  statesProcessed = 0,
}: EnhancedLoadingProgressProps) {
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState(1);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Calculate progress based on time elapsed
  useEffect(() => {
    const startTime = Date.now();

    // Bug fix P2-1: Prevent flicker for very short time (<1s) by using minimum 2s
    const safeEstimatedTime = Math.max(2, estimatedTime);

    const interval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000; // seconds
      setElapsedTime(Math.floor(elapsed));

      // Calculate progress: 0-100% based on safeEstimatedTime
      const calculatedProgress = Math.min(100, (elapsed / safeEstimatedTime) * 100);
      setProgress(calculatedProgress);

      // Determine current stage based on progress
      let newStage = 1;
      for (const stage of STAGES) {
        if (calculatedProgress >= stage.progressTarget) {
          newStage = stage.id;
        } else {
          break;
        }
      }

      // If progress exceeds current stage target, move to next
      if (newStage !== currentStage) {
        setCurrentStage(newStage);
        onStageChange?.(newStage);
      }
    }, 500); // Update every 500ms

    return () => clearInterval(interval);
  }, [estimatedTime, currentStage, onStageChange]);

  const activeStage = STAGES.find(s => s.id === currentStage) || STAGES[0];
  const progressPercentage = Math.min(100, Math.max(0, progress));

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
              {activeStage.description}
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-2xl font-bold font-data tabular-nums text-brand-blue">
            {Math.floor(progressPercentage)}%
          </p>
          <p className="text-xs text-ink-muted">
            {/* Bug fix P2-2: Handle very long time (>5min) with proper formatting */}
            {elapsedTime >= 300
              ? `${Math.floor(elapsedTime / 60)}m ${elapsedTime % 60}s`
              : `${elapsedTime}s`}
            {' / '}
            {estimatedTime >= 300
              ? `${Math.floor(estimatedTime / 60)}m ${estimatedTime % 60}s`
              : `${estimatedTime}s`}
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

      {/* Meta information */}
      <div className="flex justify-between text-xs text-ink-secondary pt-3 border-t border-strong">
        <span>
          {/* Issue #109: Show progress "X of Y states processed" for better feedback */}
          {statesProcessed > 0 ? (
            <>
              <span className="font-semibold text-brand-blue">{statesProcessed}</span>
              {' de '}
              <span className="font-semibold">{stateCount}</span>
              {` ${stateCount === 1 ? 'estado processado' : 'estados processados'}`}
            </>
          ) : (
            `Processando ${stateCount} ${stateCount === 1 ? 'estado' : 'estados'}`
          )}
        </span>
        <span>
          {elapsedTime < estimatedTime
            ? estimatedTime - elapsedTime >= 60
              ? `~${Math.floor((estimatedTime - elapsedTime) / 60)}m restantes`
              : `~${estimatedTime - elapsedTime}s restantes`
            : 'Finalizando...'}
        </span>
      </div>
    </div>
  );
}
