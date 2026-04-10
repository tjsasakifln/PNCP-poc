import {
  buildContractsContext,
  generateLicitacoesFAQsWithFallback,
  generateCidadeSectorFAQsWithFallback,
  generateCidadeFAQsWithFallback,
  type ContratosSetorUfStats,
  type ContractsFallbackContext,
} from '@/lib/contracts-fallback';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeSetorUfStats(
  overrides: Partial<ContratosSetorUfStats> = {},
): ContratosSetorUfStats {
  return {
    sector_id: 'vestuario',
    sector_name: 'Vestuário e Uniformes',
    uf: 'SP',
    total_contracts: 42,
    total_value: 12_600_000,
    avg_value: 300_000,
    top_orgaos: [
      { nome: 'Secretaria de Segurança Pública SP', cnpj: '00000000000111', total_contratos: 12, valor_total: 4_500_000 },
      { nome: 'Polícia Militar SP', cnpj: '00000000000222', total_contratos: 8, valor_total: 3_200_000 },
    ],
    top_fornecedores: [
      { nome: 'Uniformes Brasil LTDA', cnpj: '12345678000101', total_contratos: 15, valor_total: 5_000_000 },
    ],
    monthly_trend: [],
    last_updated: '2026-04-10T00:00:00Z',
    ...overrides,
  };
}

const ZERO_STATS: ContratosSetorUfStats = makeSetorUfStats({
  total_contracts: 0,
  total_value: 0,
  avg_value: 0,
  top_orgaos: [],
  top_fornecedores: [],
});

// ---------------------------------------------------------------------------
// buildContractsContext
// ---------------------------------------------------------------------------

describe('buildContractsContext', () => {
  it('returns undefined when data is null', () => {
    expect(buildContractsContext(null)).toBeUndefined();
  });

  it('returns undefined when data is undefined', () => {
    expect(buildContractsContext(undefined)).toBeUndefined();
  });

  it('returns undefined when total_contracts is 0', () => {
    expect(buildContractsContext(ZERO_STATS)).toBeUndefined();
  });

  it('extracts totalContracts, avgContractValue and topOrgao from populated data', () => {
    const ctx = buildContractsContext(makeSetorUfStats());
    expect(ctx).toEqual({
      totalContracts: 42,
      avgContractValue: 300_000,
      topOrgao: 'Secretaria de Segurança Pública SP',
    });
  });

  it('leaves topOrgao undefined when top_orgaos is empty', () => {
    const ctx = buildContractsContext(makeSetorUfStats({ top_orgaos: [] }));
    expect(ctx).toEqual({
      totalContracts: 42,
      avgContractValue: 300_000,
      topOrgao: undefined,
    });
  });
});

// ---------------------------------------------------------------------------
// generateLicitacoesFAQsWithFallback — critical anti-contradiction tests
// ---------------------------------------------------------------------------

describe('generateLicitacoesFAQsWithFallback', () => {
  const ctxWithContracts: ContractsFallbackContext = {
    totalContracts: 42,
    avgContractValue: 300_000,
    topOrgao: 'Secretaria de Segurança Pública SP',
  };

  it('uses the explicit count when totalEditais > 0 (no "diversas")', () => {
    const faqs = generateLicitacoesFAQsWithFallback('Vestuário', 'São Paulo', 5, 100_000, undefined);
    expect(faqs).toHaveLength(5);
    expect(faqs[0].answer).toContain('5 licitações');
    expect(faqs[0].answer).not.toContain('diversas');
  });

  it('NEVER emits the word "diversas" — not even when totalEditais is 0', () => {
    // This is the critical regression test: the old FAQ said "diversas licitações"
    // when count was 0, contradicting the visible "0 editais" counter in the hero.
    const faqs = generateLicitacoesFAQsWithFallback('Vestuário', 'São Paulo', 0, 0, undefined);
    for (const faq of faqs) {
      expect(faq.answer).not.toContain('diversas');
    }
  });

  it('references historical contracts when totalEditais is 0 and context is provided', () => {
    const faqs = generateLicitacoesFAQsWithFallback(
      'Vestuário',
      'São Paulo',
      0,
      0,
      ctxWithContracts,
    );
    // FAQ #1 should explicitly say "não há editais abertos" and cite the contract count
    expect(faqs[0].answer).toContain('não há editais abertos');
    expect(faqs[0].answer).toContain('42 contratos');
  });

  it('honestly admits no data when totalEditais is 0 and no contracts found', () => {
    const faqs = generateLicitacoesFAQsWithFallback('Vestuário', 'São Paulo', 0, 0, undefined);
    expect(faqs[0].answer).toContain('não há editais abertos');
    expect(faqs[0].answer).toContain('não identificamos contratos recentes');
  });

  it('uses contract avg_value as fallback for FAQ #2 when avgValue is 0', () => {
    const faqs = generateLicitacoesFAQsWithFallback('Vestuário', 'São Paulo', 0, 0, ctxWithContracts);
    // FAQ #2 should reference the historical avg contract value as a benchmark
    expect(faqs[1].answer).toContain('contratos deste setor');
    expect(faqs[1].answer).toContain('valor médio');
  });

  it('enriches FAQ #4 with the top órgão when available', () => {
    const faqs = generateLicitacoesFAQsWithFallback('Vestuário', 'São Paulo', 0, 0, ctxWithContracts);
    expect(faqs[3].answer).toContain('Secretaria de Segurança Pública SP');
  });

  it('always returns exactly 5 FAQs regardless of branch', () => {
    expect(generateLicitacoesFAQsWithFallback('X', 'SP', 10, 1000, undefined)).toHaveLength(5);
    expect(generateLicitacoesFAQsWithFallback('X', 'SP', 0, 0, undefined)).toHaveLength(5);
    expect(generateLicitacoesFAQsWithFallback('X', 'SP', 0, 0, ctxWithContracts)).toHaveLength(5);
  });
});

// ---------------------------------------------------------------------------
// generateCidadeSectorFAQsWithFallback
// ---------------------------------------------------------------------------

describe('generateCidadeSectorFAQsWithFallback', () => {
  const ctx: ContractsFallbackContext = {
    totalContracts: 15,
    avgContractValue: 85_000,
    topOrgao: 'Prefeitura de Campinas',
  };

  it('NEVER emits "diversas" in any branch', () => {
    const branches = [
      generateCidadeSectorFAQsWithFallback('Campinas', 'SP', 'Vestuário', 10, 50_000, undefined),
      generateCidadeSectorFAQsWithFallback('Campinas', 'SP', 'Vestuário', 0, 0, undefined),
      generateCidadeSectorFAQsWithFallback('Campinas', 'SP', 'Vestuário', 0, 0, ctx),
    ];
    for (const faqs of branches) {
      for (const faq of faqs) {
        expect(faq.answer).not.toContain('diversas');
      }
    }
  });

  it('returns 4 FAQs', () => {
    expect(
      generateCidadeSectorFAQsWithFallback('Campinas', 'SP', 'Vestuário', 0, 0, ctx),
    ).toHaveLength(4);
  });

  it('references historical contracts when totalEditais is 0 and context is provided', () => {
    const faqs = generateCidadeSectorFAQsWithFallback('Campinas', 'SP', 'Vestuário', 0, 0, ctx);
    expect(faqs[0].answer).toContain('15 contratos');
    expect(faqs[2].answer).toContain('Prefeitura de Campinas');
  });
});

// ---------------------------------------------------------------------------
// generateCidadeFAQsWithFallback
// ---------------------------------------------------------------------------

describe('generateCidadeFAQsWithFallback', () => {
  it('NEVER says volume "varia semana a semana" when count is 0 (old contradiction)', () => {
    // The old inline FAQ said "O volume de editais varia semana a semana"
    // to paper over a 0-count. The new implementation admits zero honestly.
    const faqs = generateCidadeFAQsWithFallback('Campinas', 'SP', 0, 0, undefined, undefined);
    expect(faqs[1].answer).toContain('não há editais abertos');
  });

  it('prefers live top órgãos over historical context for FAQ #3 when provided', () => {
    const faqs = generateCidadeFAQsWithFallback(
      'Campinas',
      'SP',
      5,
      50_000,
      undefined,
      ['Prefeitura Municipal', 'Secretaria de Educação'],
    );
    expect(faqs[2].answer).toContain('Prefeitura Municipal');
    expect(faqs[2].answer).toContain('Secretaria de Educação');
  });

  it('falls back to historical topOrgao when no live órgãos and contracts exist', () => {
    const ctx: ContractsFallbackContext = {
      totalContracts: 10,
      avgContractValue: 50_000,
      topOrgao: 'Prefeitura de Campinas',
    };
    const faqs = generateCidadeFAQsWithFallback('Campinas', 'SP', 0, 0, ctx, undefined);
    expect(faqs[2].answer).toContain('Prefeitura de Campinas');
  });

  it('returns exactly 4 FAQs', () => {
    expect(generateCidadeFAQsWithFallback('Campinas', 'SP', 0, 0, undefined)).toHaveLength(4);
  });
});
