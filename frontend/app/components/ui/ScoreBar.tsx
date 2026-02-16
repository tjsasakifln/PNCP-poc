'use client';

import { motion } from 'framer-motion';
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

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${bar}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${percentage}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
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
