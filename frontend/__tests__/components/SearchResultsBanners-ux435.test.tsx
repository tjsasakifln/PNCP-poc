/**
 * UX-435: Banner "Atualizando dados em tempo real" nunca desaparece
 *
 * AC4: Testar banner de live-fetch com:
 *   - Busca que completa normalmente (banner some via SSE complete)
 *   - Busca que usa cache stale (banner presente enquanto live-fetch ocorre)
 *   - Timeout de 30s (liveFetchTimedOut=true → banner oculto)
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import type { BuscaResult } from "../../app/types";

// ─── Mocks ───────────────────────────────────────────────────────────────────

jest.mock("next/link", () => {
  return ({ href, children, ...props }: any) =>
    React.createElement("a", { href, ...props }, children);
});

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { variants, initial, animate, exit, transition, ...restProps } = props;
      return React.createElement("div", restProps, children);
    },
  },
  AnimatePresence: ({ children }: any) => children,
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

// Mock complex sub-banners so we only test the live-fetch banner logic
jest.mock("../../app/buscar/components/DataQualityBanner", () => ({
  DataQualityBanner: () => React.createElement("div", { "data-testid": "mock-data-quality-banner" }),
}));

jest.mock("../../app/buscar/components/FilterRelaxedBanner", () => ({
  FilterRelaxedBanner: () => React.createElement("div", { "data-testid": "mock-filter-relaxed-banner" }),
}));

jest.mock("../../app/buscar/components/RefreshBanner", () => ({
  default: () => React.createElement("div", { "data-testid": "mock-refresh-banner" }),
}));

// BannerStack renders all banners (simplified for testing)
jest.mock("../../app/buscar/components/BannerStack", () => ({
  BannerStack: ({ banners }: { banners: Array<{ id: string; content: React.ReactNode }> }) =>
    React.createElement(
      "div",
      { "data-testid": "banner-stack" },
      ...banners.map((b) => React.createElement("div", { key: b.id, "data-banner-id": b.id }, b.content))
    ),
}));

// ─── Fixtures ────────────────────────────────────────────────────────────────

const RESULT_MOCK: BuscaResult = {
  licitacoes: [
    {
      pncp_id: "test-1",
      numero_controle: "NC-001",
      objeto: "Aquisição de equipamentos de TI",
      orgao: "Prefeitura de São Paulo",
      uf: "SP",
      valor_estimado: 100000,
      data_abertura: "2026-05-01",
      data_publicacao: "2026-04-01",
      modalidade: "Pregão Eletrônico",
      modalidade_id: 6,
      situacao: "Em Andamento",
      status: "ativo",
      source: "PNCP",
      confidence: "high",
      setor_id: "tecnologia",
      relevance_score: 0.9,
    } as any,
  ],
  resumo: {
    total_oportunidades: 1,
    valor_total: 100000,
    por_modalidade: {},
    por_uf: {},
    por_setor: {},
  } as any,
  total_filtrado: 1,
  total_raw: 5,
  response_state: "fresh",
  cached: false,
  cached_at: null,
  cache_status: null,
  is_truncated: false,
  cache_fallback: false,
  cache_date_range: null,
  failed_ufs: [],
  sources_used: ["PNCP"],
  source_stats: [{ source_code: "PNCP", status: "success" }],
  sources_degraded: false,
  filter_relaxed: false,
  coverage_pct: 100,
  filter_stats: null,
} as unknown as BuscaResult;

// ─── Tests ───────────────────────────────────────────────────────────────────

import { SearchResultsBanners } from "../../app/buscar/components/SearchResultsBanners";

const defaultProps = {
  result: RESULT_MOCK,
  loading: false,
  ufsSelecionadas: new Set(["SP"]),
  onSearch: jest.fn(),
};

describe("UX-435: live-fetch banner visibility", () => {
  it("AC4a: mostra 'Buscando atualizações em segundo plano...' quando liveFetchInProgress=true", () => {
    render(
      <SearchResultsBanners
        {...defaultProps}
        liveFetchInProgress={true}
        liveFetchTimedOut={false}
      />
    );

    expect(
      screen.getByText("Buscando atualizações em segundo plano...")
    ).toBeInTheDocument();
  });

  it("AC4b: oculta banner quando liveFetchTimedOut=true (timeout de 30s expirou)", () => {
    render(
      <SearchResultsBanners
        {...defaultProps}
        liveFetchInProgress={true}
        liveFetchTimedOut={true}
      />
    );

    expect(
      screen.queryByText("Buscando atualizações em segundo plano...")
    ).not.toBeInTheDocument();
  });

  it("AC4c: banner ausente quando liveFetchInProgress=false (busca normal sem live-fetch)", () => {
    render(
      <SearchResultsBanners
        {...defaultProps}
        liveFetchInProgress={false}
        liveFetchTimedOut={false}
      />
    );

    expect(
      screen.queryByText("Buscando atualizações em segundo plano...")
    ).not.toBeInTheDocument();
  });

  it("AC4d: banner presente com cache stale + liveFetchInProgress=true", () => {
    const staleResult: BuscaResult = {
      ...RESULT_MOCK,
      cached: true,
      cached_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h atrás
      cache_status: "stale",
      response_state: "cached",
    } as unknown as BuscaResult;

    render(
      <SearchResultsBanners
        {...defaultProps}
        result={staleResult}
        liveFetchInProgress={true}
        liveFetchTimedOut={false}
      />
    );

    expect(
      screen.getByText("Buscando atualizações em segundo plano...")
    ).toBeInTheDocument();
  });

  it("AC4e: banner oculto quando loading=true (busca em andamento, resultado ainda não chegou)", () => {
    render(
      <SearchResultsBanners
        {...defaultProps}
        loading={true}
        liveFetchInProgress={true}
        liveFetchTimedOut={false}
      />
    );

    // Quando loading=true, o componente não mostra o live-fetch banner
    expect(
      screen.queryByText("Buscando atualizações em segundo plano...")
    ).not.toBeInTheDocument();
  });
});
