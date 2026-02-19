/**
 * GTM-RESILIENCE-A01 AC12: Frontend test for empty_failure rendering.
 *
 * Verifies that when response_state === "empty_failure", the SourcesUnavailable
 * component renders "Fontes temporariamente indisponíveis" (not "Nenhuma oportunidade").
 */

import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { SourcesUnavailable } from "@/app/buscar/components/SourcesUnavailable";

describe("GTM-RESILIENCE-A01 AC12: empty_failure rendering", () => {
  const defaultProps = {
    onRetry: jest.fn(),
    onLoadLastSearch: jest.fn(),
    hasLastSearch: false,
    retrying: false,
  };

  it("renders 'Fontes temporariamente indisponíveis' title", () => {
    render(<SourcesUnavailable {...defaultProps} />);

    expect(
      screen.getByText("Fontes temporariamente indisponíveis")
    ).toBeInTheDocument();
  });

  it("does NOT render 'Nenhuma oportunidade encontrada'", () => {
    render(<SourcesUnavailable {...defaultProps} />);

    expect(
      screen.queryByText(/Nenhuma.*[Oo]portunidade/i)
    ).not.toBeInTheDocument();
  });

  it("shows backend degradation_guidance when provided", () => {
    const guidance =
      "Fontes de dados governamentais estão temporariamente indisponíveis. " +
      "Tente novamente em alguns minutos ou reduza o número de estados.";

    render(
      <SourcesUnavailable {...defaultProps} degradationGuidance={guidance} />
    );

    expect(screen.getByText(guidance)).toBeInTheDocument();
  });

  it("shows default subtitle when no degradation_guidance", () => {
    render(<SourcesUnavailable {...defaultProps} />);

    expect(
      screen.getByText(/geralmente se resolve em poucos minutos/i)
    ).toBeInTheDocument();
  });

  it("renders 'Tentar novamente' button with 30s cooldown", () => {
    render(<SourcesUnavailable {...defaultProps} />);

    const retryButton = screen.getByRole("button", {
      name: /Tentar novamente/i,
    });
    expect(retryButton).toBeInTheDocument();
    // Initial state has 30s cooldown
    expect(retryButton).toBeDisabled();
  });

  it("renders 'Ver última busca salva' button", () => {
    render(<SourcesUnavailable {...defaultProps} hasLastSearch={true} />);

    expect(
      screen.getByRole("button", { name: /última busca salva/i })
    ).toBeInTheDocument();
  });

  it("disables 'Ver última busca salva' when no saved search", () => {
    render(<SourcesUnavailable {...defaultProps} hasLastSearch={false} />);

    const btn = screen.getByRole("button", { name: /última busca salva/i });
    expect(btn).toBeDisabled();
  });
});
