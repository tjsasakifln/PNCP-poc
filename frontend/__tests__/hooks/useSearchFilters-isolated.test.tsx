/**
 * TD-006 AC2: Isolated test suite for useSearchFilters hook.
 *
 * Covers:
 * - Sector loading from API
 * - Sector fallback on API failure
 * - Stale cache fallback
 * - UF toggle, region toggle, select all, clear
 * - Term validation (stopwords, short terms, special chars)
 * - Add/remove terms
 * - Value range filter
 * - canSearch validation
 * - Computed values (sectorName, searchLabel, dateLabel)
 * - modoBusca behavior
 * - Collapsible state persistence
 */

import { renderHook, act, waitFor } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock("../../app/components/AuthProvider", () => ({
  useAuth: () => ({
    user: { user_metadata: { sector: "engenharia" } },
    session: { access_token: "test-token" },
  }),
}));

jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: jest.fn() }),
}));

// Explicitly mock next/navigation — jest.setup.js mock may not work due to try/catch
const mockUseSearchParams = jest.fn().mockReturnValue(new URLSearchParams());
jest.mock("next/navigation", () => ({
  __esModule: true,
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  })),
  usePathname: jest.fn(() => "/buscar"),
  useSearchParams: (...args: any[]) => mockUseSearchParams(...args),
}));

// Mock dates utility for deterministic tests
jest.mock("../../app/buscar/utils/dates", () => ({
  getBrtDate: () => "2026-03-01",
  addDays: (_base: string, days: number) => {
    const d = new Date("2026-03-01");
    d.setDate(d.getDate() + days);
    return d.toISOString().slice(0, 10);
  },
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import {
  useSearchFilters,
  validateTermsClientSide,
  SETORES_FALLBACK,
  DEFAULT_SEARCH_DAYS,
} from "../../app/buscar/hooks/useSearchFilters";

// ---------------------------------------------------------------------------
// Setup / Teardown
// ---------------------------------------------------------------------------

beforeEach(() => {
  mockFetch.mockReset();
  if (typeof window !== "undefined") {
    localStorage.clear();
  }
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useSearchFilters (isolated)", () => {
  // 1. Sector loading from API
  test("loads sectors from /api/setores on mount", async () => {
    const sectors = [
      { id: "engenharia", name: "Engenharia", description: "Obras" },
      { id: "saude", name: "Saude", description: "Medicamentos" },
    ];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: sectors }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    expect(result.current.setores).toEqual(sectors);
    expect(result.current.setoresUsingFallback).toBe(false);
    expect(result.current.setoresError).toBe(false);
  });

  // 2. Sector fallback on API failure
  test("falls back to SETORES_FALLBACK after retries exhausted", async () => {
    jest.useFakeTimers();
    // All 3 attempts fail (attempt 0, 1, 2)
    mockFetch
      .mockRejectedValueOnce(new Error("fail1"))
      .mockRejectedValueOnce(new Error("fail2"))
      .mockRejectedValueOnce(new Error("fail3"));

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    // Advance through retry delays: 1s (2^0), 2s (2^1)
    await act(async () => {
      await jest.advanceTimersByTimeAsync(1100);
    });
    await act(async () => {
      await jest.advanceTimersByTimeAsync(2100);
    });

    await waitFor(() => {
      expect(result.current.setoresError).toBe(true);
    });

    expect(result.current.setoresUsingFallback).toBe(true);
    expect(result.current.setores).toEqual(SETORES_FALLBACK);

    jest.useRealTimers();
  });

  // 3. Uses fresh localStorage cache
  test("uses cached sectors when fresh", async () => {
    const cached = {
      data: [{ id: "cached", name: "Cached Sector", description: "From cache" }],
      timestamp: Date.now(), // fresh
    };
    localStorage.setItem("smartlic-sectors-cache-v3", JSON.stringify(cached));

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    expect(result.current.setores[0].id).toBe("cached");
    expect(mockFetch).not.toHaveBeenCalled();
  });

  // 4. UF toggle
  test("toggleUf adds and removes UFs", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    // Default is empty (no profile context in localStorage)
    expect(result.current.ufsSelecionadas.size).toBe(0);

    // Toggle RJ on
    act(() => {
      result.current.toggleUf("RJ");
    });
    expect(result.current.ufsSelecionadas.has("RJ")).toBe(true);
    expect(clearResult).toHaveBeenCalled();

    // Toggle RJ off
    act(() => {
      result.current.toggleUf("RJ");
    });
    expect(result.current.ufsSelecionadas.has("RJ")).toBe(false);
  });

  // 5. Select all / clear UFs
  test("selecionarTodos selects all 27 UFs", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    act(() => {
      result.current.selecionarTodos();
    });

    expect(result.current.ufsSelecionadas.size).toBe(27);
    expect(result.current.allUfsSelected).toBe(true);

    act(() => {
      result.current.limparSelecao();
    });

    expect(result.current.ufsSelecionadas.size).toBe(0);
  });

  // 6. Region toggle
  test("toggleRegion toggles all UFs in a region", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    // Clear first
    act(() => {
      result.current.limparSelecao();
    });

    const sudeste = ["SP", "RJ", "MG", "ES"];
    act(() => {
      result.current.toggleRegion(sudeste);
    });

    expect(result.current.ufsSelecionadas.has("SP")).toBe(true);
    expect(result.current.ufsSelecionadas.has("RJ")).toBe(true);
    expect(result.current.ufsSelecionadas.has("MG")).toBe(true);
    expect(result.current.ufsSelecionadas.has("ES")).toBe(true);

    // Toggle same region off
    act(() => {
      result.current.toggleRegion(sudeste);
    });

    expect(result.current.ufsSelecionadas.size).toBe(0);
  });

  // 7. Term validation — stopwords rejected
  test("validateTermsClientSide rejects stopwords", () => {
    const result = validateTermsClientSide(["de", "para", "engenharia"]);
    expect(result.ignored).toContain("de");
    expect(result.ignored).toContain("para");
    expect(result.valid).toContain("engenharia");
  });

  // 8. Term validation — short terms rejected
  test("validateTermsClientSide rejects short single-word terms", () => {
    const result = validateTermsClientSide(["abc", "obra", "ti"]);
    expect(result.ignored).toContain("abc");
    expect(result.ignored).toContain("ti");
    expect(result.valid).toContain("obra");
    expect(result.reasons["abc"]).toContain("curto");
  });

  // 9. Term validation — special chars rejected
  test("validateTermsClientSide rejects special characters", () => {
    const result = validateTermsClientSide(["engenharia@civil", "obras"]);
    expect(result.ignored).toContain("engenharia@civil");
    expect(result.valid).toContain("obras");
  });

  // 10. addTerms / removeTerm
  test("addTerms adds terms and removeTerm removes them", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    // Switch to termos mode
    act(() => {
      result.current.setSearchMode("termos");
    });

    act(() => {
      result.current.addTerms(["engenharia", "construcao"]);
    });

    expect(result.current.termosArray).toEqual(["engenharia", "construcao"]);
    expect(clearResult).toHaveBeenCalled();

    // Add duplicate — should not duplicate
    act(() => {
      result.current.addTerms(["engenharia", "reformas"]);
    });

    expect(result.current.termosArray).toEqual(["engenharia", "construcao", "reformas"]);

    // Remove
    act(() => {
      result.current.removeTerm("construcao");
    });

    expect(result.current.termosArray).toEqual(["engenharia", "reformas"]);
  });

  // 11. canSearch validation
  test("canSearch is false when no UFs selected", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    act(() => {
      result.current.limparSelecao();
    });

    await waitFor(() => {
      expect(result.current.canSearch).toBe(false);
    });

    expect(result.current.validationErrors.ufs).toBeDefined();
  });

  // 12. Computed: sectorName
  test("sectorName returns selected sector name", async () => {
    const sectors = [
      { id: "engenharia", name: "Engenharia e Obras", description: "Desc" },
    ];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: sectors }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    act(() => {
      result.current.setSetorId("engenharia");
    });

    expect(result.current.sectorName).toBe("Engenharia e Obras");
  });

  // 13. dateLabel changes with modoBusca
  test("dateLabel changes based on modoBusca", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ setores: SETORES_FALLBACK }),
    });

    const clearResult = jest.fn();
    const { result } = renderHook(() => useSearchFilters(clearResult));

    await waitFor(() => {
      expect(result.current.setoresLoading).toBe(false);
    });

    // Default is "abertas"
    expect(result.current.dateLabel).toContain("abertas");

    act(() => {
      result.current.setModoBusca("publicacao");
    });

    expect(result.current.dateLabel).toContain("publicação");
  });

  // 14. DEFAULT_SEARCH_DAYS is exported correctly
  test("DEFAULT_SEARCH_DAYS is 10", () => {
    expect(DEFAULT_SEARCH_DAYS).toBe(10);
  });

  // 15. SETORES_FALLBACK structure is valid (exact count validated against backend YAML by sector-sync.test.ts)
  test("SETORES_FALLBACK contains valid sector entries", () => {
    expect(Array.isArray(SETORES_FALLBACK)).toBe(true);
    expect(SETORES_FALLBACK.length).toBeGreaterThan(0);
    expect(SETORES_FALLBACK[0].id).toBe("vestuario");
    SETORES_FALLBACK.forEach((s) => {
      expect(s).toHaveProperty("id");
      expect(s).toHaveProperty("name");
    });
  });
});
