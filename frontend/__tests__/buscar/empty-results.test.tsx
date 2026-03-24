/**
 * HARDEN-025 AC4: EmptyResults rendering tests.
 * Tests the EmptyResults component displays icon, message, and contextual suggestions.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { EmptyResults } from "../../app/buscar/components/EmptyResults";

describe("EmptyResults", () => {
  it("renders icon and friendly message (AC1)", () => {
    render(<EmptyResults />);
    expect(screen.getByTestId("empty-results")).toBeInTheDocument();
    expect(screen.getByText("Nenhum resultado compatível")).toBeInTheDocument();
    expect(screen.getByTestId("empty-results-message")).toBeInTheDocument();
  });

  it("shows contextual suggestions (AC2)", () => {
    render(<EmptyResults />);
    expect(screen.getByTestId("suggestion-remover-uf")).toBeInTheDocument();
    expect(screen.getByTestId("suggestion-termos-genericos")).toBeInTheDocument();
    expect(screen.getByText(/Remover filtros de UF/)).toBeInTheDocument();
    expect(screen.getByText(/Usar termos genéricos/)).toBeInTheDocument();
  });

  it("displays total_raw count when provided (filtered-out scenario)", () => {
    render(<EmptyResults totalRaw={150} sectorName="Tecnologia" />);
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(
      screen.getByText(/licitações, mas nenhuma passou nos filtros/)
    ).toBeInTheDocument();
    expect(screen.getByText("Tecnologia")).toBeInTheDocument();
  });

  it("displays fallback message when totalRaw is 0", () => {
    render(<EmptyResults totalRaw={0} sectorName="Saúde" ufCount={3} />);
    expect(screen.getByText(/Nenhuma licitação encontrada/)).toBeInTheDocument();
    expect(screen.getByText(/Saúde/)).toBeInTheDocument();
    expect(screen.getByText(/3 estados/)).toBeInTheDocument();
  });

  it("shows singular 'estado' for ufCount=1", () => {
    render(<EmptyResults totalRaw={0} ufCount={1} />);
    expect(screen.getByText(/1 estado/)).toBeInTheDocument();
  });

  it("renders adjust button when onScrollToTop provided", () => {
    const onScrollToTop = jest.fn();
    render(<EmptyResults onScrollToTop={onScrollToTop} />);
    const btn = screen.getByTestId("empty-results-adjust");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onScrollToTop).toHaveBeenCalledTimes(1);
  });

  it("hides adjust button when onScrollToTop not provided", () => {
    render(<EmptyResults />);
    expect(screen.queryByTestId("empty-results-adjust")).not.toBeInTheDocument();
  });

  it("renders without sectorName gracefully", () => {
    render(<EmptyResults totalRaw={50} />);
    expect(
      screen.getByText(/licitações, mas nenhuma passou nos filtros/)
    ).toBeInTheDocument();
    // Should not crash or show "undefined"
    expect(screen.queryByText("undefined")).not.toBeInTheDocument();
  });
});
