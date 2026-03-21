interface SlaData {
  avg_response_hours: number;
  pending_count: number;
  breached_count: number;
}

interface AdminSupportSLAProps {
  slaData: SlaData | null;
  slaLoading: boolean;
  onRefresh: () => void;
}

export function AdminSupportSLA({ slaData, slaLoading, onRefresh }: AdminSupportSLAProps) {
  return (
    <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-[var(--ink)]">SLA de Suporte</h2>
        <button
          onClick={onRefresh}
          disabled={slaLoading}
          className="text-xs px-3 py-1 border border-[var(--border)] rounded-button hover:bg-[var(--surface-1)] disabled:opacity-50 text-[var(--ink-secondary)]"
        >
          {slaLoading ? "Atualizando..." : "Atualizar"}
        </button>
      </div>
      {slaLoading && !slaData ? (
        <div className="h-16 bg-[var(--surface-1)] rounded animate-pulse" />
      ) : !slaData ? (
        <p className="text-sm text-[var(--ink-muted)]">Dados indisponiveis</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-card border border-[var(--border)] bg-[var(--surface-1)]">
            <p className="text-xs text-[var(--ink-muted)] mb-1">Tempo medio de resposta</p>
            <p className={`text-2xl font-bold ${
              slaData.avg_response_hours <= 8 ? "text-green-600" :
              slaData.avg_response_hours <= 20 ? "text-yellow-600" : "text-red-600"
            }`}>
              {slaData.avg_response_hours}h
            </p>
            <p className="text-xs text-[var(--ink-muted)]">horas uteis</p>
          </div>
          <div className="p-4 rounded-card border border-[var(--border)] bg-[var(--surface-1)]">
            <p className="text-xs text-[var(--ink-muted)] mb-1">Aguardando resposta</p>
            <p className={`text-2xl font-bold ${
              slaData.pending_count === 0 ? "text-green-600" :
              slaData.pending_count <= 3 ? "text-yellow-600" : "text-red-600"
            }`}>
              {slaData.pending_count}
            </p>
            <p className="text-xs text-[var(--ink-muted)]">conversas</p>
          </div>
          <div className="p-4 rounded-card border border-[var(--border)] bg-[var(--surface-1)]">
            <p className="text-xs text-[var(--ink-muted)] mb-1">SLA violado (&gt;20h)</p>
            <p className={`text-2xl font-bold ${
              slaData.breached_count === 0 ? "text-green-600" : "text-red-600"
            }`}>
              {slaData.breached_count}
            </p>
            <p className="text-xs text-[var(--ink-muted)]">conversas</p>
          </div>
        </div>
      )}
    </div>
  );
}
