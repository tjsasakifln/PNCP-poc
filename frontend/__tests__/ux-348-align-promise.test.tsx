/**
 * UX-348: Alinhar promessa da landing page com entrega da area logada.
 *
 * AC13: Viability badge renders with correct data
 * AC14: Link to official source present in each card
 * AC15: Positive framing with correct counts
 * AC16: Zero regressions (verified by running full test suite)
 */

import React from "react";
import { render, screen, within } from "@testing-library/react";

// ---- Mocks ----
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

// Mock AddToPipelineButton — usePipeline now uses SWR + useAuth (TD-008)
jest.mock("../app/components/AddToPipelineButton", () => ({
  AddToPipelineButton: () => null,
}));

// ---- Component imports ----
import { LicitacoesPreview } from "../app/components/LicitacoesPreview";
import { SearchEmptyState as EmptyState } from "../app/buscar/components/SearchEmptyState";
import type { LicitacaoItem } from "../app/types";

// ---- Helpers ----
function makeBid(overrides: Partial<LicitacaoItem> = {}): LicitacaoItem {
  return {
    objeto: "Aquisicao de uniformes escolares",
    orgao: "Prefeitura Municipal de Teste",
    valor: 250000,
    uf: "SP",
    municipio: "São Paulo",
    modalidade: "Pregão Eletrônico",
    data_encerramento: "2026-03-15",
    data_abertura: "2026-02-20",
    dias_restantes: 21,
    urgencia: "media",
    pncp_id: "pncp-001",
    link: "https://pncp.gov.br/app/editais/12345",
    relevance_score: 0.8,
    relevance_source: "keyword",
    confidence: "high" as const,
    viability_level: "alta" as const,
    viability_score: 85,
    viability_factors: {
      modalidade: 100,
      modalidade_label: "Ótimo",
      timeline: 80,
      timeline_label: "21 dias",
      value_fit: 90,
      value_fit_label: "Ideal",
      geography: 100,
      geography_label: "Sua região",
    },
    _value_source: "estimated" as const,
    _source: "PNCP",
    matched_terms: ["uniformes"],
    ...overrides,
  } as LicitacaoItem;
}

// ============================================================================
// AC13: Viability badge renders with correct data
// ============================================================================
describe("AC13: Viability badge in result cards", () => {
  it("renders viability badge for each visible bid", () => {
    const bids = [
      makeBid({ viability_level: "alta", viability_score: 85 }),
      makeBid({ viability_level: "media", viability_score: 55, pncp_id: "pncp-002" }),
    ];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={["uniformes"]}
      />
    );
    const badges = screen.getAllByTestId("viability-badge");
    expect(badges.length).toBe(2);
    expect(badges[0]).toHaveTextContent("Viabilidade alta");
    expect(badges[1]).toHaveTextContent("Viabilidade média");
  });

  it("renders viability badge with factor tooltip", () => {
    const bid = makeBid({
      viability_level: "alta",
      viability_score: 95,
      viability_factors: {
        modalidade: 100, modalidade_label: "Ótimo",
        timeline: 80, timeline_label: "12 dias",
        value_fit: 100, value_fit_label: "Ideal",
        geography: 100, geography_label: "Sua região",
      },
    });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const badge = screen.getByTestId("viability-badge");
    const title = badge.getAttribute("title") || "";
    expect(title).toContain("95/100");
    expect(title).toContain("Modalidade");
    expect(title).toContain("Prazo");
    expect(title).toContain("Valor");
    expect(title).toContain("UF");
  });

  it("does NOT render viability badge when data is absent", () => {
    const bid = makeBid({
      viability_level: null,
      viability_score: null,
      viability_factors: null,
    });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    expect(screen.queryByTestId("viability-badge")).toBeNull();
  });

  it("renders viability badge in paid extra items (beyond previewCount)", () => {
    const bids = [
      makeBid({ pncp_id: "p1", viability_level: "alta", viability_score: 90 }),
      makeBid({ pncp_id: "p2", viability_level: "media", viability_score: 50 }),
      makeBid({ pncp_id: "p3", viability_level: "baixa", viability_score: 20 }),
    ];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={1}
        excelAvailable={true}
        searchTerms={[]}
      />
    );
    const badges = screen.getAllByTestId("viability-badge");
    // 1 visible + 2 paid extra = 3 badges
    expect(badges.length).toBe(3);
  });
});

// ============================================================================
// AC14: Link to official source in each card
// ============================================================================
describe("AC14: Official source link in result cards", () => {
  it("renders 'Ver edital completo' link for each bid with link", () => {
    const bids = [
      makeBid({ link: "https://pncp.gov.br/app/editais/123", pncp_id: "p1" }),
      makeBid({ link: "https://pncp.gov.br/app/editais/456", pncp_id: "p2" }),
    ];
    render(
      <LicitacoesPreview licitacoes={bids} previewCount={5} excelAvailable={true} />
    );
    const links = screen.getAllByTestId("link-edital");
    expect(links.length).toBe(2);
    expect(links[0]).toHaveTextContent("Ver edital");
    expect(links[0]).toHaveAttribute("href", "https://pncp.gov.br/app/editais/123");
  });

  it("link opens in new tab with noopener", () => {
    render(
      <LicitacoesPreview
        licitacoes={[makeBid()]}
        previewCount={5}
        excelAvailable={true}
      />
    );
    const link = screen.getByTestId("link-edital");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("does not render link when bid has no link", () => {
    const bid = makeBid({ link: undefined });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    expect(screen.queryByTestId("link-edital")).toBeNull();
  });
});

// ============================================================================
// AC15: Positive framing with correct counts
// ============================================================================
describe("AC15: Positive framing", () => {
  describe("EmptyState", () => {
    it("shows positive framing message with rawCount", () => {
      render(
        <EmptyState
          rawCount={150}
          stateCount={5}
          sectorName="uniformes"
        />
      );
      const msg = screen.getByTestId("empty-state-message");
      expect(msg.textContent).toContain("Analisamos 150 editais");
      expect(msg.textContent).toContain("nenhum correspondeu ao seu perfil");
      expect(msg.textContent).toContain("Volte amanhã");
    });

    it("shows positive framing when rawCount is 0", () => {
      render(
        <EmptyState rawCount={0} stateCount={3} sectorName="software" />
      );
      const msg = screen.getByTestId("empty-state-message");
      expect(msg.textContent).toContain("nenhum correspondeu ao seu perfil");
      expect(msg.textContent).toContain("Volte amanhã");
    });

    it("never shows 'eliminados' in the message", () => {
      render(
        <EmptyState
          rawCount={500}
          stateCount={27}
          sectorName="vestuário"
          filterStats={{
            rejeitadas_keyword: 300,
            rejeitadas_valor: 100,
            rejeitadas_uf: 50,
            rejeitadas_exclusion: 0,
            rejeitadas_status: 0,
            total_analisadas: 500,
            total_aprovadas: 0,
          } as any}
        />
      );
      const container = screen.getByTestId("empty-state-message");
      expect(container.textContent).not.toContain("eliminaram");
      expect(container.textContent).not.toContain("eliminados");
    });
  });
});

// ============================================================================
// AC11: Deadline color coding
// ============================================================================
describe("AC11: Deadline color coding", () => {
  it("shows red for bids with <8 days remaining", () => {
    const bid = makeBid({ dias_restantes: 5, urgencia: "critica", data_encerramento: "2026-02-27" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Urgente/);
    expect(urgencyBadge.className).toContain("bg-red-100");
  });

  it("shows yellow for bids with 8-15 days remaining", () => {
    const bid = makeBid({ dias_restantes: 10, urgencia: "alta", data_encerramento: "2026-03-04" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Atenção/);
    expect(urgencyBadge.className).toContain("bg-yellow-100");
  });

  it("shows green for bids with >15 days remaining", () => {
    const bid = makeBid({ dias_restantes: 20, urgencia: "media", data_encerramento: "2026-03-14" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Prazo final/);
    expect(urgencyBadge.className).toContain("bg-green-100");
  });

  it("shows green for bid with exactly 16 days", () => {
    const bid = makeBid({ dias_restantes: 16, urgencia: undefined as any, data_encerramento: "2026-03-10" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Prazo final/);
    expect(urgencyBadge.className).toContain("bg-green-100");
  });

  it("shows yellow for bid with exactly 15 days", () => {
    const bid = makeBid({ dias_restantes: 15, urgencia: undefined as any, data_encerramento: "2026-03-09" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Atenção/);
    expect(urgencyBadge.className).toContain("bg-yellow-100");
  });

  it("shows yellow for bid with exactly 8 days", () => {
    const bid = makeBid({ dias_restantes: 8, urgencia: undefined as any, data_encerramento: "2026-03-02" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Atenção/);
    expect(urgencyBadge.className).toContain("bg-yellow-100");
  });

  it("shows red for bid with exactly 7 days", () => {
    const bid = makeBid({ dias_restantes: 7, urgencia: undefined as any, data_encerramento: "2026-03-01" });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    const urgencyBadge = screen.getByText(/Urgente/);
    expect(urgencyBadge.className).toContain("bg-red-100");
  });

  it("formats value as R$ with thousands separator", () => {
    const bid = makeBid({ valor: 1500000 });
    render(
      <LicitacoesPreview licitacoes={[bid]} previewCount={5} excelAvailable={true} />
    );
    // UX-401 AC7: Now uses formatCurrencyBR with abbreviation for >= 1M
    expect(screen.getByText(/R\$\s*1,5\s*mi/)).toBeInTheDocument();
  });
});
