/**
 * STORY-430 AC7: Tests for dynamic noindex on thin content pages.
 */

import { generateMetadata } from '@/app/licitacoes/[setor]/page';

// Mock dependencies
jest.mock('@/lib/sectors', () => ({
  getSectorBySlug: jest.fn(),
  getAllSectorSlugs: jest.fn(() => ['saude', 'informatica']),
  getRelatedSectors: jest.fn(() => []),
  fetchSectorStats: jest.fn(),
  formatBRL: jest.fn((v: number) => `R$ ${v}`),
  SECTORS: [],
}));
jest.mock('@/data/sector-faqs', () => ({ getSectorFaqs: jest.fn(() => []) }));
jest.mock('@/lib/seo', () => ({ getFreshnessLabel: jest.fn(() => 'Hoje') }));
jest.mock('@/components/seo/MicroDemo', () => ({ MicroDemo: () => null }));
jest.mock('@/components/seo/MicroDemoSchema', () => ({ MicroDemoSchema: () => null }));
jest.mock('@/lib/programmatic', () => ({ UF_NAMES: { SP: 'São Paulo' } }));

const { getSectorBySlug, fetchSectorStats } = require('@/lib/sectors');

const MOCK_SECTOR = { id: 'saude', name: 'Saúde', slug: 'saude', description: 'Setor de saúde' };

describe('licitacoes/[setor] generateMetadata — STORY-430 AC2', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    getSectorBySlug.mockReturnValue(MOCK_SECTOR);
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna robots noindex quando total_open < 5 (default threshold)', async () => {
    fetchSectorStats.mockResolvedValue({ total_open: 3, top_ufs: [], avg_value: 0 });
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'saude' }) });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots noindex quando total_open = 0', async () => {
    fetchSectorStats.mockResolvedValue({ total_open: 0, top_ufs: [], avg_value: 0 });
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'saude' }) });
    expect(meta.robots).toEqual({ index: false, follow: false });
  });

  it('retorna robots index:true quando total_open >= 5', async () => {
    fetchSectorStats.mockResolvedValue({
      total_open: 10,
      top_ufs: [{ name: 'São Paulo' }],
      avg_value: 150000,
    });
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'saude' }) });
    expect((meta.robots as any)?.index).toBe(true);
  });

  it('respeita MIN_ACTIVE_BIDS_FOR_INDEX env var customizado', async () => {
    process.env.MIN_ACTIVE_BIDS_FOR_INDEX = '10';
    fetchSectorStats.mockResolvedValue({ total_open: 7, top_ufs: [], avg_value: 0 });
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'saude' }) });
    // 7 < 10 → noindex
    expect(meta.robots).toEqual({ index: false, follow: false });
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna title de fallback no caso noindex', async () => {
    fetchSectorStats.mockResolvedValue({ total_open: 1, top_ufs: [], avg_value: 0 });
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'saude' }) });
    // STORY-450: "| SmartLic" removido do título noindex (já controlado pelo layout global)
    expect(meta.title).toContain('Saúde');
  });

  it('retorna 404 metadata para setor inválido', async () => {
    getSectorBySlug.mockReturnValue(null);
    const meta = await generateMetadata({ params: Promise.resolve({ setor: 'nao-existe' }) });
    expect(meta.title).toContain('não encontrado');
  });
});
