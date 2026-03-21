// Step progress indicator with ARIA progressbar

export function OnboardingProgress({ currentStep, totalSteps }: { currentStep: number; totalSteps: number }) {
  return (
    <div
      className="flex items-center gap-2 mb-8"
      role="progressbar"
      aria-valuenow={currentStep + 1}
      aria-valuemin={1}
      aria-valuemax={totalSteps}
      aria-label="Progresso do cadastro"
    >
      {Array.from({ length: totalSteps }, (_, i) => (
        <div key={i} className="flex-1 flex items-center gap-2">
          <div
            className={`h-2 rounded-full flex-1 transition-colors duration-300 ${
              i < currentStep
                ? "bg-[var(--brand-blue)]"
                : i === currentStep
                ? "bg-[var(--brand-blue)] opacity-60"
                : "bg-[var(--border)]"
            }`}
          />
        </div>
      ))}
      <span className="text-xs text-[var(--ink-secondary)] ml-2 whitespace-nowrap" aria-hidden="true">
        {currentStep + 1} de {totalSteps}
      </span>
    </div>
  );
}
