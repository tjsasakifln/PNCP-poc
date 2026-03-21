import Link from "next/link";

interface AdminUptimeWidgetProps {
  uptimePct30d: number | null;
}

export function AdminUptimeWidget({ uptimePct30d }: AdminUptimeWidgetProps) {
  return (
    <div className="mb-8 p-6 bg-[var(--surface-0)] border border-[var(--border)] rounded-card">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--ink)]">Uptime (30 dias)</h2>
        <Link href="/status" className="text-sm text-[var(--brand-blue)] hover:underline">
          Status Page
        </Link>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <div className={`text-4xl font-bold ${
          uptimePct30d === null ? "text-[var(--ink-muted)]" :
          uptimePct30d >= 99 ? "text-green-600" :
          uptimePct30d >= 95 ? "text-yellow-600" : "text-red-600"
        }`}>
          {uptimePct30d !== null ? `${uptimePct30d}%` : "\u2014"}
        </div>
        <div className="text-sm text-[var(--ink-secondary)]">
          {uptimePct30d !== null && uptimePct30d >= 99
            ? "Alta disponibilidade"
            : uptimePct30d !== null && uptimePct30d >= 95
              ? "Disponibilidade aceitavel"
              : uptimePct30d !== null
                ? "Abaixo do esperado"
                : "Carregando..."}
        </div>
      </div>
    </div>
  );
}
