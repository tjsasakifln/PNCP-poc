/**
 * STORY-430 AC2/AC7: Tests for dynamic noindex on thin content pages.
 * Covers /blog/programmatic/[setor]/[uf] and /alertas-publicos/[setor]/[uf].
 */

// Single mock for @/lib/programmatic covering all functions used by both pages
jest.mock('@/lib/programmatic', () => ({
  generateSectorUfParams: jest.fn(() => []),
  fetchSectorUfBlogStats: jest.fn(),
  fetchAlertasPublicos: jest.fn(),
  getSectorFromSlug: jest.fn(),
  formatBRL: jest.fn((v: number) => `R$ ${v}`),
  generateSectorFAQs: jest.fn(() => []),
  ALL_UFS: ['SP', 'SC', 'RJ'],
  UF_NAMES: { SP: 'São Paulo', SC: 'Santa Catarina', RJ: 'Rio de Janeiro' },
}));

jest.mock('@/lib/seo', () => ({
  buildCanonical: jest.fn((path: string) => `https://smartlic.tech${path}`),
  getFreshnessLabel: jest.fn(() => 'Hoje'),
}));

const lib = require('@/lib/programmatic');

import { generateMetadata as generateProgrammaticMetadata } from '@/app/blog/programmatic/[setor]/[uf]/page';
import { generateMetadata as generateAlertasMetadata } from '@/app/alertas-publicos/[setor]/[uf]/page';

const MOCK_SECTOR = { id: 'saude', name: 'Saúde', slug: 'saude' };

// ---------------------------------------------------------------------------
// /blog/programmatic/[setor]/[uf]
// ---------------------------------------------------------------------------

describe('blog/programmatic/[setor]/[uf] generateMetadata — STORY-430 AC2', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lib.getSectorFromSlug.mockReturnValue(MOCK_SECTOR);
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna robots noindex quando total_editais < 5 (threshold padrão)', async () => {
    lib.fetchSectorUfBlogStats.mockResolvedValue({
      total_editais: 2,
      avg_value: 0,
      last_updated: new Date().toISOString(),
      top_oportunidades: [],
    });
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots noindex quando total_editais = 0', async () => {
    lib.fetchSectorUfBlogStats.mockResolvedValue({
      total_editais: 0,
      avg_value: 0,
      top_oportunidades: [],
    });
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots index:true quando total_editais >= 5', async () => {
    lib.fetchSectorUfBlogStats.mockResolvedValue({
      total_editais: 12,
      avg_value: 200000,
      last_updated: new Date().toISOString(),
      top_oportunidades: [],
    });
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect((meta.robots as any)?.index).not.toBe(false);
    expect(meta.alternates?.canonical).toContain('/blog/programmatic/saude/sp');
  });

  it('respeita MIN_ACTIVE_BIDS_FOR_INDEX env var customizado', async () => {
    process.env.MIN_ACTIVE_BIDS_FOR_INDEX = '10';
    lib.fetchSectorUfBlogStats.mockResolvedValue({
      total_editais: 7,
      avg_value: 0,
      top_oportunidades: [],
    });
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna 404 metadata para setor inválido', async () => {
    lib.getSectorFromSlug.mockReturnValue(null);
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'nao-existe', uf: 'sp' }),
    });
    expect(meta.title).toContain('não encontrada');
  });

  it('retorna 404 metadata para UF inválida', async () => {
    const meta = await generateProgrammaticMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'xx' }),
    });
    expect(meta.title).toContain('não encontrada');
  });
});

// ---------------------------------------------------------------------------
// /alertas-publicos/[setor]/[uf]
// ---------------------------------------------------------------------------

describe('alertas-publicos/[setor]/[uf] generateMetadata — STORY-430 AC2', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    lib.getSectorFromSlug.mockReturnValue(MOCK_SECTOR);
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna robots noindex quando bids.length < 5', async () => {
    lib.fetchAlertasPublicos.mockResolvedValue({
      bids: [{ pncp_id: '1' }, { pncp_id: '2' }],
      total: 2,
      last_updated: new Date().toISOString(),
    });
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots noindex quando total = 0 e bids vazio', async () => {
    lib.fetchAlertasPublicos.mockResolvedValue({ bids: [], total: 0 });
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots index:true quando total >= 5', async () => {
    lib.fetchAlertasPublicos.mockResolvedValue({
      bids: Array(8).fill({ pncp_id: 'x' }),
      total: 8,
      last_updated: new Date().toISOString(),
    });
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect((meta.robots as any)?.index).not.toBe(false);
  });

  it('retorna robots noindex quando fetchAlertasPublicos retorna null', async () => {
    lib.fetchAlertasPublicos.mockResolvedValue(null);
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna metadata vazia para setor inválido', async () => {
    lib.getSectorFromSlug.mockReturnValue(null);
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'nao-existe', uf: 'sp' }),
    });
    expect(Object.keys(meta)).toHaveLength(0);
  });

  it('respeita MIN_ACTIVE_BIDS_FOR_INDEX env var', async () => {
    process.env.MIN_ACTIVE_BIDS_FOR_INDEX = '3';
    lib.fetchAlertasPublicos.mockResolvedValue({
      bids: Array(3).fill({ pncp_id: 'x' }),
      total: 3,
    });
    const meta = await generateAlertasMetadata({
      params: Promise.resolve({ setor: 'saude', uf: 'sp' }),
    });
    // 3 >= 3 → deve indexar
    expect((meta.robots as any)?.index).not.toBe(false);
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });
});
