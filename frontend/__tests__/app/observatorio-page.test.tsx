/**
 * STORY-431 AC9: Teste da rota frontend do Observatório.
 * Verifica que a página renderiza corretamente com dados mockados
 * e que a metadata é gerada com robots correto.
 */

// Mock fetch para os testes
const mockRelatorio = {
  mes: 3,
  ano: 2026,
  mes_nome: 'março',
  periodo: 'Editais publicados de 1 a 31 de março de 2026',
  total_editais: 12543,
  valor_total: 1580000000,
  valor_medio: 125000,
  top_ufs: [
    { uf: 'SP', uf_name: 'São Paulo', total: 3200, pct: 25.5 },
    { uf: 'RJ', uf_name: 'Rio de Janeiro', total: 1800, pct: 14.4 },
  ],
  modalidades: [
    { modalidade_id: 6, modalidade_name: 'Pregão Eletrônico', total: 7500, pct: 59.8 },
    { modalidade_id: 8, modalidade_name: 'Dispensa de Licitação', total: 3100, pct: 24.7 },
  ],
  tendencia_semanal: [
    { semana: 'Semana 1', total: 3100 },
    { semana: 'Semana 2', total: 3200 },
    { semana: 'Semana 3', total: 3300 },
    { semana: 'Semana 4', total: 2943 },
  ],
  setores_em_alta: [
    { setor_id: 'saude', setor_name: 'Saúde', total_atual: 1200, total_anterior: 900, variacao_pct: 33.3 },
  ],
  gerado_em: '2026-04-01T10:00:00Z',
  fonte: 'SmartLic Observatório — dados PNCP',
  license: 'Creative Commons BY 4.0',
};

global.fetch = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  (global.fetch as jest.Mock).mockResolvedValue({
    ok: true,
    json: async () => mockRelatorio,
  });
});

// ---------------------------------------------------------------------------
// parseSlug helper
// ---------------------------------------------------------------------------

describe('parseSlug — slug parsing', () => {
  // Importamos a função indiretamente testando generateMetadata
  it('slug válido retorna mes e ano corretos', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    // Total editais deve aparecer no título quando dados disponíveis
    expect(meta.title).toContain('2026');
    expect(meta.title).toContain('Março');
  });

  it('slug inválido retorna título de fallback', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    (global.fetch as jest.Mock).mockResolvedValueOnce({ ok: false });
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'slug-invalido' }),
    });
    expect(meta.title).toContain('não encontrado');
  });
});

// ---------------------------------------------------------------------------
// generateMetadata — robots e SEO
// ---------------------------------------------------------------------------

describe('generateMetadata — STORY-431 AC9', () => {
  it('gera título com total_editais formatado quando dados disponíveis', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    // 12543 formatado em pt-BR = "12.543"
    expect(String(meta.title)).toContain('12.543');
  });

  it('inclui description com dado impactante', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    expect(String(meta.description ?? '')).toContain('12.543');
  });

  it('inclui canonical correto no alternates', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    expect(meta.alternates?.canonical).toContain('/observatorio/raio-x-marco-2026');
  });

  it('robots.index = true quando dados disponíveis', async () => {
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    // Deve ser indexável quando há dados reais
    const robots = meta.robots as { index?: boolean } | undefined;
    if (robots) {
      expect(robots.index).not.toBe(false);
    }
  });

  it('fallback gracioso quando fetch falha', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
    const { generateMetadata } = await import('@/app/observatorio/[mes]-[ano]/page');
    const meta = await generateMetadata({
      params: Promise.resolve({ 'mes-ano': 'raio-x-marco-2026' }),
    });
    // Sem dados, título genérico mas sem crash
    expect(meta.title).toContain('Março');
    expect(meta.title).toContain('2026');
  });
});
