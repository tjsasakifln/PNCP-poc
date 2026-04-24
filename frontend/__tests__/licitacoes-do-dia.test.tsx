/**
 * Tests for /blog/licitacoes-do-dia pages (Wave 3.2)
 */
import React from 'react';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
  useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
  usePathname: () => '/blog/licitacoes-do-dia',
}));

jest.mock('@/app/components/landing/LandingNavbar', () => () => <nav data-testid="navbar" />);
jest.mock('@/app/components/Footer', () => () => <footer data-testid="footer" />);
jest.mock('@/components/LeadCapture', () => ({
  LeadCapture: ({ heading }: { heading: string }) => <div data-testid="lead-capture">{heading}</div>,
}));
jest.mock('@/lib/authors', () => ({
  getAuthorBySlug: () => ({ name: 'Test Author', role: 'Editor', sameAs: [] }),
  DEFAULT_AUTHOR_SLUG: 'test-author',
}));

describe('LicitacoesDoDiaHubPage', () => {
  it('exports revalidate = 3600', async () => {
    const mod = await import('@/app/blog/licitacoes-do-dia/page');
    expect(mod.revalidate).toBe(3600);
  });

  it('has metadata with correct title', async () => {
    const mod = await import('@/app/blog/licitacoes-do-dia/page');
    expect(mod.metadata.title).toContain('Licitacoes do Dia');
  });
});

describe('DailyDigestDetailPage', () => {
  it('exports revalidate = 3600', async () => {
    const mod = await import('@/app/blog/licitacoes-do-dia/[date]/page');
    expect(mod.revalidate).toBe(3600);
  });

  it('generateStaticParams returns empty array', async () => {
    const mod = await import('@/app/blog/licitacoes-do-dia/[date]/page');
    expect(mod.generateStaticParams()).toEqual([]);
  });

  it('generateMetadata returns title for valid data', async () => {
    const mockData = {
      date: '2026-04-08',
      title: '2026-04-08: 150 editais publicados, destaque Informatica',
      total_bids: 150,
      total_value: 5000000,
      avg_value: 33333,
      by_sector: [],
      by_uf: [],
      by_modalidade: [],
      highlights: [],
      top_sector: 'Informatica',
      top_uf: 'SP',
      updated_at: '2026-04-08T12:00:00Z',
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }) as jest.Mock;

    const mod = await import('@/app/blog/licitacoes-do-dia/[date]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ date: '2026-04-08' }),
    });

    expect(metadata.title).toContain('150 editais');
  });

  it('generateMetadata returns noindex+nofollow for invalid date', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
    }) as jest.Mock;

    const mod = await import('@/app/blog/licitacoes-do-dia/[date]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ date: 'invalid' }),
    });

    // STORY-SEO-017 AC3: nofollow tambem (era so noindex) — datas sem dados nunca
    // devem propagar autoridade nem ser re-crawled.
    expect(metadata.robots).toEqual({ index: false, follow: false });
  });

  it('generateMetadata returns 200+noindex (nao 404) para data valida sem bids', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
    }) as jest.Mock;

    const mod = await import('@/app/blog/licitacoes-do-dia/[date]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ date: '2026-03-26' }),
    });

    // STORY-SEO-017 AC3: data valida sem bids = noindex+nofollow + canonical
    // (anteriormente notFound() -> 404 -> 42 URLs penalizados no GSC).
    expect(metadata.title).toContain('Sem licitacoes publicadas em 2026-03-26');
    expect(metadata.robots).toEqual({ index: false, follow: false });
    expect((metadata.alternates as { canonical?: string })?.canonical).toContain('/blog/licitacoes-do-dia/2026-03-26');
  });
});
