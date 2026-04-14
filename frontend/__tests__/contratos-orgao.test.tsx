/**
 * Tests for /contratos/orgao/[cnpj] page (Wave 2.3)
 */
import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
  useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
  usePathname: () => '/contratos/orgao/99999999000100',
}));

// Mock LeadCapture
jest.mock('@/components/LeadCapture', () => ({
  LeadCapture: ({ heading }: { heading: string }) => <div data-testid="lead-capture">{heading}</div>,
}));

// Mock LandingNavbar + Footer
jest.mock('@/app/components/landing/LandingNavbar', () => () => <nav data-testid="navbar" />);
jest.mock('@/app/components/Footer', () => () => <footer data-testid="footer" />);

describe('OrgaoContratosPage types and structure', () => {
  it('exports revalidate = 14400 (4h ISR, reduzido de 24h no SEO-hotfix)', async () => {
    const mod = await import('@/app/contratos/orgao/[cnpj]/page');
    expect(mod.revalidate).toBe(14400);
  });

  it('generateStaticParams returns empty array', async () => {
    const mod = await import('@/app/contratos/orgao/[cnpj]/page');
    expect(mod.generateStaticParams()).toEqual([]);
  });

  it('generateMetadata returns title for valid stats', async () => {
    const mockStats = {
      orgao_nome: 'Secretaria de Educacao',
      orgao_cnpj: '99999999000100',
      total_contracts: 50,
      total_value: 5000000,
      avg_value: 100000,
      top_fornecedores: [],
      monthly_trend: [],
      sample_contracts: [],
      last_updated: '2026-04-08T12:00:00Z',
      aviso_legal: 'Dados publicos.',
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockStats),
    }) as jest.Mock;

    const mod = await import('@/app/contratos/orgao/[cnpj]/page');
    const metadata = await mod.generateMetadata({
      params: Promise.resolve({ cnpj: '99999999000100' }),
    });

    expect(metadata.title).toContain('Secretaria de Educacao');
  });
});
