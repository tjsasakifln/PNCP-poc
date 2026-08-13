import type { SurfaceState } from "@/lib/intelligence/types";

const COPY: Record<Exclude<SurfaceState, "ok">, { title: string; body: string }> = {
  empty: {
    title: "Não há cobertura neste recorte",
    body: "Isso não significa que o fato não exista na origem. O recorte conhecido está vazio ou ainda não foi publicado no contrato de leitura.",
  },
  stale: {
    title: "Você está vendo a última revisão válida",
    body: "O recorte está desatualizado. Preferimos servir o último HTML/dado conhecido a inventar um zero.",
  },
  blocked: {
    title: "A leitura pública está bloqueada",
    body: "O contrato de leitura recusou este recorte (completude, kill-switch ou provenance insuficiente).",
  },
  error: {
    title: "Falha temporária ao ler o recorte",
    body: "O erro de backend não apaga o último estado válido. Tente de novo; se persistir, o dado não deve ser tratado como zero.",
  },
  unknown: {
    title: "Estado do dado é desconhecido",
    body: "Ausência de métrica não é zero. Sem freshness ou contagem confiável, não afirmamos cobertura.",
  },
};

export function DataStateBanner({ state }: { state: SurfaceState }) {
  if (state === "ok") return null;
  const copy = COPY[state];
  return (
    <div
      data-testid="data-state-banner"
      data-state={state}
      className="rounded-lg border border-border bg-surface-1 px-4 py-3"
    >
      <p className="font-semibold text-ink">{copy.title}</p>
      <p className="mt-1 text-sm text-ink-secondary">{copy.body}</p>
    </div>
  );
}
