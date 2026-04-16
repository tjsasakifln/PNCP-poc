/**
 * ProgressBar — Visual progress bar with ARIA semantics.
 * Extracted from EnhancedLoadingProgress. DEBT-FE-014.
 * DEBT-v3-S2 AC12: No percentage number is displayed.
 * DEBT-v3-S2 AC9: Indeterminate animation when stuck (>45s).
 */

interface ProgressBarProps {
  /** 0-100 */
  progress: number;
  /** Amber styling for degraded state */
  isDegraded?: boolean;
  /** DEBT-v3-S2 AC9: Switch to indeterminate animation when stuck */
  isStuck?: boolean;
}

export function ProgressBar({ progress, isDegraded = false, isStuck = false }: ProgressBarProps) {
  const colorClass = isDegraded
    ? "bg-gradient-to-r from-amber-500 to-amber-600"
    : "bg-gradient-to-r from-brand-blue to-brand-blue-hover";

  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className="mb-5">
      <div className="w-full bg-surface-2 rounded-full h-2.5 overflow-hidden">
        {isStuck ? (
          <div
            className={`${colorClass} h-2.5 rounded-full animate-indeterminate-bar w-[30%]`}
            role="progressbar"
            aria-label="Buscando em mais fontes"
          />
        ) : (
          // eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width computed from clampedProgress
          <div
            className={`${colorClass} h-2.5 rounded-full transition-all duration-700 ease-out`}
            style={{ width: `${clampedProgress}%` }}
            role="progressbar"
            aria-valuenow={clampedProgress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        )}
      </div>
    </div>
  );
}
