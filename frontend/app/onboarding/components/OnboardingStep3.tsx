import type { OnboardingData } from "./types";

interface OnboardingStep3Props {
  data: OnboardingData;
  isAnalyzing: boolean;
}

export function OnboardingStep3({ data, isAnalyzing }: OnboardingStep3Props) {
  const formatCurrency = (val: number) => {
    if (val === 0) return "Sem limite";
    return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);
  };

  // Extract display name from CNAE string
  const cnaeDisplay = data.cnae.includes("\u2014")
    ? data.cnae.split("\u2014")[1]?.trim() || data.cnae
    : data.cnae;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-1">Pronto para começar</h2>
        <p className="text-sm text-[var(--ink-secondary)]">
          Vamos encontrar suas primeiras oportunidades agora. Isso leva ~15 segundos.
        </p>
      </div>

      <div className="space-y-4 p-4 rounded-lg bg-[var(--surface-1)] border border-[var(--border)]">
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Segmento</div>
          <div className="text-sm font-medium text-[var(--ink)]">{cnaeDisplay}</div>
        </div>
        {data.objetivo_principal && (
          <div>
            <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Objetivo</div>
            <div className="text-sm text-[var(--ink)]">{data.objetivo_principal}</div>
          </div>
        )}
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Estados de atuação</div>
          <div className="flex flex-wrap gap-1 mt-1">
            {data.ufs_atuacao.length === 27 ? (
              <span className="text-sm text-[var(--ink)]">Todos os estados</span>
            ) : (
              data.ufs_atuacao.map((uf) => (
                <span key={uf} className="px-1.5 py-0.5 text-xs rounded bg-[var(--brand-blue)]/10 text-[var(--brand-blue)]">
                  {uf}
                </span>
              ))
            )}
          </div>
        </div>
        <div>
          <div className="text-xs text-[var(--ink-secondary)] uppercase tracking-wide">Faixa de valor</div>
          <div className="text-sm text-[var(--ink)]">
            {formatCurrency(data.faixa_valor_min)} — {formatCurrency(data.faixa_valor_max)}
          </div>
        </div>
      </div>

      {isAnalyzing && (
        <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--brand-blue)]/5 border border-[var(--brand-blue)]/20">
          <div className="w-5 h-5 border-2 border-[var(--brand-blue)] border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-[var(--brand-blue)]">Analisando oportunidades...</p>
            <p className="text-xs text-[var(--ink-secondary)]">Configurando seu perfil e iniciando análise automática</p>
          </div>
        </div>
      )}
    </div>
  );
}
