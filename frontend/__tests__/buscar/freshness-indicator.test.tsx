/**
 * GTM-RESILIENCE-C03 AC11: FreshnessIndicator component tests
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { FreshnessIndicator, formatRelativeTimePtBr } from "../../app/buscar/components/FreshnessIndicator";

describe("FreshnessIndicator", () => {
  it('shows "Dados de agora" for live freshness', () => {
    render(
      <FreshnessIndicator
        timestamp={new Date().toISOString()}
        freshness="live"
      />
    );
    expect(screen.getByText("Dados de agora")).toBeInTheDocument();
    expect(screen.getByTestId("freshness-indicator")).toHaveAttribute(
      "aria-label",
      "Dados obtidos agora"
    );
  });

  it("shows relative time for cached_fresh", () => {
    const thirtyMinAgo = new Date(Date.now() - 30 * 60000).toISOString();
    render(
      <FreshnessIndicator
        timestamp={thirtyMinAgo}
        freshness="cached_fresh"
      />
    );
    expect(screen.getByText(/Dados de há 30 minutos/)).toBeInTheDocument();
  });

  it("shows relative time for cached_stale", () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 3600000).toISOString();
    render(
      <FreshnessIndicator
        timestamp={threeHoursAgo}
        freshness="cached_stale"
      />
    );
    expect(screen.getByText(/Dados de há 3 horas/)).toBeInTheDocument();
  });

  it('shows "Cache" when cacheBannerVisible and not live', () => {
    const oneHourAgo = new Date(Date.now() - 60 * 60000).toISOString();
    render(
      <FreshnessIndicator
        timestamp={oneHourAgo}
        freshness="cached_fresh"
        cacheBannerVisible={true}
      />
    );
    expect(screen.getByText("Cache")).toBeInTheDocument();
    expect(screen.queryByText(/Dados de/)).not.toBeInTheDocument();
  });

  it("shows full label when live even with cacheBannerVisible", () => {
    render(
      <FreshnessIndicator
        timestamp={new Date().toISOString()}
        freshness="live"
        cacheBannerVisible={true}
      />
    );
    expect(screen.getByText("Dados de agora")).toBeInTheDocument();
  });
});

describe("formatRelativeTimePtBr", () => {
  it('returns "agora" for just now', () => {
    expect(formatRelativeTimePtBr(new Date().toISOString())).toBe("agora");
  });

  it("returns minutes for < 1 hour", () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60000).toISOString();
    expect(formatRelativeTimePtBr(fiveMinAgo)).toBe("há 5 minutos");
  });

  it("returns hours for < 24 hours", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    expect(formatRelativeTimePtBr(twoHoursAgo)).toBe("há 2 horas");
  });

  it("returns days for >= 24 hours", () => {
    const twoDaysAgo = new Date(Date.now() - 48 * 3600000).toISOString();
    expect(formatRelativeTimePtBr(twoDaysAgo)).toBe("há 2 dias");
  });

  it("singular minute", () => {
    const oneMinAgo = new Date(Date.now() - 1 * 60000).toISOString();
    expect(formatRelativeTimePtBr(oneMinAgo)).toBe("há 1 minuto");
  });

  it("singular hour", () => {
    const oneHourAgo = new Date(Date.now() - 1 * 3600000).toISOString();
    expect(formatRelativeTimePtBr(oneHourAgo)).toBe("há 1 hora");
  });
});
