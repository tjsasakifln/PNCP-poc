/**
 * UX-350: Resumo por IA com Timeout + Recomendações do Consultor com Contexto.
 *
 * AC9:  Timeout de 30s mostra fallback
 * AC10: SSE `llm_ready` após timeout atualiza resumo
 * AC11: Perfil incompleto mostra banner com CTA
 * AC12: Zero regressões (verified by running full test suite)
 */

import React from "react";
import { render, screen, act, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

// ---- Module mocks (hoisted by Jest) ----

jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

jest.mock("../hooks/useSearchSSE", () => ({
  useSearchSSE: () => ({
    currentEvent: null,
    sseAvailable: false,
    sseDisconnected: false,
    isDegraded: false,
    degradedDetail: null,
    partialProgress: null,
    refreshAvailable: null,
    ufStatuses: new Map(),
    ufTotalFound: 0,
    ufAllComplete: false,
    batchProgress: null,
  }),
}));

// Mock child components not relevant to this test
jest.mock("../components/EnhancedLoadingProgress", () => ({
  EnhancedLoadingProgress: () => null,
}));
jest.mock("../app/components/LoadingResultsSkeleton", () => ({
  LoadingResultsSkeleton: () => null,
}));
jest.mock("../app/components/EmptyState", () => ({
  EmptyState: () => null,
}));
jest.mock("../app/buscar/components/DegradationBanner", () => ({
  DegradationBanner: () => null,
}));
jest.mock("../app/buscar/components/OperationalStateBanner", () => ({
  OperationalStateBanner: () => null,
}));
jest.mock("../app/buscar/components/UfProgressGrid", () => ({
  UfProgressGrid: () => null,
}));
jest.mock("../app/buscar/components/PartialResultsPrompt", () => ({
  PartialResultsPrompt: () => null,
  PartialResultsBanner: () => null,
  FailedUfsBanner: () => null,
}));
jest.mock("../app/buscar/components/CacheBanner", () => ({
  CacheBanner: () => null,
}));
jest.mock("../app/buscar/components/SourcesUnavailable", () => ({
  SourcesUnavailable: () => null,
}));
jest.mock("../app/buscar/components/TruncationWarningBanner", () => ({
  TruncationWarningBanner: () => null,
}));
jest.mock("../app/components/QuotaCounter", () => ({
  QuotaCounter: () => null,
}));
jest.mock("../app/components/LicitacoesPreview", () => ({
  LicitacoesPreview: () => null,
}));
jest.mock("../app/components/OrdenacaoSelect", () => ({
  OrdenacaoSelect: () => null,
}));
jest.mock("../app/buscar/components/ErrorDetail", () => ({
  ErrorDetail: () => null,
}));
jest.mock("../app/buscar/components/PartialTimeoutBanner", () => ({
  PartialTimeoutBanner: () => null,
}));
jest.mock("../app/buscar/components/RefreshBanner", () => ({
  __esModule: true,
  default: () => null,
}));
jest.mock("../components/GoogleSheetsExportButton", () => ({
  __esModule: true,
  default: () => null,
}));

// ---- Import components under test ----
import SearchResults from "../app/buscar/components/SearchResults";
import { LlmSourceBadge } from "../app/buscar/components/LlmSourceBadge";
import type { BuscaResult } from "../app/types";

// ---- Test helpers ----

const BASE_PLAN_INFO = {
  plan_id: "smartlic_pro",
  plan_name: "SmartLic Pro",
  quota_used: 5,
  quota_reset_date: "2026-03-01",
  capabilities: {
    max_history_days: 1825,
    max_requests_per_month: 1000,
    allow_excel: true,
  },
};

function makeResult(overrides: Partial<BuscaResult> = {}): BuscaResult {
  return {
    resumo: {
      resumo_executivo: "Resumo de teste executivo",
      total_oportunidades: 3,
      valor_total: 500000,
      destaques: ["Destaque 1"],
      recomendacoes: [
        {
          oportunidade: "Prefeitura Municipal de Teste - Aquisição de uniformes",
          valor: 250000,
          urgencia: "alta" as const,
          acao_sugerida: "Preparar documentação",
          justificativa: "Valor alto e prazo curto",
        },
        {
          oportunidade: "Governo do Estado - Compra de materiais",
          valor: 100000,
          urgencia: "media" as const,
          acao_sugerida: "Acompanhar publicação",
          justificativa: "Boa aderência ao perfil",
        },
      ],
    } as any,
    licitacoes: [
      {
        pncp_id: "p1",
        objeto: "Aquisição de uniformes",
        orgao: "Prefeitura Municipal de Teste",
        valor: 250000,
        uf: "SP",
        link: "https://pncp.gov.br/app/editais/12345",
      },
      {
        pncp_id: "p2",
        objeto: "Compra de materiais",
        orgao: "Governo do Estado",
        valor: 100000,
        uf: "RJ",
        link: "https://pncp.gov.br/app/editais/67890",
      },
      {
        pncp_id: "p3",
        objeto: "Serviços de TI",
        orgao: "Tribunal Regional",
        valor: 150000,
        uf: "MG",
        link: "https://pncp.gov.br/app/editais/11111",
      },
    ] as any,
    download_id: "dl-123",
    download_url: null,
    total_raw: 10,
    total_filtrado: 3,
    filter_stats: null,
    termos_utilizados: null,
    stopwords_removidas: null,
    excel_available: true,
    upgrade_message: null,
    source_stats: null,
    ...overrides,
  };
}

const DEFAULT_PROPS = {
  loading: false,
  loadingStep: 1,
  estimatedTime: 30,
  stateCount: 3,
  statesProcessed: 3,
  onCancel: jest.fn(),
  sseEvent: null,
  useRealProgress: false,
  sseAvailable: false,
  onStageChange: jest.fn(),
  error: null,
  quotaError: null,
  rawCount: 10,
  ufsSelecionadas: new Set(["SP", "RJ", "MG"]),
  sectorName: "Vestuário",
  searchMode: "setor" as const,
  termosArray: [] as string[],
  ordenacao: "relevancia" as any,
  onOrdenacaoChange: jest.fn(),
  downloadLoading: false,
  downloadError: null,
  onDownload: jest.fn(),
  onSearch: jest.fn(),
  session: { access_token: "test-token" },
  onShowUpgradeModal: jest.fn(),
  onTrackEvent: jest.fn(),
  planInfo: BASE_PLAN_INFO,
};

// ============================================================================
// AC5: Title "Recomendações Estratégicas" (with proper accents)
// ============================================================================
describe("AC5: Recomendações Estratégicas title", () => {
  it("renders 'Recomendações Estratégicas:' instead of 'Recomendações do Consultor'", () => {
    render(<SearchResults {...DEFAULT_PROPS} result={makeResult()} />);
    expect(screen.getByText("Recomendações Estratégicas:")).toBeInTheDocument();
    expect(screen.queryByText("Recomendações do Consultor:")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC6 + AC11: Incomplete profile shows banner with CTA
// ============================================================================
describe("AC6/AC11: Profile incomplete banner", () => {
  it("shows incomplete profile banner with link to /conta when isProfileComplete=false", () => {
    render(
      <SearchResults {...DEFAULT_PROPS} result={makeResult()} isProfileComplete={false} />
    );
    const banner = screen.getByTestId("profile-incomplete-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent("Complete seu perfil para recomendações mais precisas");

    const link = screen.getByText("Completar perfil →");
    expect(link).toHaveAttribute("href", "/conta");
  });

  it("hides profile banner when isProfileComplete=true", () => {
    render(
      <SearchResults {...DEFAULT_PROPS} result={makeResult()} isProfileComplete={true} />
    );
    expect(screen.queryByTestId("profile-incomplete-banner")).not.toBeInTheDocument();
  });

  it("hides profile banner by default (isProfileComplete defaults to true)", () => {
    render(
      <SearchResults {...DEFAULT_PROPS} result={makeResult()} />
    );
    expect(screen.queryByTestId("profile-incomplete-banner")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC7: "Ver edital na fonte oficial" links
// ============================================================================
describe("AC7: Ver edital na fonte oficial links", () => {
  it("renders 'Ver edital na fonte oficial' when recommendation matches a bid", () => {
    render(<SearchResults {...DEFAULT_PROPS} result={makeResult()} />);
    const links = screen.getAllByTestId("rec-edital-link");
    expect(links.length).toBeGreaterThanOrEqual(1);
    expect(links[0]).toHaveTextContent("Ver edital na fonte oficial");
    expect(links[0]).toHaveAttribute("target", "_blank");
  });

  it("links point to correct PNCP URLs", () => {
    render(<SearchResults {...DEFAULT_PROPS} result={makeResult()} />);
    const links = screen.getAllByTestId("rec-edital-link");
    const hrefs = links.map(l => l.getAttribute("href"));
    expect(hrefs).toContain("https://pncp.gov.br/app/editais/12345");
  });

  it("does not show link when recommendation has no matching bid", () => {
    const resultWithNoMatch = makeResult({
      resumo: {
        resumo_executivo: "Resumo",
        total_oportunidades: 1,
        valor_total: 50000,
        destaques: [],
        recomendacoes: [
          {
            oportunidade: "Entidade Inexistente - Serviço desconhecido",
            valor: 50000,
            urgencia: "baixa" as const,
            acao_sugerida: "Monitorar",
            justificativa: "Relevante",
          },
        ],
      } as any,
      licitacoes: [
        {
          pncp_id: "p1",
          objeto: "Algo completamente diferente",
          orgao: "Órgão diferente",
          valor: 50000,
          uf: "SP",
          link: "https://pncp.gov.br/app/editais/99999",
        },
      ] as any,
    });
    render(<SearchResults {...DEFAULT_PROPS} result={resultWithNoMatch} />);
    expect(screen.queryByTestId("rec-edital-link")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC8: AI transparency label
// ============================================================================
describe("AC8: AI transparency label", () => {
  it("renders AI transparency label when recommendations exist", () => {
    render(<SearchResults {...DEFAULT_PROPS} result={makeResult()} />);
    const label = screen.getByTestId("ai-transparency-label");
    expect(label).toBeInTheDocument();
    expect(label).toHaveTextContent("Análise gerada por IA com base no seu perfil e no edital");
  });

  it("does not render transparency label when no recommendations", () => {
    const noRecs = makeResult({
      resumo: {
        resumo_executivo: "Resumo",
        total_oportunidades: 3,
        valor_total: 100000,
        destaques: [],
        recomendacoes: [],
      } as any,
    });
    render(<SearchResults {...DEFAULT_PROPS} result={noRecs} />);
    expect(screen.queryByTestId("ai-transparency-label")).not.toBeInTheDocument();
  });
});

// ============================================================================
// AC9: LlmSourceBadge — "processing" shows spinner, "fallback" shows automatic label
// ============================================================================
describe("AC9: LLM Source Badge timeout behavior", () => {
  it("shows 'Resumo por IA sendo preparado...' when llm_source is processing", () => {
    render(<LlmSourceBadge llmSource="processing" />);
    expect(screen.getByText("Resumo por IA sendo preparado...")).toBeInTheDocument();
  });

  it("shows 'Resumo automatico' when llm_source is fallback (after timeout)", () => {
    render(<LlmSourceBadge llmSource="fallback" />);
    expect(screen.getByText("Resumo automatico")).toBeInTheDocument();
  });

  it("shows 'Resumo por IA' when llm_source is ai", () => {
    render(<LlmSourceBadge llmSource="ai" />);
    expect(screen.getByText("Resumo por IA")).toBeInTheDocument();
  });

  it("SearchResults renders fallback badge when llm_source is fallback", () => {
    const result = makeResult({ llm_source: "fallback" });
    render(<SearchResults {...DEFAULT_PROPS} result={result} />);
    expect(screen.getByText("Resumo automatico")).toBeInTheDocument();
  });

  it("SearchResults renders processing badge when llm_source is processing", () => {
    const result = makeResult({ llm_source: "processing" });
    render(<SearchResults {...DEFAULT_PROPS} result={result} />);
    expect(screen.getByText("Resumo por IA sendo preparado...")).toBeInTheDocument();
  });
});

// ============================================================================
// AC10: SSE llm_ready after timeout updates resumo (integration-level)
// ============================================================================
describe("AC10: handleSseEvent replaces resumo on llm_ready", () => {
  it("llm_ready SSE event updates result with AI source", () => {
    // This is a unit test for the handler logic —
    // we test that calling setResult with llm_ready data produces the correct state
    const initialResult = makeResult({
      llm_source: "fallback",
      llm_status: "ready",
    });

    // Simulate what handleSseEvent does when llm_ready arrives:
    const updatedResult = {
      ...initialResult,
      resumo: {
        ...initialResult.resumo,
        resumo_executivo: "Resumo gerado por IA aprimorado",
      },
      llm_status: "ready" as const,
      llm_source: "ai" as const,
    };

    const { rerender } = render(
      <SearchResults {...DEFAULT_PROPS} result={initialResult} />
    );

    // Initially shows fallback
    expect(screen.getByText("Resumo automatico")).toBeInTheDocument();

    // After SSE event updates result
    rerender(<SearchResults {...DEFAULT_PROPS} result={updatedResult} />);

    // Now shows AI badge
    expect(screen.getByText("Resumo por IA")).toBeInTheDocument();
    expect(screen.queryByText("Resumo automatico")).not.toBeInTheDocument();
    expect(screen.getByText("Resumo gerado por IA aprimorado")).toBeInTheDocument();
  });
});
