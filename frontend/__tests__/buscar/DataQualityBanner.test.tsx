/**
 * GTM-UX-001: Comprehensive tests for the unified DataQualityBanner component.
 *
 * Covers:
 *   T1-T5: Required story acceptance criteria tests
 *   Severity priority logic (AC4): error > warning > info
 *   Badges (AC5-AC7): UFs expand, freshness, sources
 *   Action button (AC8): retry / refresh / spinner
 *   Render null: when nothing to report
 *   Message format (AC2): pipe-separated segments
 *   Accessibility: ARIA attributes, roles
 */
import React from "react";
import { render, screen, fireEvent, within, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DataQualityBanner, DataQualityBannerProps } from "../../app/buscar/components/DataQualityBanner";

// ============================================================================
// Base props factory
// ============================================================================

const createBaseProps = (
  overrides: Partial<DataQualityBannerProps> = {}
): DataQualityBannerProps => ({
  totalUfs: 7,
  succeededUfs: 7,
  failedUfs: [],
  isCached: false,
  cachedAt: null,
  cacheStatus: undefined,
  isTruncated: false,
  sourcesTotal: 1,
  sourcesAvailable: 1,
  sourceNames: ["PNCP"],
  responseState: "live",
  coveragePct: 100,
  onRefresh: jest.fn(),
  onRetry: jest.fn(),
  loading: false,
  ...overrides,
});

// ============================================================================
// T1-T5: Required story acceptance criteria
// ============================================================================

describe("DataQualityBanner -- GTM-UX-001 Story Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("T1: shows '5/7 estados' when 2 UFs fail", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent("5/7 estados");
  });

  it("T2: shows cache age when data is stale", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: twoHoursAgo,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toHaveTextContent(/Cache de 2h/);
    expect(screen.getByText("Atualizar")).toBeInTheDocument();
  });

  it("T3: renders only 1 banner even with multiple issues", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
      isTruncated: true,
      isCached: true,
      cachedAt: twoHoursAgo,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    const banners = screen.getAllByTestId("data-quality-banner");
    expect(banners).toHaveLength(1);

    // With failedUfs > 0, severity should be warning, and since failedUfs exist
    // the action button should show "Tentar novamente" (error/failedUfs path)
    expect(screen.getByText("Tentar novamente")).toBeInTheDocument();
  });

  it("T4: 'Atualizar' button triggers onRefresh", () => {
    const onRefresh = jest.fn();
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: twoHoursAgo,
      cacheStatus: "stale",
      onRefresh,
    });
    render(<DataQualityBanner {...props} />);

    fireEvent.click(screen.getByText("Atualizar"));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it("T5: mobile compact layout with badges in horizontal scroll", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date(Date.now() - 60000).toISOString(),
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    const badgesRow = screen.getByTestId("badges-row");
    expect(badgesRow.className).toContain("overflow-x-auto");
    expect(badgesRow.className).toContain("flex-nowrap");
  });
});

// ============================================================================
// Severity Priority (AC4)
// ============================================================================

describe("DataQualityBanner -- Severity Priority (AC4)", () => {
  it("error severity when responseState is 'empty_failure'", () => {
    const props = createBaseProps({
      responseState: "empty_failure",
      succeededUfs: 3,
      totalUfs: 7,
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // Error uses red styling
    expect(banner.className).toContain("red");
  });

  it("error severity when succeededUfs is 0", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 0,
      failedUfs: ["SP", "RJ", "MG", "BA", "PR", "RS", "SC"],
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("red");
  });

  it("warning severity when failedUfs > 0 (but not total failure)", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("amber");
  });

  it("warning severity when isTruncated is true", () => {
    const props = createBaseProps({
      isTruncated: true,
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("amber");
  });

  it("warning severity when cache is stale", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date(Date.now() - 3600000).toISOString(),
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("amber");
  });

  it("info severity when something to report but no issues (fresh cache)", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date().toISOString(),
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("blue");
  });

  it("error takes priority over warning conditions", () => {
    const props = createBaseProps({
      responseState: "empty_failure",
      failedUfs: ["SP"],
      totalUfs: 7,
      succeededUfs: 6,
      isTruncated: true,
      isCached: true,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // Error (red) should win over warning (amber)
    expect(banner.className).toContain("red");
    expect(banner.className).not.toMatch(/\bamber\b/);
  });

  it("warning takes priority over info conditions", () => {
    const props = createBaseProps({
      isTruncated: true,
      isCached: true,
      cachedAt: new Date().toISOString(),
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("amber");
  });
});

// ============================================================================
// Badges (AC5-AC7)
// ============================================================================

describe("DataQualityBanner -- Badges", () => {
  describe("UFs badge (AC5)", () => {
    it("displays X/Y estados count", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 5,
        failedUfs: ["SP", "RJ"],
      });
      render(<DataQualityBanner {...props} />);

      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent("5/7 estados");
    });

    it("shows expand panel with failed UF details on click", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 5,
        failedUfs: ["SP", "RJ"],
      });
      render(<DataQualityBanner {...props} />);

      // Click the UFs badge button to expand
      const ufsButton = screen.getByLabelText(
        /5 de 7 estados processados/
      );
      fireEvent.click(ufsButton);

      // Detail panel should now be visible
      const detailPanel = screen.getByRole("region", {
        name: /Detalhes de estados com falha/,
      });
      expect(detailPanel).toBeInTheDocument();
      expect(detailPanel).toHaveTextContent("SP (timeout)");
      expect(detailPanel).toHaveTextContent("RJ (timeout)");
      expect(detailPanel).toHaveTextContent("Estados com falha (2)");
    });

    it("toggles expand panel closed on second click", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 5,
        failedUfs: ["SP", "RJ"],
      });
      render(<DataQualityBanner {...props} />);

      const ufsButton = screen.getByLabelText(/5 de 7 estados processados/);

      // Open
      fireEvent.click(ufsButton);
      expect(
        screen.getByRole("region", { name: /Detalhes de estados com falha/ })
      ).toBeInTheDocument();

      // Close
      fireEvent.click(ufsButton);
      expect(
        screen.queryByRole("region", { name: /Detalhes de estados com falha/ })
      ).not.toBeInTheDocument();
    });

    it("sets aria-expanded attribute correctly", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 5,
        failedUfs: ["SP", "RJ"],
      });
      render(<DataQualityBanner {...props} />);

      const ufsButton = screen.getByLabelText(/5 de 7 estados processados/);
      expect(ufsButton).toHaveAttribute("aria-expanded", "false");

      fireEvent.click(ufsButton);
      expect(ufsButton).toHaveAttribute("aria-expanded", "true");
    });

    it("does not show detail panel when failedUfs is empty even if expanded", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 7,
        failedUfs: [],
        isCached: true,
        cachedAt: new Date().toISOString(),
        cacheStatus: "fresh",
      });
      render(<DataQualityBanner {...props} />);

      const ufsButton = screen.getByLabelText(/7 de 7 estados processados/);
      fireEvent.click(ufsButton);

      // No detail panel because failedUfs is empty
      expect(
        screen.queryByRole("region", { name: /Detalhes de estados com falha/ })
      ).not.toBeInTheDocument();
    });

    it("closes detail panel on Escape key", () => {
      const props = createBaseProps({
        totalUfs: 7,
        succeededUfs: 5,
        failedUfs: ["SP", "RJ"],
      });
      render(<DataQualityBanner {...props} />);

      const ufsButton = screen.getByLabelText(/5 de 7 estados processados/);
      fireEvent.click(ufsButton);

      expect(
        screen.getByRole("region", { name: /Detalhes de estados com falha/ })
      ).toBeInTheDocument();

      // Press Escape
      fireEvent.keyDown(document, { key: "Escape" });
      expect(
        screen.queryByRole("region", { name: /Detalhes de estados com falha/ })
      ).not.toBeInTheDocument();
    });
  });

  describe("Freshness badge (AC6)", () => {
    it("shows 'Dados em tempo real' when not cached", () => {
      const props = createBaseProps({
        isCached: true,
        cachedAt: new Date().toISOString(),
        cacheStatus: "fresh",
      });
      render(<DataQualityBanner {...props} />);

      // The freshness badge should show "Dados em tempo real" for very recent data
      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent("Dados em tempo real");
    });

    it("shows relative time for older cached data", () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
      const props = createBaseProps({
        isCached: true,
        cachedAt: twoHoursAgo,
        cacheStatus: "stale",
      });
      render(<DataQualityBanner {...props} />);

      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent(/Dados de 2h/);
    });

    it("shows 'Dados em tempo real' when isCached is false", () => {
      const props = createBaseProps({
        isCached: false,
        isTruncated: true, // Need something to report so banner renders
      });
      render(<DataQualityBanner {...props} />);

      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent("Dados em tempo real");
    });
  });

  describe("Sources badge (AC7)", () => {
    it("shows correct source count", () => {
      const props = createBaseProps({
        sourcesTotal: 2,
        sourcesAvailable: 1,
        sourceNames: ["PNCP", "Portal Compras"],
      });
      render(<DataQualityBanner {...props} />);

      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent("1/2 fontes");
    });

    it("shows source names tooltip on click", () => {
      const props = createBaseProps({
        sourcesTotal: 2,
        sourcesAvailable: 1,
        sourceNames: ["PNCP", "Portal Compras"],
      });
      render(<DataQualityBanner {...props} />);

      const sourcesButton = screen.getByLabelText(
        /1 de 2 fontes disponíveis/
      );
      fireEvent.click(sourcesButton);

      const tooltip = screen.getByRole("tooltip");
      expect(tooltip).toBeInTheDocument();
      expect(tooltip).toHaveTextContent("Fontes de dados:");
      expect(tooltip).toHaveTextContent("PNCP");
      expect(tooltip).toHaveTextContent("Portal Compras");
    });

    it("closes sources tooltip on Escape", () => {
      const props = createBaseProps({
        sourcesTotal: 2,
        sourcesAvailable: 1,
        sourceNames: ["PNCP", "Portal Compras"],
      });
      render(<DataQualityBanner {...props} />);

      const sourcesButton = screen.getByLabelText(/1 de 2 fontes disponíveis/);
      fireEvent.click(sourcesButton);
      expect(screen.getByRole("tooltip")).toBeInTheDocument();

      fireEvent.keyDown(document, { key: "Escape" });
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    });

    it("shows 1/1 fontes for single source", () => {
      const props = createBaseProps({
        sourcesTotal: 1,
        sourcesAvailable: 1,
        sourceNames: ["PNCP"],
        isCached: true,
        cachedAt: new Date().toISOString(),
        cacheStatus: "fresh",
      });
      render(<DataQualityBanner {...props} />);

      const badgesRow = screen.getByTestId("badges-row");
      expect(badgesRow).toHaveTextContent("1/1 fontes");
    });
  });
});

// ============================================================================
// Action Button (AC8)
// ============================================================================

describe("DataQualityBanner -- Action Button (AC8)", () => {
  it("shows 'Tentar novamente' on error severity", () => {
    const props = createBaseProps({
      responseState: "empty_failure",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByText("Tentar novamente")).toBeInTheDocument();
  });

  it("shows 'Tentar novamente' when failedUfs > 0 (even if warning severity)", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByText("Tentar novamente")).toBeInTheDocument();
  });

  it("calls onRetry when 'Tentar novamente' is clicked", () => {
    const onRetry = jest.fn();
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
      onRetry,
    });
    render(<DataQualityBanner {...props} />);

    fireEvent.click(screen.getByText("Tentar novamente"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("shows 'Atualizar' on stale cache (no failedUfs)", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date(Date.now() - 3600000).toISOString(),
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByText("Atualizar")).toBeInTheDocument();
  });

  it("shows spinner and 'Tentando...' when loading with error/failedUfs", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
      loading: true,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByText("Tentando...")).toBeInTheDocument();
    // The action button is disabled; find it by its text content
    const actionButton = screen.getByText("Tentando...").closest("button")!;
    expect(actionButton).toBeDisabled();
  });

  it("shows spinner and 'Atualizando...' when loading with stale cache", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date(Date.now() - 3600000).toISOString(),
      cacheStatus: "stale",
      loading: true,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByText("Atualizando...")).toBeInTheDocument();
    const actionButton = screen.getByText("Atualizando...").closest("button")!;
    expect(actionButton).toBeDisabled();
  });

  it("does not show action button when info severity and no stale cache", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date().toISOString(),
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.queryByRole("button", { name: /Atualizar/i })).not.toBeInTheDocument();
    expect(screen.queryByText("Tentar novamente")).not.toBeInTheDocument();
  });

  it("'Tentar novamente' takes priority over 'Atualizar' when both conditions apply", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP"],
      isCached: true,
      cachedAt: new Date(Date.now() - 3600000).toISOString(),
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    // failedUfs causes isError=true, so "Tentar novamente" wins
    expect(screen.getByText("Tentar novamente")).toBeInTheDocument();
    expect(screen.queryByText("Atualizar")).not.toBeInTheDocument();
  });
});

// ============================================================================
// Render null
// ============================================================================

describe("DataQualityBanner -- Render null", () => {
  it("returns null when nothing to report (all OK, not cached, not truncated)", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 7,
      failedUfs: [],
      isCached: false,
      isTruncated: false,
      sourcesTotal: 1,
      sourcesAvailable: 1,
      responseState: "live",
      coveragePct: 100,
    });
    const { container } = render(<DataQualityBanner {...props} />);

    expect(container.firstChild).toBeNull();
    expect(screen.queryByTestId("data-quality-banner")).not.toBeInTheDocument();
  });

  it("renders when isCached is true (even with fresh status)", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: new Date().toISOString(),
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("renders when sourcesAvailable < sourcesTotal", () => {
    const props = createBaseProps({
      sourcesTotal: 2,
      sourcesAvailable: 1,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("renders when responseState is 'degraded'", () => {
    const props = createBaseProps({
      responseState: "degraded",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("renders when coveragePct < 100", () => {
    const props = createBaseProps({
      coveragePct: 80,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("renders when isTruncated is true", () => {
    const props = createBaseProps({
      isTruncated: true,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });

  it("renders when failedUfs has items", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 6,
      failedUfs: ["SP"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toBeInTheDocument();
  });
});

// ============================================================================
// Message format (AC2)
// ============================================================================

describe("DataQualityBanner -- Message Format (AC2)", () => {
  it("shows pipe-separated message with correct segments", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
      isCached: true,
      cachedAt: twoHoursAgo,
      cacheStatus: "stale",
      isTruncated: true,
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // Segments: "Resultados de 5/7 estados | Cache de 2h atras | 2 timeouts | Resultados truncados"
    expect(banner).toHaveTextContent(/Resultados de 5\/7 estados/);
    expect(banner).toHaveTextContent(/Cache de 2h/);
    expect(banner).toHaveTextContent(/2 timeouts/);
    expect(banner).toHaveTextContent(/Resultados truncados/);
  });

  it("contains 'Resultados de X/Y estados' when UFs are partial", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 4,
      failedUfs: ["SP", "RJ", "MG"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "Resultados de 4/7 estados"
    );
  });

  it("does not show UFs segment when all succeeded", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 7,
      failedUfs: [],
      isTruncated: true, // Need something to report
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // Should NOT contain the UFs segment in the primary message
    expect(banner).not.toHaveTextContent(/Resultados de 7\/7 estados/);
  });

  it("shows singular 'timeout' for 1 failed UF", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 6,
      failedUfs: ["SP"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "1 timeout"
    );
    // Should not be "1 timeouts"
    expect(screen.getByTestId("data-quality-banner")).not.toHaveTextContent(
      "1 timeouts"
    );
  });

  it("shows plural 'timeouts' for 2+ failed UFs", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "2 timeouts"
    );
  });

  it("shows sources segment when not all sources available", () => {
    const props = createBaseProps({
      sourcesTotal: 3,
      sourcesAvailable: 2,
      sourceNames: ["PNCP", "Portal Compras", "DOU"],
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "2/3 fontes"
    );
  });

  it("does not show sources segment when all sources available", () => {
    const props = createBaseProps({
      sourcesTotal: 1,
      sourcesAvailable: 1,
      isTruncated: true, // Need something to report
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // The primary message should not contain the sources segment
    // (Note: the badges row still shows "1/1 fontes" but not in the primary message)
    const primaryMessage = banner.querySelector("p");
    expect(primaryMessage?.textContent).not.toMatch(/1\/1 fontes/);
  });

  it("shows 'Resultados truncados' in message when isTruncated", () => {
    const props = createBaseProps({
      isTruncated: true,
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "Resultados truncados"
    );
  });

  it("shows cache relative time with correct format for minutes", () => {
    const thirtyMinAgo = new Date(Date.now() - 30 * 60000).toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: thirtyMinAgo,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      /Cache de 30min/
    );
  });

  it("shows cache relative time with correct format for days", () => {
    const twoDaysAgo = new Date(Date.now() - 48 * 3600000).toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: twoDaysAgo,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      /Cache de 2d/
    );
  });

  it("shows 'Dados em tempo real' in message when cached just now", () => {
    const justNow = new Date().toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: justNow,
      cacheStatus: "fresh",
    });
    render(<DataQualityBanner {...props} />);

    expect(screen.getByTestId("data-quality-banner")).toHaveTextContent(
      "Dados em tempo real"
    );
  });
});

// ============================================================================
// Accessibility
// ============================================================================

describe("DataQualityBanner -- Accessibility", () => {
  it("has role='status' for assistive technology", () => {
    const props = createBaseProps({ isTruncated: true });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toHaveAttribute("role", "status");
  });

  it("has aria-live='polite' for screen readers", () => {
    const props = createBaseProps({ isTruncated: true });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toHaveAttribute("aria-live", "polite");
  });

  it("UFs badge has appropriate aria-label", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    const ufsButton = screen.getByLabelText(
      "5 de 7 estados processados. Clique para detalhes."
    );
    expect(ufsButton).toBeInTheDocument();
  });

  it("Sources badge has appropriate aria-label", () => {
    const props = createBaseProps({
      sourcesTotal: 2,
      sourcesAvailable: 1,
      sourceNames: ["PNCP", "Portal Compras"],
    });
    render(<DataQualityBanner {...props} />);

    const sourcesButton = screen.getByLabelText(
      "1 de 2 fontes disponíveis"
    );
    expect(sourcesButton).toBeInTheDocument();
  });

  it("Freshness badge has aria-label with freshness description", () => {
    const twoHoursAgo = new Date(Date.now() - 2 * 3600000).toISOString();
    const props = createBaseProps({
      isCached: true,
      cachedAt: twoHoursAgo,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    const freshnessBadge = screen.getByLabelText(/Dados de 2h/);
    expect(freshnessBadge).toBeInTheDocument();
  });

  it("UFs detail panel has id matching aria-controls", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    const ufsButton = screen.getByLabelText(/5 de 7 estados processados/);
    expect(ufsButton).toHaveAttribute("aria-controls", "uf-detail-panel");

    fireEvent.click(ufsButton);
    const panel = document.getElementById("uf-detail-panel");
    expect(panel).toBeInTheDocument();
  });
});

// ============================================================================
// Glass morphism and responsive styling (AC13, AC15)
// ============================================================================

describe("DataQualityBanner -- Styling", () => {
  it("applies glass morphism classes", () => {
    const props = createBaseProps({ isTruncated: true });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("backdrop-blur-md");
    expect(banner.className).toContain("shadow-lg");
  });

  it("applies responsive padding classes (p-3 sm:p-4)", () => {
    const props = createBaseProps({ isTruncated: true });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("p-3");
    expect(banner.className).toContain("sm:p-4");
  });

  it("applies fade-in animation class", () => {
    const props = createBaseProps({ isTruncated: true });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("animate-fade-in-up");
  });
});

// ============================================================================
// Edge cases
// ============================================================================

describe("DataQualityBanner -- Edge Cases", () => {
  it("handles empty sourceNames array for tooltip", () => {
    const props = createBaseProps({
      sourcesTotal: 2,
      sourcesAvailable: 1,
      sourceNames: [],
    });
    render(<DataQualityBanner {...props} />);

    const sourcesButton = screen.getByLabelText(/1 de 2 fontes disponíveis/);
    fireEvent.click(sourcesButton);

    // Tooltip should not render when sourceNames is empty
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("handles undefined sourceNames for tooltip", () => {
    const props = createBaseProps({
      sourcesTotal: 2,
      sourcesAvailable: 1,
      sourceNames: undefined,
    });
    render(<DataQualityBanner {...props} />);

    const sourcesButton = screen.getByLabelText(/1 de 2 fontes disponíveis/);
    fireEvent.click(sourcesButton);

    // Tooltip should not render when sourceNames is undefined
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("handles 0 totalUfs without crashing", () => {
    const props = createBaseProps({
      totalUfs: 0,
      succeededUfs: 0,
      failedUfs: [],
      // Need responseState to trigger hasAnythingToReport since failedUfs=[] and isCached=false
      responseState: "empty_failure",
    });
    // succeededUfs === 0 triggers error severity via deriveSeverity
    // This test ensures no division by zero or crash
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toBeInTheDocument();
    // Badges row shows "0/0 estados"
    const badgesRow = screen.getByTestId("badges-row");
    expect(badgesRow).toHaveTextContent("0/0 estados");
  });

  it("handles cachedAt as null with isCached true", () => {
    const props = createBaseProps({
      isCached: true,
      cachedAt: null,
      cacheStatus: "stale",
    });
    render(<DataQualityBanner {...props} />);

    // Should render banner but not crash on null cachedAt
    const banner = screen.getByTestId("data-quality-banner");
    expect(banner).toBeInTheDocument();
  });

  it("handles all UFs failing gracefully", () => {
    const allUfs = ["AC", "AL", "AM", "AP", "BA", "CE", "DF"];
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 0,
      failedUfs: allUfs,
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    expect(banner.className).toContain("red"); // error severity
    expect(banner).toHaveTextContent("Resultados de 0/7 estados");
    expect(banner).toHaveTextContent("7 timeouts");
  });

  it("renders correctly with only truncation flagged", () => {
    const props = createBaseProps({
      isTruncated: true,
    });
    render(<DataQualityBanner {...props} />);

    const banner = screen.getByTestId("data-quality-banner");
    // Primary message only has truncation segment
    const primaryMessage = banner.querySelector("p");
    expect(primaryMessage).toHaveTextContent("Resultados truncados");
    // Primary message should NOT have UFs segment (since all succeeded)
    expect(primaryMessage?.textContent).not.toMatch(/Resultados de/);
    // Badges row still shows "7/7 estados" (that's expected)
  });

  it("closes UFs popover on outside click", () => {
    const props = createBaseProps({
      totalUfs: 7,
      succeededUfs: 5,
      failedUfs: ["SP", "RJ"],
    });
    render(<DataQualityBanner {...props} />);

    const ufsButton = screen.getByLabelText(/5 de 7 estados processados/);
    fireEvent.click(ufsButton);

    expect(
      screen.getByRole("region", { name: /Detalhes de estados com falha/ })
    ).toBeInTheDocument();

    // Click outside (on document body)
    fireEvent.mouseDown(document.body);

    expect(
      screen.queryByRole("region", { name: /Detalhes de estados com falha/ })
    ).not.toBeInTheDocument();
  });

  it("closes sources tooltip on outside click", () => {
    const props = createBaseProps({
      sourcesTotal: 2,
      sourcesAvailable: 1,
      sourceNames: ["PNCP", "Portal Compras"],
    });
    render(<DataQualityBanner {...props} />);

    const sourcesButton = screen.getByLabelText(/1 de 2 fontes disponíveis/);
    fireEvent.click(sourcesButton);

    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });
});
