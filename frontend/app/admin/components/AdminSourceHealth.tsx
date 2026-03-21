interface SourceInfo {
  status: string;
  latency_ms?: number;
  last_check?: string;
}

interface AdminSourceHealthProps {
  sourceHealth: Record<string, SourceInfo>;
  sourceHealthLoading: boolean;
  onRefresh: () => void;
}

export function AdminSourceHealth({ sourceHealth, sourceHealthLoading, onRefresh }: AdminSourceHealthProps) {
  return (
    <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-[var(--ink)]">Fontes ativas</h2>
        <button
          onClick={onRefresh}
          disabled={sourceHealthLoading}
          className="text-xs px-3 py-1 border border-[var(--border)] rounded-button hover:bg-[var(--surface-1)] disabled:opacity-50 text-[var(--ink-secondary)]"
        >
          {sourceHealthLoading ? "Atualizando..." : "Atualizar"}
        </button>
      </div>
      {sourceHealthLoading && Object.keys(sourceHealth).length === 0 ? (
        <div className="h-12 bg-[var(--surface-1)] rounded animate-pulse" />
      ) : Object.keys(sourceHealth).length === 0 ? (
        <p className="text-sm text-[var(--ink-muted)]">Status indisponivel</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Object.entries(sourceHealth).map(([code, info]) => {
            const statusLabel =
              info.status === "healthy" ? "UP" : info.status === "degraded" ? "DEGRADED" : "DOWN";
            const statusColor =
              info.status === "healthy"
                ? "text-green-600 bg-green-50"
                : info.status === "degraded"
                  ? "text-yellow-600 bg-yellow-50"
                  : "text-red-600 bg-red-50";
            const dotColor =
              info.status === "healthy"
                ? "bg-green-500"
                : info.status === "degraded"
                  ? "bg-yellow-500"
                  : "bg-red-500";
            const sourceName =
              code === "pncp" ? "PNCP" : code === "portal" ? "PCP v2" : code === "comprasgov" ? "ComprasGov" : code;

            return (
              <div
                key={code}
                className="flex items-center gap-3 p-4 rounded-card border border-[var(--border)] bg-[var(--surface-1)]"
              >
                <span className={`w-3 h-3 rounded-full ${dotColor} flex-shrink-0`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--ink)]">{sourceName}</p>
                  {info.latency_ms !== undefined && (
                    <p className="text-xs text-[var(--ink-muted)]">{info.latency_ms}ms</p>
                  )}
                </div>
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${statusColor}`}>
                  {statusLabel}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
