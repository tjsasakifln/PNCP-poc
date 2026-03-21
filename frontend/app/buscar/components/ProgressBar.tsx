/**
 * ProgressBar — Visual progress bar with ARIA semantics.
 * Extracted from EnhancedLoadingProgress. DEBT-FE-014.
 */

interface ProgressBarProps {
  /** 0–100 */
  progress: number;
  /** Amber styling for degraded state */
  isDegraded?: boolean;
}

export function ProgressBar({ progress, isDegraded = false }: ProgressBarProps) {
  const colorClass = isDegraded
    ? "bg-gradient-to-r from-amber-500 to-amber-600"
    : "bg-gradient-to-r from-brand-blue to-brand-blue-hover";

  return (
    <div className="mb-5">
      <div className="w-full bg-surface-2 rounded-full h-2.5 overflow-hidden">
        <div
          className={`${colorClass} h-2.5 rounded-full transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          role="progressbar"
          aria-valuenow={Math.min(100, Math.max(0, progress))}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
