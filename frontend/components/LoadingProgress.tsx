/**
 * LoadingProgress Component - Basic loading indicator
 * Created as base for EnhancedLoadingProgress (Feature #2)
 * Phase 3 - Day 8
 */

import React from 'react';

interface LoadingProgressProps {
  currentStep: number;
  estimatedTime: number;
  stateCount: number;
}

export function LoadingProgress({
  currentStep,
  estimatedTime,
  stateCount,
}: LoadingProgressProps) {
  return (
    <div className="mt-6 sm:mt-8 p-4 sm:p-6 bg-surface-0 border border-strong rounded-card animate-fade-in-up">
      <div className="flex items-center justify-center gap-3 mb-4">
        <svg className="animate-spin h-6 w-6 text-brand-blue" viewBox="0 0 24 24">
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
        <p className="text-base sm:text-lg font-medium text-ink">
          Buscando licitações...
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm text-ink-secondary">
          <span>Processando {stateCount} {stateCount === 1 ? 'estado' : 'estados'}</span>
          <span>~{estimatedTime}s estimados</span>
        </div>

        {/* Progress bar placeholder */}
        <div className="w-full bg-surface-2 rounded-full h-2">
          <div
            className="bg-brand-blue h-2 rounded-full transition-all duration-300 animate-pulse"
            style={{ width: '30%' }}
          />
        </div>

        <p className="text-xs text-ink-muted text-center mt-3">
          Aguarde enquanto processamos sua busca...
        </p>
      </div>
    </div>
  );
}
