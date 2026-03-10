'use client';

import { useState, useEffect, useRef } from 'react';
import { getScoreColor } from '@/lib/data/analysisExamples';

interface ScoreBarProps {
  score: number;
  maxScore?: number;
  showLabel?: boolean;
  className?: string;
}

/**
 * GTM-005: Visual compatibility score bar (0-10).
 * Color-coded: green (7.5+), amber (5-7.4), red (<5).
 */
export function ScoreBar({
  score,
  maxScore = 10,
  showLabel = true,
  className = '',
}: ScoreBarProps) {
  const { text, bar } = getScoreColor(score);
  const percentage = (score / maxScore) * 100;
  const [width, setWidth] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setWidth(percentage);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [percentage]);

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div ref={ref} className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${bar} transition-all duration-[800ms] ease-[cubic-bezier(0.4,0,0.2,1)]`}
          style={{ width: `${width}%` }}
        />
      </div>
      {showLabel && (
        <span className={`text-sm font-bold tabular-nums min-w-[2.5rem] text-right ${text}`}>
          {score.toFixed(1)}
        </span>
      )}
    </div>
  );
}
