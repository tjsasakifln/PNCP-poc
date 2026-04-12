/**
 * STORY-439 AC1: Tests for thin content noindex gate in /orgaos/[slug]/page.tsx
 */

// Mock next/navigation
jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
}));

// Mock ContentPageLayout
jest.mock('@/app/components/ContentPageLayout', () => () => <div data-testid="layout" />);

// Mock OrgaoPerfilClient
jest.mock('@/app/orgaos/[slug]/OrgaoPerfilClient', () => () => <div data-testid="orgao-client" />);

// Mock LeadCapture
jest.mock('@/components/LeadCapture', () => ({
  LeadCapture: () => <div data-testid="lead-capture" />,
}));

const mockOrgaoStats = {
  nome: 'Secretaria Municipal de Saúde de São Paulo',
  cnpj: '46523056000100',
  esfera: 'municipal',
  uf: 'SP',
  municipio: 'São Paulo',
  total_licitacoes: 20,
  licitacoes_30d: 3,
  licitacoes_90d: 8,
  licitacoes_365d: 20,
  valor_medio_estimado: 250000,
  valor_total_estimado: 5000000,
  top_modalidades: [],
  top_setores: ['Saúde'],
  ultimas_licitacoes: [],
  aviso_legal: 'Dados públicos.',
};

describe('orgaos/[slug] — thin content noindex gate (STORY-439 AC1)', () => {
  beforeEach(() => {
    jest.resetModules();
    delete process.env.MIN_ACTIVE_BIDS_FOR_INDEX;
  });

  it('retorna noindex quando stats é null (órgão não encontrado)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-inexistente' }),
    });

    expect(metadata.robots).toEqual({ index: false, follow: false });
  });

  it('retorna noindex quando total_licitacoes < threshold padrão (5)', async () => {
    const sparseStats = { ...mockOrgaoStats, total_licitacoes: 3 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(sparseStats),
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-sparse' }),
    });

    expect(metadata.robots).toEqual({ index: false, follow: true });
    expect(metadata.title).toContain(sparseStats.nome);
  });

  it('retorna noindex quando total_licitacoes === 0', async () => {
    const emptyStats = { ...mockOrgaoStats, total_licitacoes: 0 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(emptyStats),
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-empty' }),
    });

    expect(metadata.robots).toEqual({ index: false, follow: true });
  });

  it('permite indexação quando total_licitacoes >= threshold padrão (5)', async () => {
    const richStats = { ...mockOrgaoStats, total_licitacoes: 10 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(richStats),
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-rico' }),
    });

    // Quando indexável, robots não deve ser { index: false }
    expect(metadata.robots).toBeUndefined();
    expect(metadata.title).toContain(richStats.nome);
  });

  it('respeita threshold customizado via MIN_ACTIVE_BIDS_FOR_INDEX', async () => {
    process.env.MIN_ACTIVE_BIDS_FOR_INDEX = '10';

    const mediumStats = { ...mockOrgaoStats, total_licitacoes: 7 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mediumStats),
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-medium' }),
    });

    // 7 < 10 → noindex
    expect(metadata.robots).toEqual({ index: false, follow: true });
  });

  it('retorna metadata completa com title e description quando indexável', async () => {
    const richStats = { ...mockOrgaoStats, total_licitacoes: 20 };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(richStats),
    }) as jest.Mock;

    const mod = await import('@/app/orgaos/[slug]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ slug: 'orgao-rico' }),
    });

    expect(metadata.title).toContain(richStats.nome);
    expect(metadata.description).toContain('20 licitações');
    expect(metadata.robots).toBeUndefined();
  });
});
