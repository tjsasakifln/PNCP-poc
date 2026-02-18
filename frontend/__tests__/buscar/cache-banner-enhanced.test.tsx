/**
 * UX-303 AC5+AC10: Enhanced CacheBanner tests — fresh/stale distinction.
 *
 * Covers:
 *   - Green styling for fresh cache
 *   - Amber styling for stale cache
 *   - No refresh button for fresh cache
 *   - Refresh button present for stale cache
 *   - Cache status data attribute
 *   - Source names display
 *   - Backward compatibility (no cacheStatus prop)
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CacheBanner } from "../../app/buscar/components/CacheBanner";

describe("CacheBanner — UX-303 Enhanced", () => {
  const baseProps = {
    cachedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
    onRefresh: jest.fn(),
    refreshing: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // === Fresh cache tests ===

  it("shows green styling for fresh cache", () => {
    render(<CacheBanner {...baseProps} cacheStatus="fresh" />);
    const alert = screen.getByTestId("cache-banner");
    expect(alert.className).toContain("green");
  });

  it("shows checkmark icon for fresh cache", () => {
    render(
      <CacheBanner {...baseProps} cacheStatus="fresh" cachedSources={["PNCP"]} />
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/Cache atualizado/);
  });

  it("does NOT show refresh button for fresh cache", () => {
    render(<CacheBanner {...baseProps} cacheStatus="fresh" />);
    expect(screen.queryByText("Tentar atualizar")).not.toBeInTheDocument();
  });

  it("sets data-cache-status=fresh", () => {
    render(<CacheBanner {...baseProps} cacheStatus="fresh" />);
    const banner = screen.getByTestId("cache-banner");
    expect(banner).toHaveAttribute("data-cache-status", "fresh");
  });

  // === Stale cache tests ===

  it("shows amber styling for stale cache", () => {
    render(<CacheBanner {...baseProps} cacheStatus="stale" />);
    const alert = screen.getByTestId("cache-banner");
    expect(alert.className).toContain("amber");
  });

  it("shows warning text for stale cache", () => {
    render(
      <CacheBanner {...baseProps} cacheStatus="stale" cachedSources={["PNCP"]} />
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/desatualizados/);
  });

  it("shows refresh button for stale cache", () => {
    render(<CacheBanner {...baseProps} cacheStatus="stale" />);
    expect(screen.getByText("Tentar atualizar")).toBeInTheDocument();
  });

  it("calls onRefresh when button clicked (stale)", () => {
    const onRefresh = jest.fn();
    render(<CacheBanner {...baseProps} cacheStatus="stale" onRefresh={onRefresh} />);
    fireEvent.click(screen.getByText("Tentar atualizar"));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("sets data-cache-status=stale", () => {
    render(<CacheBanner {...baseProps} cacheStatus="stale" />);
    const banner = screen.getByTestId("cache-banner");
    expect(banner).toHaveAttribute("data-cache-status", "stale");
  });

  // === Backward compatibility ===

  it("defaults to stale (amber) when cacheStatus not provided", () => {
    render(<CacheBanner {...baseProps} />);
    const alert = screen.getByTestId("cache-banner");
    expect(alert.className).toContain("amber");
    expect(alert).toHaveAttribute("data-cache-status", "stale");
  });

  it("shows refresh button when cacheStatus not provided", () => {
    render(<CacheBanner {...baseProps} />);
    expect(screen.getByText("Tentar atualizar")).toBeInTheDocument();
  });

  // === Source names ===

  it("shows multiple source names", () => {
    render(
      <CacheBanner
        {...baseProps}
        cacheStatus="stale"
        cachedSources={["PNCP", "PORTAL_COMPRAS"]}
      />
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      /PNCP \+ Portal de Compras Públicas/
    );
  });

  it("shows generic text when no sources", () => {
    render(<CacheBanner {...baseProps} />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /Nossas fontes estão temporariamente lentas/
    );
  });

  // === Refreshing state ===

  it("disables button and shows spinner when refreshing", () => {
    render(<CacheBanner {...baseProps} cacheStatus="stale" refreshing={true} />);
    expect(screen.getByText("Atualizando...")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
