interface ReconRun {
  id: string;
  run_at: string;
  total_checked: number;
  divergences_found: number;
  auto_fixed: number;
  manual_review: number;
  duration_ms: number;
}

interface AdminReconciliationProps {
  reconHistory: ReconRun[];
  reconLoading: boolean;
  reconTriggering: boolean;
  onTrigger: () => void;
}

export function AdminReconciliation({ reconHistory, reconLoading, reconTriggering, onTrigger }: AdminReconciliationProps) {
  return (
    <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-[var(--ink)]">Reconciliacao Stripe</h2>
        <button
          onClick={onTrigger}
          disabled={reconTriggering}
          className="px-4 py-2 text-sm bg-[var(--brand-navy)] text-white rounded-button hover:bg-[var(--brand-blue)] disabled:opacity-50"
        >
          {reconTriggering ? "Executando..." : "Executar agora"}
        </button>
      </div>

      {reconLoading ? (
        <div className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />
      ) : reconHistory.length === 0 ? (
        <p className="text-sm text-[var(--ink-muted)]">Nenhuma execucao registrada</p>
      ) : (
        <div className="space-y-2">
          {reconHistory.map((run) => {
            const statusColor =
              run.divergences_found === 0
                ? "text-green-600"
                : run.divergences_found < 5
                  ? "text-yellow-600"
                  : "text-red-600";
            const statusDot =
              run.divergences_found === 0
                ? "bg-green-500"
                : run.divergences_found < 5
                  ? "bg-yellow-500"
                  : "bg-red-500";

            return (
              <div
                key={run.id}
                className="flex items-center gap-4 text-sm py-2 px-3 rounded bg-[var(--surface-1)]"
              >
                <span className={`w-2 h-2 rounded-full ${statusDot}`} />
                <span className="text-[var(--ink-muted)] w-36">
                  {new Date(run.run_at).toLocaleString("pt-BR")}
                </span>
                <span className="text-[var(--ink-secondary)]">
                  {run.total_checked} verificados
                </span>
                <span className={statusColor}>
                  {run.divergences_found} divergencia{run.divergences_found !== 1 ? "s" : ""}
                </span>
                <span className="text-[var(--ink-secondary)]">
                  {run.auto_fixed} corrigidas
                </span>
                {run.manual_review > 0 && (
                  <span className="text-yellow-600">
                    {run.manual_review} manual
                  </span>
                )}
                <span className="text-[var(--ink-muted)] ml-auto">
                  {run.duration_ms}ms
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
