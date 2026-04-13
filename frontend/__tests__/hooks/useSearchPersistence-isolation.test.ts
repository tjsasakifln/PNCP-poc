/**
 * useSearchPersistence isolation tests — FE-035
 *
 * Tests the persistence sub-hook in isolation:
 * - handleSaveSearch: opens dialog with correct default name
 * - confirmSaveSearch: calls saveNewSearch, fires toast, closes dialog
 * - confirmSaveSearch: handles save error
 * - handleLoadSearch: restores filters from saved search (setor + termos modes)
 * - handleRefresh: restores params and calls buscar
 * - restoreSearchStateOnMount: restores result + form state
 * - buscarForceFresh: calls buscar with forceFresh:true
 * - dismissPartialResults: clears showingPartialResults
 */

import { renderHook, act } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const mockTrackEvent = jest.fn();
jest.mock("../../hooks/useAnalytics", () => ({
  useAnalytics: () => ({ trackEvent: mockTrackEvent }),
}));

const mockSaveNewSearch = jest.fn();
const mockIsMaxCapacity = false;
jest.mock("../../hooks/useSavedSearches", () => ({
  useSavedSearches: () => ({
    saveNewSearch: mockSaveNewSearch,
    isMaxCapacity: mockIsMaxCapacity,
  }),
}));

const mockRestoreSearchState = jest.fn(() => null);
jest.mock("../../lib/searchStatePersistence", () => ({
  restoreSearchState: () => mockRestoreSearchState(),
}));

const mockSaveNavSearch = jest.fn(() => true);
const mockRestoreNavSearch = jest.fn(() => null);
const mockClearNavSearch = jest.fn();
jest.mock("../../lib/navSearchCache", () => ({
  saveNavSearch: (...args: unknown[]) => mockSaveNavSearch(...args),
  restoreNavSearch: () => mockRestoreNavSearch(),
  clearNavSearch: () => mockClearNavSearch(),
  hasNavSearch: jest.fn(() => false),
}));

jest.mock("sonner", () => ({
  toast: { success: jest.fn(), error: jest.fn(), info: jest.fn() },
}));

// ---------------------------------------------------------------------------
// Import under test
// ---------------------------------------------------------------------------

import { useSearchPersistence } from "../../app/buscar/hooks/useSearchPersistence";
import type { BuscaResult } from "../../app/types";
import type { SavedSearch } from "../../lib/savedSearches";

const { toast: mockToast } = require("sonner");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

type BuscaResultPartial = Partial<BuscaResult>;

function makeBuscaResult(overrides: BuscaResultPartial = {}): BuscaResult {
  return {
    resumo: {
      resumo_executivo: "Teste",
      total_oportunidades: 2,
      valor_total: 50000,
      destaques: [],
      recomendacoes: [],
      alertas_urgencia: [],
      insight_setorial: "",
    } as BuscaResult["resumo"],
    licitacoes: [{ pncp_id: "lic-1" } as BuscaResult["licitacoes"][0]],
    total_raw: 5,
    total_filtrado: 2,
    excel_available: false,
    quota_used: 1,
    quota_remaining: 9,
    response_state: "live" as const,
    ...overrides,
  } as BuscaResult;
}

function makeFilters(overrides: Record<string, unknown> = {}) {
  return {
    searchMode: "setor" as const,
    sectorName: "Construção Civil",
    termosArray: [] as string[],
    ufsSelecionadas: new Set(["SP", "RJ"]),
    dataInicial: "2026-01-01",
    dataFinal: "2026-01-15",
    setorId: "construcao",
    status: "todos" as any,
    modalidades: [] as number[],
    valorMin: null,
    valorMax: null,
    esferas: [] as any[],
    municipios: [] as any[],
    ordenacao: "relevancia" as any,
    setUfsSelecionadas: jest.fn(),
    setDataInicial: jest.fn(),
    setDataFinal: jest.fn(),
    setSearchMode: jest.fn(),
    setSetorId: jest.fn(),
    setTermosArray: jest.fn(),
    setStatus: jest.fn(),
    setModalidades: jest.fn(),
    setValorMin: jest.fn(),
    setValorMax: jest.fn(),
    setEsferas: jest.fn(),
    setMunicipios: jest.fn(),
    ...overrides,
  };
}

function makeParams(overrides: Record<string, unknown> = {}) {
  return {
    filters: makeFilters(),
    result: makeBuscaResult(),
    setResult: jest.fn(),
    buscar: jest.fn().mockResolvedValue(undefined),
    ...overrides,
  };
}

function makeSavedSearch(overrides: Record<string, unknown> = {}): SavedSearch {
  return {
    id: "saved-1",
    name: "Minha Análise",
    createdAt: Date.now(),
    searchParams: {
      ufs: ["SP"],
      dataInicial: "2026-01-01",
      dataFinal: "2026-01-15",
      searchMode: "setor",
      setorId: "construcao",
    },
    ...overrides,
  } as SavedSearch;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useSearchPersistence — isolation tests (FE-035)", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRestoreSearchState.mockReturnValue(null);
  });

  // =========================================================================
  // Initial state
  // =========================================================================

  describe("initial state", () => {
    test("showSaveDialog starts false", () => {
      const { result } = renderHook(() => useSearchPersistence(makeParams() as any));
      expect(result.current.showSaveDialog).toBe(false);
    });

    test("saveSearchName starts empty", () => {
      const { result } = renderHook(() => useSearchPersistence(makeParams() as any));
      expect(result.current.saveSearchName).toBe("");
    });

    test("saveError starts null", () => {
      const { result } = renderHook(() => useSearchPersistence(makeParams() as any));
      expect(result.current.saveError).toBeNull();
    });

    test("showingPartialResults starts false", () => {
      const { result } = renderHook(() => useSearchPersistence(makeParams() as any));
      expect(result.current.showingPartialResults).toBe(false);
    });

    test("lastSearchParamsRef starts null", () => {
      const { result } = renderHook(() => useSearchPersistence(makeParams() as any));
      expect(result.current.lastSearchParamsRef.current).toBeNull();
    });
  });

  // =========================================================================
  // handleSaveSearch
  // =========================================================================

  describe("handleSaveSearch", () => {
    test("does nothing when result is null", () => {
      const params = makeParams({ result: null });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.showSaveDialog).toBe(false);
    });

    test("opens dialog with sector name as default for setor mode", () => {
      const params = makeParams({
        filters: makeFilters({ searchMode: "setor", sectorName: "Tecnologia" }),
      });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.showSaveDialog).toBe(true);
      expect(result.current.saveSearchName).toBe("Tecnologia");
    });

    test("uses termos as default name in termos mode", () => {
      const params = makeParams({
        filters: makeFilters({
          searchMode: "termos",
          termosArray: ["pavimento", "rodovia"],
        }),
      });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.saveSearchName).toContain("pavimento");
      expect(result.current.saveSearchName).toContain("rodovia");
    });

    test("uses 'Análise personalizada' fallback when sector name empty", () => {
      const params = makeParams({
        filters: makeFilters({ searchMode: "setor", sectorName: "" }),
      });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.saveSearchName).toBe("Análise personalizada");
    });

    test("clears saveError when opening dialog", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      // Manually set a saveError first
      act(() => {
        // Simulate prior error state via confirmSaveSearch failure
        mockSaveNewSearch.mockImplementationOnce(() => { throw new Error("prior error"); });
        result.current.handleSaveSearch();
      });
      act(() => {
        result.current.confirmSaveSearch();
      });

      const priorError = result.current.saveError;

      // Open dialog again — should clear error
      act(() => {
        result.current.handleSaveSearch();
      });

      expect(result.current.saveError).toBeNull();
    });
  });

  // =========================================================================
  // confirmSaveSearch
  // =========================================================================

  describe("confirmSaveSearch", () => {
    test("calls saveNewSearch with name and filter params", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleSaveSearch();
        result.current.setSaveSearchName("Análise Custom");
      });

      act(() => {
        result.current.confirmSaveSearch();
      });

      expect(mockSaveNewSearch).toHaveBeenCalledWith(
        "Análise Custom",
        expect.objectContaining({
          ufs: expect.any(Array),
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-15",
          searchMode: "setor",
          setorId: "construcao",
        })
      );
    });

    test("shows success toast after saving", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.setSaveSearchName("Teste");
        result.current.confirmSaveSearch();
      });

      expect(mockToast.success).toHaveBeenCalled();
    });

    test("closes dialog after successful save", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.setShowSaveDialog(true);
        result.current.setSaveSearchName("Teste");
        result.current.confirmSaveSearch();
      });

      expect(result.current.showSaveDialog).toBe(false);
    });

    test("resets saveSearchName after save", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.setSaveSearchName("Meu nome");
        result.current.confirmSaveSearch();
      });

      expect(result.current.saveSearchName).toBe("");
    });

    test("uses 'Análise sem nome' when name is empty", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.setSaveSearchName("");
        result.current.confirmSaveSearch();
      });

      expect(mockSaveNewSearch).toHaveBeenCalledWith("Análise sem nome", expect.any(Object));
    });

    test("sets saveError and fires error toast when saveNewSearch throws", () => {
      mockSaveNewSearch.mockImplementationOnce(() => {
        throw new Error("Limite de análises salvas atingido");
      });

      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.confirmSaveSearch();
      });

      expect(result.current.saveError).toBe("Limite de análises salvas atingido");
      expect(mockToast.error).toHaveBeenCalled();
    });

    test("tracks saved_search_created Mixpanel event", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      // Set the name first
      act(() => {
        result.current.setSaveSearchName("Analytics Test");
      });

      // Confirm in a separate act so state has updated
      act(() => {
        result.current.confirmSaveSearch();
      });

      expect(mockTrackEvent).toHaveBeenCalledWith(
        "saved_search_created",
        expect.objectContaining({ search_name: "Analytics Test" })
      );
    });
  });

  // =========================================================================
  // handleLoadSearch
  // =========================================================================

  describe("handleLoadSearch", () => {
    test("restores UFs, dates, and mode for setor search", () => {
      const filters = makeFilters();
      const params = makeParams({ filters });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      const saved = makeSavedSearch({
        searchParams: {
          ufs: ["MG", "RS"],
          dataInicial: "2026-02-01",
          dataFinal: "2026-02-28",
          searchMode: "setor",
          setorId: "saude",
        },
      });

      act(() => {
        result.current.handleLoadSearch(saved);
      });

      expect((filters as any).setUfsSelecionadas).toHaveBeenCalledWith(new Set(["MG", "RS"]));
      expect((filters as any).setDataInicial).toHaveBeenCalledWith("2026-02-01");
      expect((filters as any).setDataFinal).toHaveBeenCalledWith("2026-02-28");
      expect((filters as any).setSearchMode).toHaveBeenCalledWith("setor");
      expect((filters as any).setSetorId).toHaveBeenCalledWith("saude");
    });

    test("restores termos search with comma-separated terms", () => {
      const filters = makeFilters();
      const params = makeParams({ filters });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      const saved = makeSavedSearch({
        searchParams: {
          ufs: ["SP"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-15",
          searchMode: "termos",
          termosBusca: "pavimento, rodovia, obra",
        },
      });

      act(() => {
        result.current.handleLoadSearch(saved);
      });

      expect((filters as any).setTermosArray).toHaveBeenCalledWith(["pavimento", "rodovia", "obra"]);
    });

    test("restores termos search with space-separated terms (no comma)", () => {
      const filters = makeFilters();
      const params = makeParams({ filters });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      const saved = makeSavedSearch({
        searchParams: {
          ufs: ["SP"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-15",
          searchMode: "termos",
          termosBusca: "software hardware",
        },
      });

      act(() => {
        result.current.handleLoadSearch(saved);
      });

      expect((filters as any).setTermosArray).toHaveBeenCalledWith(["software", "hardware"]);
    });

    test("clears result when loading a search", () => {
      const setResult = jest.fn();
      const params = makeParams({ setResult });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.handleLoadSearch(makeSavedSearch());
      });

      expect(setResult).toHaveBeenCalledWith(null);
    });
  });

  // =========================================================================
  // handleRefresh
  // =========================================================================

  describe("handleRefresh", () => {
    test("does nothing when lastSearchParamsRef is null", async () => {
      const mockBuscar = jest.fn();
      const params = makeParams({ buscar: mockBuscar });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      await act(async () => {
        await result.current.handleRefresh();
      });

      expect(mockBuscar).not.toHaveBeenCalled();
    });

    test("restores all params and calls buscar when lastSearchParamsRef set", async () => {
      const filters = makeFilters();
      const mockBuscar = jest.fn().mockResolvedValue(undefined);
      const params = makeParams({ filters, buscar: mockBuscar });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      // Set lastSearchParamsRef manually
      act(() => {
        result.current.lastSearchParamsRef.current = {
          ufs: new Set(["PR"]),
          dataInicial: "2026-03-01",
          dataFinal: "2026-03-15",
          searchMode: "setor",
          setorId: "tecnologia",
          termosArray: undefined,
          status: "abertas" as any,
          modalidades: [5],
          valorMin: 1000,
          valorMax: 999999,
          esferas: ["federal"] as any,
          municipios: [],
          ordenacao: "data" as any,
        };
      });

      await act(async () => {
        await result.current.handleRefresh();
      });

      expect((filters as any).setUfsSelecionadas).toHaveBeenCalledWith(new Set(["PR"]));
      expect((filters as any).setDataInicial).toHaveBeenCalledWith("2026-03-01");
      expect((filters as any).setDataFinal).toHaveBeenCalledWith("2026-03-15");
      expect((filters as any).setSearchMode).toHaveBeenCalledWith("setor");
      expect(mockBuscar).toHaveBeenCalledTimes(1);
    });

    test("tracks pull_to_refresh_triggered Mixpanel event", async () => {
      const mockBuscar = jest.fn().mockResolvedValue(undefined);
      const params = makeParams({ buscar: mockBuscar });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.lastSearchParamsRef.current = {
          ufs: new Set(["SP"]),
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-15",
          searchMode: "termos",
          termosArray: ["teste"],
          status: "todos" as any,
          modalidades: [],
          valorMin: null,
          valorMax: null,
          esferas: [],
          municipios: [],
          ordenacao: "relevancia" as any,
        };
      });

      await act(async () => {
        await result.current.handleRefresh();
      });

      expect(mockTrackEvent).toHaveBeenCalledWith(
        "pull_to_refresh_triggered",
        expect.objectContaining({ search_mode: "termos" })
      );
    });
  });

  // =========================================================================
  // restoreSearchStateOnMount
  // =========================================================================

  describe("restoreSearchStateOnMount", () => {
    test("does nothing when no saved state", () => {
      mockRestoreSearchState.mockReturnValue(null);
      const setResult = jest.fn();
      const params = makeParams({ setResult });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.restoreSearchStateOnMount();
      });

      expect(setResult).not.toHaveBeenCalled();
      expect(mockToast.success).not.toHaveBeenCalled();
    });

    test("restores result and form state when saved", () => {
      const savedResult = makeBuscaResult({ download_id: "dl-saved" });
      mockRestoreSearchState.mockReturnValue({
        result: savedResult,
        downloadId: "dl-saved",
        formState: {
          ufs: ["GO"],
          startDate: "2026-03-01",
          endDate: "2026-03-10",
          setor: "saude",
        },
      });

      const setResult = jest.fn();
      const filters = makeFilters();
      const params = makeParams({ setResult, filters });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.restoreSearchStateOnMount();
      });

      expect(setResult).toHaveBeenCalledWith(savedResult);
      expect((filters as any).setUfsSelecionadas).toHaveBeenCalledWith(new Set(["GO"]));
      expect((filters as any).setDataInicial).toHaveBeenCalledWith("2026-03-01");
      expect((filters as any).setDataFinal).toHaveBeenCalledWith("2026-03-10");
      expect((filters as any).setSearchMode).toHaveBeenCalledWith("setor");
      expect((filters as any).setSetorId).toHaveBeenCalledWith("saude");
    });

    test("shows success toast on restore", () => {
      const savedResult = makeBuscaResult({ download_id: "dl-abc" });
      mockRestoreSearchState.mockReturnValue({
        result: savedResult,
        downloadId: "dl-abc",
        formState: { ufs: ["SP"] },
      });

      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.restoreSearchStateOnMount();
      });

      expect(mockToast.success).toHaveBeenCalledWith(
        expect.stringContaining("restaurados")
      );
    });

    test("restores termos keywords from formState", () => {
      mockRestoreSearchState.mockReturnValue({
        result: makeBuscaResult(),
        downloadId: "dl-t",
        formState: {
          includeKeywords: ["asfalto", "pavimento"],
        },
      });

      const filters = makeFilters();
      const params = makeParams({ filters });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.restoreSearchStateOnMount();
      });

      expect((filters as any).setSearchMode).toHaveBeenCalledWith("termos");
      expect((filters as any).setTermosArray).toHaveBeenCalledWith(["asfalto", "pavimento"]);
    });

    test("tracks search_state_auto_restored event", () => {
      mockRestoreSearchState.mockReturnValue({
        result: makeBuscaResult(),
        downloadId: "dl-123",
        formState: {},
      });

      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.restoreSearchStateOnMount();
      });

      expect(mockTrackEvent).toHaveBeenCalledWith(
        "search_state_auto_restored",
        expect.objectContaining({ download_id: "dl-123" })
      );
    });
  });

  // =========================================================================
  // buscarForceFresh
  // =========================================================================

  describe("buscarForceFresh", () => {
    test("calls buscar with forceFresh: true", async () => {
      const mockBuscar = jest.fn().mockResolvedValue(undefined);
      const params = makeParams({ buscar: mockBuscar });
      const { result } = renderHook(() => useSearchPersistence(params as any));

      await act(async () => {
        await result.current.buscarForceFresh();
      });

      expect(mockBuscar).toHaveBeenCalledWith({ forceFresh: true });
    });
  });

  // =========================================================================
  // dismissPartialResults
  // =========================================================================

  describe("dismissPartialResults", () => {
    test("sets showingPartialResults to false", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));

      act(() => {
        result.current.setShowingPartialResults(true);
      });
      expect(result.current.showingPartialResults).toBe(true);

      act(() => {
        result.current.dismissPartialResults();
      });
      expect(result.current.showingPartialResults).toBe(false);
    });
  });

  // =========================================================================
  // isMaxCapacity passthrough
  // =========================================================================

  describe("isMaxCapacity", () => {
    test("exposes isMaxCapacity from useSavedSearches", () => {
      const params = makeParams();
      const { result } = renderHook(() => useSearchPersistence(params as any));
      expect(result.current.isMaxCapacity).toBe(false);
    });
  });

  // =========================================================================
  // UX-432 — Navigation cache
  // =========================================================================

  describe("UX-432 — Nav cache", () => {
    beforeEach(() => {
      mockRestoreNavSearch.mockReturnValue(null);
      mockClearNavSearch.mockClear();
      mockSaveNavSearch.mockClear();
    });

    describe("initial state", () => {
      test("isRestoredFromNav starts false", () => {
        const { result } = renderHook(() =>
          useSearchPersistence(makeParams({ result: null }) as any)
        );
        expect(result.current.isRestoredFromNav).toBe(false);
      });

      test("restoredNavMeta starts null", () => {
        const { result } = renderHook(() =>
          useSearchPersistence(makeParams({ result: null }) as any)
        );
        expect(result.current.restoredNavMeta).toBeNull();
      });
    });

    describe("restoreSearchStateOnMount — nav cache path", () => {
      test("restores result and sets isRestoredFromNav when nav cache has data", () => {
        const navResult = makeBuscaResult({ total_raw: 10 });
        mockRestoreNavSearch.mockReturnValue({
          result: navResult,
          formState: { ufs: ["SC"], startDate: "2026-01-01", endDate: "2026-01-07", setor: "uniformes" },
          meta: { sectorName: "Uniformes", ufsLabel: "SC" },
          timestamp: Date.now(),
          expiresAt: Date.now() + 1_800_000,
        });

        const mockSetResult = jest.fn();
        const params = makeParams({ result: null, setResult: mockSetResult });
        const { result } = renderHook(() => useSearchPersistence(params as any));

        act(() => {
          result.current.restoreSearchStateOnMount();
        });

        expect(mockSetResult).toHaveBeenCalledWith(navResult);
        expect(result.current.isRestoredFromNav).toBe(true);
        expect(result.current.restoredNavMeta).toEqual({
          sectorName: "Uniformes",
          ufsLabel: "SC",
        });
      });

      test("restores filters (UFs, dates, setor) from nav cache", () => {
        mockRestoreNavSearch.mockReturnValue({
          result: makeBuscaResult(),
          formState: {
            ufs: ["SC", "RS"],
            startDate: "2026-02-01",
            endDate: "2026-02-15",
            setor: "uniformes",
          },
          meta: { sectorName: "Uniformes", ufsLabel: "SC, RS" },
          timestamp: Date.now(),
          expiresAt: Date.now() + 1_800_000,
        });

        const filters = makeFilters();
        const params = makeParams({ filters, result: null });
        const { result } = renderHook(() => useSearchPersistence(params as any));

        act(() => {
          result.current.restoreSearchStateOnMount();
        });

        expect(filters.setUfsSelecionadas).toHaveBeenCalledWith(new Set(["SC", "RS"]));
        expect(filters.setDataInicial).toHaveBeenCalledWith("2026-02-01");
        expect(filters.setDataFinal).toHaveBeenCalledWith("2026-02-15");
        expect(filters.setSearchMode).toHaveBeenCalledWith("setor");
        expect(filters.setSetorId).toHaveBeenCalledWith("uniformes");
      });

      test("auth-flow cache takes priority over nav cache", () => {
        // Auth-flow cache returns data
        mockRestoreSearchState.mockReturnValueOnce({
          result: makeBuscaResult(),
          downloadId: "dl-123",
          formState: { ufs: ["SP"], startDate: "2026-01-01", endDate: "2026-01-07" },
        });
        mockRestoreNavSearch.mockReturnValue({
          result: makeBuscaResult({ total_raw: 99 }),
          formState: { ufs: ["RS"] },
          meta: { sectorName: "Nav", ufsLabel: "RS" },
          timestamp: Date.now(),
          expiresAt: Date.now() + 1_800_000,
        });

        const { result } = renderHook(() => useSearchPersistence(makeParams({ result: null }) as any));

        act(() => {
          result.current.restoreSearchStateOnMount();
        });

        // Nav cache restore should NOT have been called
        expect(mockRestoreNavSearch).not.toHaveBeenCalled();
        expect(result.current.isRestoredFromNav).toBe(false);
      });

      test("does nothing when nav cache returns null", () => {
        mockRestoreNavSearch.mockReturnValue(null);

        const mockSetResult = jest.fn();
        const { result } = renderHook(() =>
          useSearchPersistence(makeParams({ result: null, setResult: mockSetResult }) as any)
        );

        act(() => {
          result.current.restoreSearchStateOnMount();
        });

        expect(mockSetResult).not.toHaveBeenCalled();
        expect(result.current.isRestoredFromNav).toBe(false);
      });
    });

    describe("handleNovaBusca", () => {
      test("clears nav cache, resets result, and clears isRestoredFromNav", () => {
        mockRestoreNavSearch.mockReturnValueOnce({
          result: makeBuscaResult(),
          formState: { ufs: ["SC"], startDate: "2026-01-01", endDate: "2026-01-07" },
          meta: { sectorName: "Uniformes", ufsLabel: "SC" },
          timestamp: Date.now(),
          expiresAt: Date.now() + 1_800_000,
        });

        const mockSetResult = jest.fn();
        const { result } = renderHook(() =>
          useSearchPersistence(makeParams({ result: null, setResult: mockSetResult }) as any)
        );

        // First restore to set isRestoredFromNav = true
        act(() => {
          result.current.restoreSearchStateOnMount();
        });
        expect(result.current.isRestoredFromNav).toBe(true);

        // Now click Nova busca
        act(() => {
          result.current.handleNovaBusca();
        });

        expect(mockClearNavSearch).toHaveBeenCalled();
        expect(mockSetResult).toHaveBeenLastCalledWith(null);
        expect(result.current.isRestoredFromNav).toBe(false);
        expect(result.current.restoredNavMeta).toBeNull();
      });
    });

    describe("auto-save on result change", () => {
      test("calls saveNavSearch when result is set", () => {
        const resultData = makeBuscaResult();
        renderHook(() => useSearchPersistence(makeParams({ result: resultData }) as any));

        // useEffect fires on mount with the current result
        expect(mockSaveNavSearch).toHaveBeenCalledWith(
          resultData,
          expect.objectContaining({ ufs: expect.any(Array) }),
          expect.objectContaining({ sectorName: expect.any(String), ufsLabel: expect.any(String) })
        );
      });

      test("does not call saveNavSearch when result is null", () => {
        renderHook(() => useSearchPersistence(makeParams({ result: null }) as any));
        expect(mockSaveNavSearch).not.toHaveBeenCalled();
      });
    });
  });
});
