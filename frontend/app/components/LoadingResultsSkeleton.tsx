/**
 * LoadingResultsSkeleton Component - Issue #111
 * Skeleton loader for search results to improve perceived performance
 *
 * Shows animated skeleton cards while waiting for API response
 * Matches the layout of actual result cards for smooth transition
 */

import React from 'react';

export interface LoadingResultsSkeletonProps {
  /** Number of skeleton cards to show */
  count?: number;
}

export function LoadingResultsSkeleton({ count = 3 }: LoadingResultsSkeletonProps) {
  return (
    <div className="mt-6 sm:mt-8 space-y-4 sm:space-y-6 animate-fade-in-up" role="status" aria-label="Carregando resultados">
      {/* Summary Card Skeleton */}
      <div className="p-4 sm:p-6 bg-surface-0 border border-strong rounded-card">
        {/* Executive summary text skeleton */}
        <div className="space-y-3 mb-6">
          <div className="h-4 bg-surface-2 rounded animate-pulse w-full" />
          <div className="h-4 bg-surface-2 rounded animate-pulse w-5/6" />
          <div className="h-4 bg-surface-2 rounded animate-pulse w-4/6" />
        </div>

        {/* Stats skeleton */}
        <div className="flex flex-col sm:flex-row flex-wrap gap-4 sm:gap-8">
          <div>
            <div className="h-10 bg-surface-2 rounded animate-pulse w-24 mb-2" />
            <div className="h-4 bg-surface-2 rounded animate-pulse w-20" />
          </div>
          <div>
            <div className="h-10 bg-surface-2 rounded animate-pulse w-32 mb-2" />
            <div className="h-4 bg-surface-2 rounded animate-pulse w-24" />
          </div>
        </div>

        {/* Highlights skeleton */}
        <div className="mt-6">
          <div className="h-5 bg-surface-2 rounded animate-pulse w-32 mb-3" />
          <div className="space-y-2">
            <div className="h-4 bg-surface-2 rounded animate-pulse w-full" />
            <div className="h-4 bg-surface-2 rounded animate-pulse w-4/5" />
            <div className="h-4 bg-surface-2 rounded animate-pulse w-5/6" />
          </div>
        </div>
      </div>

      {/* Download button skeleton */}
      <div className="h-14 bg-surface-2 rounded-button animate-pulse w-full" />

      {/* Stats text skeleton */}
      <div className="flex justify-center">
        <div className="h-4 bg-surface-2 rounded animate-pulse w-64" />
      </div>

      {/* Screen reader feedback */}
      <span className="sr-only">Processando resultados da busca, por favor aguarde...</span>
    </div>
  );
}
