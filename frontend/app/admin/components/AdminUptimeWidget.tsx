import Link from "next/link";

interface AdminUptimeWidgetProps {
  uptimePct30d: number | null;
  loading?: boolean;
  onRetry?: () => void;
}

export function AdminUptimeWidget({ uptimePct30d, loading = false, onRetry }: AdminUptimeWidgetProps) {
  const statusLabel = () => {
    if (loading) return "Carregando...";
    if (uptimePct30d === null) return "Dados serão exibidos após o primeiro ciclo de monitoramento.";
    if (uptimePct30d >= 99) return "Alta disponibilidade";
    if (uptimePct30d >= 95) return "Disponibilidade aceitavel";
    return "Abaixo do esperado";
  };

  return (
    <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--ink)]">Uptime (30 dias)</h2>
        <div className="flex items-center gap-3">
          {uptimePct30d === null && !loading && onRetry && (
            <button
              onClick={onRetry}
              className="text-xs px-3 py-1 border border-[var(--border)] rounded-button hover:bg-[var(--surface-1)] text-[var(--ink-secondary)]"
            >
              Tentar novamente
            </button>
          )}
          <Link href="/status" className="text-sm text-[var(--brand-blue)] hover:underline">
            Status Page
          </Link>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <div className={`text-4xl font-bold ${
          uptimePct30d === null ? "text-[var(--ink-muted)]" :
          uptimePct30d >= 99 ? "text-green-600" :
          uptimePct30d >= 95 ? "text-yellow-600" : "text-red-600"
        }`}>
          {loading ? (
            <div className="h-10 w-20 bg-[var(--surface-1)] rounded animate-pulse" />
          ) : uptimePct30d !== null ? `${uptimePct30d}%` : "\u2014"}
        </div>
        <div className="text-sm text-[var(--ink-secondary)]">
          {statusLabel()}
        </div>
      </div>
    </div>
  );
}
