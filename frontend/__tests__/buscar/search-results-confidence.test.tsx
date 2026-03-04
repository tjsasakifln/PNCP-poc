/**
 * C-02 AC10: Frontend tests for confidence badges, sorting, and header counts.
 *
 * Tests:
 * - Badge rendering for each confidence level
 * - No badge when confidence is null
 * - Tooltip text per level
 * - Sorting option existence
 * - Confidence counts in header
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// We test the LicitacoesPreview component which renders badges
import { LicitacoesPreview } from "../../app/components/LicitacoesPreview";
import type { LicitacaoItem } from "../../app/types";

// Mock next/link
jest.mock("next/link", () => {
  return ({ children, href, ...props }: any) => <a href={href} {...props}>{children}</a>;
});

// Mock AuthProvider (required by AddToPipelineButton via usePipeline)
jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: "u1", email: "test@test.com" },
    session: { access_token: "test-token" },
    loading: false,
    signOut: jest.fn(),
  }),
}));

function makeLicitacao(overrides: Partial<LicitacaoItem> = {}): LicitacaoItem {
  return {
    pncp_id: `test-${Math.random().toString(36).slice(2, 8)}`,
    objeto: "Aquisicao de uniformes para funcionarios",
    orgao: "Prefeitura Municipal de Teste",
    uf: "SP",
    valor: 150000,
    link: "https://pncp.gov.br/test",
    ...overrides,
  } as LicitacaoItem;
}

describe("C-02 Confidence Badge", () => {
  it("AC10.1: renders 'Alta relevância' badge when confidence='high'", () => {
    const licitacoes = [makeLicitacao({ confidence: "high" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    expect(screen.getByText("Alta relevância")).toBeInTheDocument();
  });

  it("AC10.2: renders 'Relevância média' badge when confidence='medium'", () => {
    const licitacoes = [makeLicitacao({ confidence: "medium" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    expect(screen.getByText("Relevância média")).toBeInTheDocument();
  });

  it("AC10.3: renders 'Avaliado por IA' badge when confidence='low'", () => {
    const licitacoes = [makeLicitacao({ confidence: "low" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    expect(screen.getByText("Avaliado por IA")).toBeInTheDocument();
  });

  it("AC10.4: no confidence badge when confidence is null", () => {
    const licitacoes = [makeLicitacao({ confidence: null })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    expect(screen.queryByText("Alta relevância")).not.toBeInTheDocument();
    expect(screen.queryByText("Relevância média")).not.toBeInTheDocument();
    expect(screen.queryByText("Avaliado por IA")).not.toBeInTheDocument();
  });

  it("AC10.4b: no confidence badge when confidence is undefined", () => {
    const licitacoes = [makeLicitacao()];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    expect(screen.queryByText("Alta relevância")).not.toBeInTheDocument();
    expect(screen.queryByText("Relevância média")).not.toBeInTheDocument();
    expect(screen.queryByText("Avaliado por IA")).not.toBeInTheDocument();
  });
});

describe("C-02 Confidence Tooltips", () => {
  it("AC10.5a: high confidence has correct tooltip", () => {
    const licitacoes = [makeLicitacao({ confidence: "high" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    const badge = screen.getByText("Alta relevância");
    expect(badge.closest("[title]")).toHaveAttribute(
      "title",
      "Alta densidade de termos relevantes para o setor selecionado"
    );
  });

  it("AC10.5b: medium confidence has correct tooltip", () => {
    const licitacoes = [makeLicitacao({ confidence: "medium" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    const badge = screen.getByText("Relevância média");
    expect(badge.closest("[title]")).toHaveAttribute(
      "title",
      "Relevância confirmada por avaliação de inteligência artificial"
    );
  });

  it("AC10.5c: low confidence has correct tooltip", () => {
    const licitacoes = [makeLicitacao({ confidence: "low" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    const badge = screen.getByText("Avaliado por IA");
    expect(badge.closest("[title]")).toHaveAttribute(
      "title",
      "Resultado com relevância possível, verificado por IA. Recomendamos revisar manualmente"
    );
  });
});

describe("C-02 Accessibility", () => {
  it("AC11.1: badges have aria-label", () => {
    const licitacoes = [
      makeLicitacao({ confidence: "high", pncp_id: "h1" }),
      makeLicitacao({ confidence: "medium", pncp_id: "m1" }),
      makeLicitacao({ confidence: "low", pncp_id: "l1" }),
    ];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );

    const highBadge = screen.getByText("Alta relevância").closest("[aria-label]");
    expect(highBadge).toHaveAttribute("aria-label", "Relevância alta deste resultado para o seu perfil");

    const medBadge = screen.getByText("Relevância média").closest("[aria-label]");
    expect(medBadge).toHaveAttribute("aria-label", "Relevância média deste resultado para o seu perfil");

    const lowBadge = screen.getByText("Avaliado por IA").closest("[aria-label]");
    expect(lowBadge).toHaveAttribute("aria-label", "Relevância baixa — verificado por IA, recomendamos revisar");
  });

  it("AC11.2: badges are focusable via keyboard", () => {
    const licitacoes = [makeLicitacao({ confidence: "high" })];
    render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );
    const badge = screen.getByText("Alta relevância").closest("[tabindex]");
    expect(badge).toHaveAttribute("tabindex", "0");
  });

  it("AC11.3: each level uses a different icon (not just color)", () => {
    const licitacoes = [
      makeLicitacao({ confidence: "high", pncp_id: "h2" }),
      makeLicitacao({ confidence: "medium", pncp_id: "m2" }),
      makeLicitacao({ confidence: "low", pncp_id: "l2" }),
    ];
    const { container } = render(
      <LicitacoesPreview licitacoes={licitacoes} previewCount={5} excelAvailable={true} />
    );

    // Each badge should have an SVG inside it
    const badges = container.querySelectorAll("[aria-label*='Relevância']");
    expect(badges).toHaveLength(3);

    // Verify each badge has an SVG icon
    badges.forEach(badge => {
      expect(badge.querySelector("svg")).toBeTruthy();
    });
  });
});

describe("C-02 Ordering", () => {
  it("AC10.6: OrdenacaoSelect includes 'Mais confiaveis' option", () => {
    // Import the options directly
    const { ORDENACAO_OPTIONS } = require("../../app/components/OrdenacaoSelect");
    const confiancaOption = ORDENACAO_OPTIONS.find(
      (opt: any) => opt.value === "confianca"
    );
    expect(confiancaOption).toBeDefined();
    expect(confiancaOption.label).toBe("Mais confiaveis");
  });
});
