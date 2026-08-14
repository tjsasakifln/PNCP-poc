import type { Provenance, SurfaceState } from "@/lib/intelligence/types";

const STATE_COPY: Record<SurfaceState, { label: string; tone: string }> = {
  ok: { label: "Dado disponível", tone: "text-emerald-800 bg-emerald-50 border-emerald-200" },
  empty: { label: "Sem cobertura neste recorte", tone: "text-amber-900 bg-amber-50 border-amber-200" },
  stale: { label: "Recorte desatualizado", tone: "text-orange-900 bg-orange-50 border-orange-200" },
  blocked: { label: "Leitura bloqueada", tone: "text-red-900 bg-red-50 border-red-200" },
  error: { label: "Falha temporária", tone: "text-red-900 bg-red-50 border-red-200" },
  unknown: { label: "Estado desconhecido", tone: "text-slate-800 bg-slate-50 border-slate-200" },
};

function formatWhen(value: string | null | undefined): string {
  if (!value) return "desconhecida";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

export function ProvenanceBar({
  provenance,
  state = "ok",
}: {
  provenance: Provenance;
  state?: SurfaceState;
}) {
  const tone = STATE_COPY[state];
  return (
    <aside
      data-testid="provenance-bar"
      className={`rounded-lg border px-4 py-3 text-sm ${tone.tone}`}
    >
      <p className="font-semibold">{tone.label}</p>
      <dl className="mt-2 grid gap-1 sm:grid-cols-2">
        <div>
          <dt className="text-xs uppercase tracking-wide opacity-70">Fonte</dt>
          <dd>{provenance.source}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide opacity-70">Atualizado em</dt>
          <dd>{formatWhen(provenance.asOf)}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide opacity-70">Completude</dt>
          <dd>{provenance.completeness}</dd>
        </div>
        <div>
          <dt className="text-xs uppercase tracking-wide opacity-70">Freshness</dt>
          <dd>{provenance.freshness}</dd>
        </div>
      </dl>
      {provenance.reasonCodes.length > 0 && (
        <p className="mt-2 text-xs">Códigos: {provenance.reasonCodes.join(", ")}</p>
      )}
      {provenance.limitations.length > 0 && (
        <ul className="mt-2 list-disc space-y-1 pl-4 text-xs">
          {provenance.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </aside>
  );
}
