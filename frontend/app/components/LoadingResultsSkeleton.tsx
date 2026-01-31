/**
 * LoadingResultsSkeleton Component
 * Issue #111: Loading skeleton for search results
 * Shows animated placeholder cards while results load
 */

import React from 'react';

interface LoadingResultsSkeletonProps {
  count?: number;
}

export function LoadingResultsSkeleton({ count = 3 }: LoadingResultsSkeletonProps) {
  return (
    <div className="mt-6 space-y-4" role="status" aria-label="Loading results">
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className="p-4 sm:p-6 bg-surface-0 border border-strong rounded-card animate-pulse"
        >
          {/* Title skeleton */}
          <div className="h-6 bg-surface-2 rounded w-3/4 mb-4" />

          {/* Content skeleton */}
          <div className="space-y-2 mb-4">
            <div className="h-4 bg-surface-2 rounded w-full" />
            <div className="h-4 bg-surface-2 rounded w-5/6" />
            <div className="h-4 bg-surface-2 rounded w-4/6" />
          </div>

          {/* Meta info skeleton */}
          <div className="flex gap-4 flex-wrap">
            <div className="h-4 bg-surface-2 rounded w-24" />
            <div className="h-4 bg-surface-2 rounded w-32" />
            <div className="h-4 bg-surface-2 rounded w-20" />
          </div>
        </div>
      ))}
      <span className="sr-only">Carregando resultados...</span>
    </div>
  );
}

export default LoadingResultsSkeleton;
