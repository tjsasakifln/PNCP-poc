/**
 * GTM-FIX-010 AC13: Tests for CacheBanner (StaleCacheBanner) component.
 *
 * Covers:
 *   - Banner renders when cached results are served
 *   - Source names displayed (AC8 revised)
 *   - Relative time formatting
 *   - "Tentar atualizar" button (AC9)
 *   - Disabled state during refresh
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CacheBanner } from "../../app/buscar/components/CacheBanner";

describe("CacheBanner (GTM-FIX-010)", () => {
  const defaultProps = {
    cachedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
    onRefresh: jest.fn(),
    refreshing: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the cache warning banner", () => {
    render(<CacheBanner {...defaultProps} />);
    const alert = screen.getByRole("alert");
    expect(alert).toBeInTheDocument();
  });

  it("shows relative time (e.g. 'há 2 horas')", () => {
    render(<CacheBanner {...defaultProps} />);
    // The banner should show relative time — "há 2 horas" in pt-BR
    expect(screen.getByRole("alert")).toHaveTextContent(/há/);
  });

  it('shows "Tentar atualizar" button (AC9)', () => {
    render(<CacheBanner {...defaultProps} />);
    expect(screen.getByText("Tentar atualizar")).toBeInTheDocument();
  });

  it("calls onRefresh when button is clicked", () => {
    const onRefresh = jest.fn();
    render(<CacheBanner {...defaultProps} onRefresh={onRefresh} />);
    fireEvent.click(screen.getByText("Tentar atualizar"));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('shows "Atualizando..." when refreshing', () => {
    render(<CacheBanner {...defaultProps} refreshing={true} />);
    expect(screen.getByText("Atualizando...")).toBeInTheDocument();
  });

  it("disables button during refresh", () => {
    render(<CacheBanner {...defaultProps} refreshing={true} />);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("shows source names when cachedSources is provided (AC8r)", () => {
    render(
      <CacheBanner
        {...defaultProps}
        cachedSources={["PNCP", "PORTAL_COMPRAS"]}
      />
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /PNCP \+ Portal de Compras Públicas/
    );
  });

  it("shows single source name", () => {
    render(
      <CacheBanner {...defaultProps} cachedSources={["PNCP"]} />
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/\(PNCP\)/);
  });

  it("shows generic text when no cachedSources", () => {
    render(<CacheBanner {...defaultProps} />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Nossas fontes estão temporariamente lentas/
    );
  });

  it("shows 'desatualizados' warning", () => {
    render(<CacheBanner {...defaultProps} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/desatualizados/);
  });

  it("has amber styling for warning appearance", () => {
    render(<CacheBanner {...defaultProps} />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("amber");
  });
});
