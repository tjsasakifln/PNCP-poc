/**
 * UX-352: Reduzir Carga Cognitiva — Badges, Alertas e Hierarquia Visual
 *
 * Tests:
 * - AC13: "FONTE OFICIAL" and "Palavra-chave" badges do NOT render
 * - AC14: Relevância badge with correct accentuation
 * - AC8: Expand/collapse details on bid cards
 * - AC9: Technical jargon removed
 * - AC10: Cache banner uses user-friendly language
 * - AC11: Return invitation message
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LicitacoesPreview } from "../app/components/LicitacoesPreview";
import type { LicitacaoItem } from "../app/types";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => (
    <a href={href} {...props}>{children}</a>
  );
});

// Mock AuthProvider (required by AddToPipelineButton via usePipeline)
jest.mock("../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: "u1", email: "test@test.com" },
    session: { access_token: "test-token" },
    loading: false,
    signOut: jest.fn(),
  }),
}));

function makeBid(overrides: Partial<LicitacaoItem> = {}): LicitacaoItem {
  return {
    pncp_id: `bid-${Math.random().toString(36).slice(2, 8)}`,
    objeto: "Aquisição de uniformes escolares para rede municipal",
    orgao: "Prefeitura Municipal de São Paulo",
    uf: "SP",
    municipio: "São Paulo",
    valor: 250000,
    modalidade: "Pregão Eletrônico",
    data_abertura: "2026-02-15",
    data_encerramento: "2026-03-15",
    data_publicacao: "2026-02-10",
    situacao: "aberta",
    link: "https://pncp.gov.br/test",
    ...overrides,
  } as LicitacaoItem;
}

describe("UX-352 AC13: Removed badges do NOT render", () => {
  it("'Fonte Oficial' badge is not rendered for PNCP source", () => {
    const bids = [makeBid({ _source: "PNCP" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.queryByText("Fonte Oficial")).not.toBeInTheDocument();
    expect(screen.queryByText(/FONTE OFICIAL/i)).not.toBeInTheDocument();
  });

  it("'Fonte Oficial' badge is not rendered for any source", () => {
    const bids = [
      makeBid({ _source: "PNCP", pncp_id: "b1" }),
      makeBid({ _source: "COMPRAS_GOV", pncp_id: "b2" }),
      makeBid({ _source: "PORTAL_COMPRAS", pncp_id: "b3" }),
    ];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.queryByText("Fonte Oficial")).not.toBeInTheDocument();
    expect(screen.queryByText("ComprasGov")).not.toBeInTheDocument();
    expect(screen.queryByText("Portal")).not.toBeInTheDocument();
  });

  it("'Palavra-chave' badge is not rendered for keyword source", () => {
    const bids = [makeBid({ relevance_source: "keyword" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.queryByText("Palavra-chave")).not.toBeInTheDocument();
  });

  it("'Palavra-chave' badge absent across all items with keyword source", () => {
    const bids = [
      makeBid({ relevance_source: "keyword", pncp_id: "k1" }),
      makeBid({ relevance_source: "keyword", pncp_id: "k2" }),
      makeBid({ relevance_source: "keyword", pncp_id: "k3" }),
    ];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.queryByText("Palavra-chave")).not.toBeInTheDocument();
  });
});

describe("UX-352 AC14: Relevância badge with correct accentuation", () => {
  it("high confidence renders 'Alta relevância' (with accent)", () => {
    const bids = [makeBid({ confidence: "high" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByText("Alta relevância")).toBeInTheDocument();
    // Old text should NOT appear
    expect(screen.queryByText("Alta confianca")).not.toBeInTheDocument();
    expect(screen.queryByText("Alta confiança")).not.toBeInTheDocument();
  });

  it("medium confidence renders 'Relevância média' (with accents)", () => {
    const bids = [makeBid({ confidence: "medium" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByText("Relevância média")).toBeInTheDocument();
    // Old text should NOT appear
    expect(screen.queryByText("Confianca media")).not.toBeInTheDocument();
  });

  it("low confidence still renders 'Avaliado por IA'", () => {
    const bids = [makeBid({ confidence: "low" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByText("Avaliado por IA")).toBeInTheDocument();
  });

  it("high confidence has correct aria-label with accents", () => {
    const bids = [makeBid({ confidence: "high" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    const badge = screen.getByText("Alta relevância").closest("[aria-label]");
    expect(badge).toHaveAttribute("aria-label", "Relevância alta deste resultado para o seu perfil");
  });
});

describe("UX-352 AC4: Viability and prazo badges remain", () => {
  it("viability badge still renders", () => {
    const bids = [makeBid({ viability_level: "alta", viability_score: 80 })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByTestId("viability-badge")).toBeInTheDocument();
    expect(screen.getByText("Viabilidade alta")).toBeInTheDocument();
  });

  it("prazo/urgency badge still renders with days remaining", () => {
    const futureDate = new Date(Date.now() + 5 * 86400000).toISOString().split("T")[0];
    const bids = [makeBid({ data_encerramento: futureDate, dias_restantes: 5, urgencia: "critica" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByText(/Urgente/)).toBeInTheDocument();
  });
});

describe("UX-352 AC8: Expand/collapse details on bid cards", () => {
  it("shows 'Ver detalhes' button on each card", () => {
    const bids = [makeBid()];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    expect(screen.getByText("Ver detalhes")).toBeInTheDocument();
  });

  it("orgão is hidden by default (in collapsed section)", () => {
    const bids = [makeBid({ orgao: "Prefeitura Municipal de São Paulo" })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    // Orgão should not be visible until expanded
    expect(screen.queryByTestId("bid-details")).not.toBeInTheDocument();
  });

  it("clicking 'Ver detalhes' reveals orgão, modalidade, and dates", () => {
    const bids = [makeBid({
      orgao: "Secretaria de Educação de SP",
      modalidade: "Pregão Eletrônico",
      data_abertura: "2026-02-15",
    })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    // Click expand
    fireEvent.click(screen.getByText("Ver detalhes"));

    // Now details should be visible
    expect(screen.getByTestId("bid-details")).toBeInTheDocument();
    expect(screen.getByText("Secretaria de Educação de SP")).toBeInTheDocument();
    expect(screen.getByText("Pregão Eletrônico")).toBeInTheDocument();
    expect(screen.getByText("15/02/2026")).toBeInTheDocument();
  });

  it("clicking 'Ocultar detalhes' collapses the section", () => {
    const bids = [makeBid()];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    // Expand
    fireEvent.click(screen.getByText("Ver detalhes"));
    expect(screen.getByText("Ocultar detalhes")).toBeInTheDocument();

    // Collapse
    fireEvent.click(screen.getByText("Ocultar detalhes"));
    expect(screen.queryByTestId("bid-details")).not.toBeInTheDocument();
    expect(screen.getByText("Ver detalhes")).toBeInTheDocument();
  });

  it("essential info (title, value, UF, viability, prazo) visible without expanding", () => {
    const futureDate = new Date(Date.now() + 10 * 86400000).toISOString().split("T")[0];
    const bids = [makeBid({
      objeto: "Fornecimento de material escolar",
      valor: 500000,
      uf: "RJ",
      viability_level: "media",
      viability_score: 55,
      data_encerramento: futureDate,
      dias_restantes: 10,
      urgencia: "alta",
    })];
    render(
      <LicitacoesPreview
        licitacoes={bids}
        previewCount={5}
        excelAvailable={true}
        searchTerms={[]}
      />
    );

    // Title
    expect(screen.getByText("Fornecimento de material escolar")).toBeInTheDocument();
    // Value
    expect(screen.getByText(/500\.000/)).toBeInTheDocument();
    // UF
    expect(screen.getByText(/RJ/)).toBeInTheDocument();
    // Viability
    expect(screen.getByText("Viabilidade média")).toBeInTheDocument();
    // Prazo
    expect(screen.getByText(/Atenção/)).toBeInTheDocument();
  });
});
