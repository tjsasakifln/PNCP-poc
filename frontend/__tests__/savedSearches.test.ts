/**
 * Tests for Saved Searches Feature (Feature #1)
 *
 * Target coverage: 75%+ for saved searches module
 */

// Mock uuid before importing savedSearches
jest.mock('uuid');

import {
  loadSavedSearches,
  saveSearch,
  deleteSavedSearch,
  markSearchAsUsed,
  clearAllSavedSearches,
  isMaxCapacityReached,
  type SavedSearch,
} from "@/lib/savedSearches";

// Define SearchParams type inline (not exported from library)
type SearchParams = SavedSearch['searchParams'];

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe("savedSearches library", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("loadSavedSearches", () => {
    it("should return empty array when no searches saved", () => {
      const searches = loadSavedSearches();
      expect(searches).toEqual([]);
    });

    it("should load saved searches from localStorage", () => {
      const mockSearches: SavedSearch[] = [
        {
          id: "test-1",
          name: "Test Search 1",
          searchParams: {
            ufs: ["SC", "PR"],
            dataInicial: "2026-01-01",
            dataFinal: "2026-01-31",
            searchMode: "setor",
            setorId: "vestuario",
          },
          createdAt: "2026-01-29T10:00:00.000Z",
          lastUsedAt: "2026-01-29T10:00:00.000Z",
        },
      ];

      localStorage.setItem(
        "descomplicita_saved_searches",
        JSON.stringify(mockSearches)
      );

      const searches = loadSavedSearches();
      expect(searches).toEqual(mockSearches);
    });

    it("should handle corrupted data gracefully", () => {
      localStorage.setItem("descomplicita_saved_searches", "corrupted json");

      const searches = loadSavedSearches();
      expect(searches).toEqual([]);
    });

    it("should sort searches by lastUsedAt (most recent first)", () => {
      const mockSearches: SavedSearch[] = [
        {
          id: "test-1",
          name: "Oldest",
          searchParams: {
            ufs: ["SC"],
            dataInicial: "2026-01-01",
            dataFinal: "2026-01-31",
            searchMode: "setor",
            setorId: "vestuario",
          },
          createdAt: "2026-01-27T10:00:00.000Z",
          lastUsedAt: "2026-01-27T10:00:00.000Z",
        },
        {
          id: "test-2",
          name: "Newest",
          searchParams: {
            ufs: ["PR"],
            dataInicial: "2026-01-01",
            dataFinal: "2026-01-31",
            searchMode: "setor",
            setorId: "alimentos",
          },
          createdAt: "2026-01-29T10:00:00.000Z",
          lastUsedAt: "2026-01-29T10:00:00.000Z",
        },
      ];

      localStorage.setItem(
        "descomplicita_saved_searches",
        JSON.stringify(mockSearches)
      );

      const searches = loadSavedSearches();
      expect(searches[0].name).toBe("Newest");
      expect(searches[1].name).toBe("Oldest");
    });
  });

  describe("saveSearch", () => {
    it("should save a new search", () => {
      const searchParams: SearchParams = {
        ufs: ["SC", "PR"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      };

      const saved = saveSearch("My Search", searchParams);

      expect(saved.name).toBe("My Search");
      expect(saved.searchParams).toEqual(searchParams);
      expect(saved.id).toBeTruthy();
      expect(saved.createdAt).toBeTruthy();
      expect(saved.lastUsedAt).toBeTruthy();

      const searches = loadSavedSearches();
      expect(searches).toHaveLength(1);
      expect(searches[0]).toEqual(saved);
    });

    it("should enforce max 10 searches", () => {
      // Save 10 searches
      for (let i = 0; i < 10; i++) {
        saveSearch(`Search ${i}`, {
          ufs: ["SC"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-31",
          searchMode: "setor",
          setorId: "vestuario",
        });
      }

      // Try to save 11th search
      expect(() => {
        saveSearch("Search 11", {
          ufs: ["PR"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-31",
          searchMode: "setor",
          setorId: "alimentos",
        });
      }).toThrow("Máximo de 10 buscas salvas atingido");

      const searches = loadSavedSearches();
      expect(searches).toHaveLength(10);
    });

    it("should handle empty name", () => {
      expect(() => {
        saveSearch("", {
          ufs: ["SC"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-31",
          searchMode: "setor",
          setorId: "vestuario",
        });
      }).toThrow("Nome da busca é obrigatório");
    });

    it("should handle duplicate names", () => {
      saveSearch("Duplicate", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      // Should allow duplicate names
      const saved2 = saveSearch("Duplicate", {
        ufs: ["PR"],
        dataInicial: "2026-02-01",
        dataFinal: "2026-02-28",
        searchMode: "setor",
        setorId: "alimentos",
      });

      expect(saved2.name).toBe("Duplicate");
      const searches = loadSavedSearches();
      expect(searches).toHaveLength(2);
    });

    it("should handle special characters in name", () => {
      const saved = saveSearch("Test @#$%^&*() Search", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      expect(saved.name).toBe("Test @#$%^&*() Search");
    });
  });

  describe("deleteSavedSearch", () => {
    it("should delete a search by ID", () => {
      const saved = saveSearch("To Delete", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      deleteSavedSearch(saved.id);

      const searches = loadSavedSearches();
      expect(searches).toHaveLength(0);
    });

    it("should handle deleting non-existent ID", () => {
      saveSearch("Existing", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      deleteSavedSearch("non-existent-id");

      const searches = loadSavedSearches();
      expect(searches).toHaveLength(1);
    });
  });

  describe("markSearchAsUsed", () => {
    it("should update lastUsedAt timestamp", (done) => {
      const saved = saveSearch("Test", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      const originalTimestamp = saved.lastUsedAt;

      setTimeout(() => {
        markSearchAsUsed(saved.id);

        const searches = loadSavedSearches();
        expect(searches[0].lastUsedAt).not.toBe(originalTimestamp);
        done();
      }, 10);
    });
  });

  describe("clearAllSavedSearches", () => {
    it("should delete all saved searches", () => {
      saveSearch("Search 1", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });
      saveSearch("Search 2", {
        ufs: ["PR"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "alimentos",
      });

      clearAllSavedSearches();

      const searches = loadSavedSearches();
      expect(searches).toHaveLength(0);
    });
  });

  describe("isMaxCapacityReached", () => {
    it("should return false when less than 10 searches", () => {
      saveSearch("Test", {
        ufs: ["SC"],
        dataInicial: "2026-01-01",
        dataFinal: "2026-01-31",
        searchMode: "setor",
        setorId: "vestuario",
      });

      expect(isMaxCapacityReached()).toBe(false);
    });

    it("should return true when 10 searches saved", () => {
      for (let i = 0; i < 10; i++) {
        saveSearch(`Search ${i}`, {
          ufs: ["SC"],
          dataInicial: "2026-01-01",
          dataFinal: "2026-01-31",
          searchMode: "setor",
          setorId: "vestuario",
        });
      }

      expect(isMaxCapacityReached()).toBe(true);
    });
  });
});
