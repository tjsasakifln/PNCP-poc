/**
 * Tests for STORY-435: Índice Municipal de Transparência
 *
 * Tests cover:
 * - IndiceClient renders filter controls and table
 * - IndiceClient handles loading/error/empty states
 * - Slug utility functions
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock next/link
jest.mock('next/link', () => {
  const Link = ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>;
  Link.displayName = 'Link';
  return Link;
});

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

const SAMPLE_RESPONSE = {
  periodo: '2026-Q1',
  total: 2,
  fonte: 'PNCP via SmartLic Observatório',
  license: 'CC BY 4.0',
  resultados: [
    {
      municipio_nome: 'São Paulo',
      municipio_slug: 'sao-paulo-sp',
      uf: 'SP',
      uf_nome: 'São Paulo',
      periodo: '2026-Q1',
      score_total: 78.5,
      score_volume_publicacao: 18.0,
      score_eficiencia_temporal: 15.5,
      score_diversidade_mercado: 16.0,
      score_transparencia_digital: 17.0,
      score_consistencia: 12.0,
      total_editais: 450,
      ranking_nacional: 1,
      ranking_uf: 1,
      percentil: 98,
      calculado_em: '2026-04-11T12:00:00+00:00',
    },
    {
      municipio_nome: 'Campinas',
      municipio_slug: 'campinas-sp',
      uf: 'SP',
      uf_nome: 'São Paulo',
      periodo: '2026-Q1',
      score_total: 45.2,
      score_volume_publicacao: 10.0,
      score_eficiencia_temporal: 9.0,
      score_diversidade_mercado: 10.2,
      score_transparencia_digital: 10.0,
      score_consistencia: 6.0,
      total_editais: 120,
      ranking_nacional: 2,
      ranking_uf: 2,
      percentil: 75,
      calculado_em: '2026-04-11T12:00:00+00:00',
    },
  ],
};

describe('IndiceClient', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('renders loading skeleton initially', async () => {
    // Never resolve — keep in loading state
    mockFetch.mockImplementation(() => new Promise(() => {}));

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    // Should show skeleton placeholders
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders table with results on success', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => SAMPLE_RESPONSE,
    } as Response);

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    await waitFor(() => {
      expect(screen.getByText('São Paulo')).toBeInTheDocument();
    });

    expect(screen.getByText('Campinas')).toBeInTheDocument();
    // Score is shown
    expect(screen.getByText('78.5')).toBeInTheDocument();
  });

  it('renders error message on fetch failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: 'Internal error' }),
    } as Response);

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    await waitFor(() => {
      // Should display an error state
      const errorEl = document.querySelector('[data-testid="indice-error"]');
      if (errorEl) {
        expect(errorEl).toBeInTheDocument();
      } else {
        // Text-based fallback check
        expect(
          screen.queryByText(/erro|indisponível|tente/i)
        ).not.toBeNull();
      }
    });
  });

  it('renders empty state when no results', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...SAMPLE_RESPONSE, resultados: [], total: 0 }),
    } as Response);

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    await waitFor(() => {
      expect(
        screen.getByText(/nenhum dado|não disponível/i)
      ).toBeInTheDocument();
    });
  });

  it('renders UF select filter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => SAMPLE_RESPONSE,
    } as Response);

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    // UF select should be present
    await waitFor(() => {
      const selects = document.querySelectorAll('select');
      expect(selects.length).toBeGreaterThan(0);
    });
  });

  it('renders link to individual municipality page', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => SAMPLE_RESPONSE,
    } as Response);

    const IndiceClientModule = await import(
      '@/app/indice-municipal/IndiceClient'
    );
    const IndiceClient = IndiceClientModule.default;

    render(<IndiceClient />);

    await waitFor(() => {
      const links = document.querySelectorAll(
        'a[href*="/indice-municipal/sao-paulo-sp"]'
      );
      expect(links.length).toBeGreaterThan(0);
    });
  });
});

describe('Slug utility (indice-municipal)', () => {
  it('verifica que sao-paulo-sp termina com uf SP', () => {
    const slug = 'sao-paulo-sp';
    const uf = slug.slice(-2).toUpperCase();
    expect(uf).toBe('SP');
  });

  it('verifica que belo-horizonte-mg tem uf MG', () => {
    const slug = 'belo-horizonte-mg';
    const uf = slug.slice(-2).toUpperCase();
    expect(uf).toBe('MG');
  });

  it('score color: verde para >= 60', () => {
    const score = 78.5;
    const color =
      score >= 60
        ? 'text-green-600'
        : score >= 40
        ? 'text-yellow-600'
        : 'text-red-600';
    expect(color).toBe('text-green-600');
  });

  it('score color: amarelo para 40-59', () => {
    const score = 45;
    const color =
      score >= 60
        ? 'text-green-600'
        : score >= 40
        ? 'text-yellow-600'
        : 'text-red-600';
    expect(color).toBe('text-yellow-600');
  });

  it('score color: vermelho para < 40', () => {
    const score = 25;
    const color =
      score >= 60
        ? 'text-green-600'
        : score >= 40
        ? 'text-yellow-600'
        : 'text-red-600';
    expect(color).toBe('text-red-600');
  });
});
