/**
 * ProgressSteps — States-processed and cancel footer for the loading indicator.
 * Extracted from EnhancedLoadingProgress. DEBT-FE-014.
 */

interface ProgressStepsProps {
  stateCount: number;
  statesProcessed: number;
  onCancel?: () => void;
}

export function ProgressSteps({ stateCount, statesProcessed, onCancel }: ProgressStepsProps) {
  const statesLabel = (() => {
    if (statesProcessed > 0) {
      if (stateCount >= 27) return "Analisando em todo o Brasil...";
      return (
        <>
          <span className="font-semibold text-brand-blue">{statesProcessed}</span>
          {" de "}
          <span className="font-semibold">{stateCount}</span>
          {` ${stateCount === 1 ? "estado processado" : "estados processados"}`}
        </>
      );
    }
    return stateCount >= 27
      ? "Analisando em todo o Brasil..."
      : `Processando ${stateCount} ${stateCount === 1 ? "estado" : "estados"}`;
  })();

  return (
    <div className="flex justify-between items-center text-xs text-ink-secondary pt-3 border-t border-strong">
      <span>{statesLabel}</span>

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
  );
}
