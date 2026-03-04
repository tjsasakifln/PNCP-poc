// ─── Profile context type & helpers ──────────────────────────────────────────
// Extracted from page.tsx to avoid exporting non-page fields (Next.js 16 strict)

export interface ProfileContext {
  ufs_atuacao?: string[];
  setor_principal?: string;
  faixa_valor_min?: number | null;
  faixa_valor_max?: number | null;
  porte_empresa?: string;
  experiencia_licitacoes?: string;
  capacidade_funcionarios?: number | null;
  faturamento_anual?: number | null;
  atestados?: string[];
}

export function completenessCount(ctx: ProfileContext): number {
  const fields = [
    ctx.ufs_atuacao?.length ? ctx.ufs_atuacao : null,
    ctx.porte_empresa || null,
    ctx.experiencia_licitacoes || null,
    ctx.faixa_valor_min != null ? ctx.faixa_valor_min : null,
    ctx.capacidade_funcionarios != null ? ctx.capacidade_funcionarios : null,
    ctx.faturamento_anual != null ? ctx.faturamento_anual : null,
    ctx.atestados?.length ? ctx.atestados : null,
  ];
  return fields.filter(f => f !== null && f !== undefined).length;
}

export const TOTAL_PROFILE_FIELDS = 7;
