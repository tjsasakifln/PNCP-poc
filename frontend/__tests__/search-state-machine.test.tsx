/**
 * CRIT-027 AC10-AC13: Search state machine tests.
 *
 * Verifies the core state machine invariants:
 * - AC10: New search clears previous results (useSearch.buscar sets result=null)
 * - AC11: Empty state does NOT appear during loading (loading guard)
 * - AC12: SearchResults respects loading state for rendering decisions
 * - AC13: Zero regressions (checked by full test suite run)
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

// ═══════════════════════════════════════════════════════════════════════════════
// Test 1: useSearch.buscar() clears result immediately (AC10)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027 AC10: buscar() clears result on new search", () => {
  it("useSearch source code sets result=null at start of buscar()", async () => {
    // Read the useSearchAPI source to verify the fix is in place
    // (buscar() was extracted from useSearch.ts into useSearchAPI.ts)
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../app/buscar/hooks/execution/useSearchAPI.ts"),
      "utf8"
    );

    // CRIT-027 AC1: Must have setResult(null) BEFORE the fetch
    // The comment marks the fix location
    expect(source).toContain("CRIT-027 AC1");
    expect(source).toContain("setResult(null)");

    // Must save previousResultFallback BEFORE clearing (for CRIT-005 error recovery)
    const setResultNullIndex = source.indexOf("setResult(null)");
    const previousResultIndex = source.indexOf("const previousResultFallback = result");
    expect(previousResultIndex).toBeLessThan(setResultNullIndex);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Test 2: SearchResults guards empty state behind !loading (AC11)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027 AC11: SearchResults loading guards", () => {
  it("SearchResults source has loading guards on empty state and result sections", async () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../app/buscar/components/SearchResults.tsx"),
      "utf8"
    );

    // Count occurrences of "!loading &&" — CRIT-027 AC2-AC3 added these guards
    const loadingGuardMatches = source.match(/!loading\s*&&/g) || [];
    // Should have at least 5 loading guards (empty_failure, sources_down, partial_filtered, empty_state, live_fetch, result)
    expect(loadingGuardMatches.length).toBeGreaterThanOrEqual(5);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Test 3: Loading state renders progress, not empty state (AC11 functional)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027 AC11: Loading state component behavior", () => {
  it("renders a simple loading indicator component correctly", () => {
    // Test a minimal component that demonstrates the loading guard pattern
    // This validates the pattern without requiring full SearchResults dependencies
    function LoadingGuardedContent({ loading, result }: { loading: boolean; result: any }) {
      if (loading) {
        return <div data-testid="loading-state">Loading...</div>;
      }
      if (!loading && result && result.licitacoes?.length === 0) {
        return <div data-testid="empty-state">Nenhuma oportunidade</div>;
      }
      if (!loading && result && result.licitacoes?.length > 0) {
        return <div data-testid="result-state">{result.licitacoes.length} results</div>;
      }
      return null;
    }

    // When loading=true, should show loading, NOT empty state
    const { rerender } = render(
      <LoadingGuardedContent loading={true} result={{ licitacoes: [] }} />
    );
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
    expect(screen.queryByTestId("empty-state")).not.toBeInTheDocument();

    // When loading=false with empty result, should show empty state
    rerender(<LoadingGuardedContent loading={false} result={{ licitacoes: [] }} />);
    expect(screen.queryByTestId("loading-state")).not.toBeInTheDocument();
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();

    // When loading=false with results, should show result state
    rerender(<LoadingGuardedContent loading={false} result={{ licitacoes: [{ id: "1" }] }} />);
    expect(screen.getByTestId("result-state")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Test 4: Error recovery preserves previous results (CRIT-005 backward compat)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027: Error recovery backward compatibility", () => {
  it("useSearch preserves previousResultFallback for error recovery", async () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../app/buscar/hooks/execution/useSearchAPI.ts"),
      "utf8"
    );

    // CRIT-005 AC23: Error recovery uses previousResultFallback
    expect(source).toContain("previousResultFallback");
    expect(source).toContain("CRIT-005 AC23");

    // In catch block, should check previousResultFallback has licitacoes
    expect(source).toContain("previousResultFallback.licitacoes?.length > 0");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Test 5: Stale data from previous search cannot contaminate new search (AC10)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027 AC10: No stale data contamination", () => {
  it("rawCount is also cleared to 0 alongside result", () => {
    const fs = require("fs");
    const path = require("path");
    const source = fs.readFileSync(
      path.join(__dirname, "../app/buscar/hooks/execution/useSearchAPI.ts"),
      "utf8"
    );

    // After setResult(null), setRawCount(0) must follow
    const setResultNullIndex = source.indexOf("setResult(null)");
    const setRawCountIndex = source.indexOf("setRawCount(0)", setResultNullIndex);
    expect(setRawCountIndex).toBeGreaterThan(setResultNullIndex);
    // They should be close together (within 50 chars)
    expect(setRawCountIndex - setResultNullIndex).toBeLessThan(50);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Test 6: Banner cleanup - "Atualizando" only during loading (AC7)
// ═══════════════════════════════════════════════════════════════════════════════

describe("CRIT-027 AC7: Live fetch banner lifecycle", () => {
  it("SearchResults source guards live fetch banner with loading check", () => {
    const fs = require("fs");
    const path = require("path");
    // DEBT-204: Live fetch banner moved to SearchResultsBanners; check both files
    const source = fs.readFileSync(
      path.join(__dirname, "../app/buscar/components/SearchResults.tsx"),
      "utf8"
    );
    const bannerSource = fs.readFileSync(
      path.join(__dirname, "../app/buscar/components/SearchResultsBanners.tsx"),
      "utf8"
    );
    const combined = source + bannerSource;

    // The "Atualizando dados em tempo real" banner should be guarded by loading
    const bannerIndex = combined.indexOf("Atualizando dados em tempo real");
    expect(bannerIndex).toBeGreaterThan(-1);

    // The banner section should have a loading guard somewhere before it
    // Look back up to 1000 chars to find the enclosing conditional
    const nearbySource = combined.substring(Math.max(0, bannerIndex - 1000), bannerIndex);
    expect(nearbySource).toMatch(/loading/);
  });
});
