/**
 * STAB-006 AC4: Tests for localStorage partial search cache utility.
 */

import {
  savePartialSearch,
  recoverPartialSearch,
  clearPartialSearch,
  cleanupExpiredPartials,
} from "../../lib/searchPartialCache";

describe("searchPartialCache", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("savePartialSearch stores data in localStorage", () => {
    savePartialSearch("search-1", { total: 5 }, ["SP", "RJ"], 5);

    const raw = localStorage.getItem("search_partial_search-1");
    expect(raw).toBeTruthy();

    const data = JSON.parse(raw!);
    expect(data.searchId).toBe("search-1");
    expect(data.partialResult).toEqual({ total: 5 });
    expect(data.ufsCompleted).toEqual(["SP", "RJ"]);
    expect(data.totalUfs).toBe(5);
    expect(data.updatedAt).toBeGreaterThan(0);
    expect(data.createdAt).toBeGreaterThan(0);
  });

  test("recoverPartialSearch retrieves valid data", () => {
    savePartialSearch("search-2", { count: 10 }, ["MG"], 3);

    const result = recoverPartialSearch("search-2");
    expect(result).toBeTruthy();
    expect(result!.partialResult).toEqual({ count: 10 });
    expect(result!.searchId).toBe("search-2");
  });

  test("recoverPartialSearch returns null for missing search", () => {
    const result = recoverPartialSearch("nonexistent");
    expect(result).toBeNull();
  });

  test("recoverPartialSearch returns null for expired data (>30min)", () => {
    const key = "search_partial_search-3";
    const expired = {
      partialResult: { x: 1 },
      searchId: "search-3",
      ufsCompleted: ["SP"],
      totalUfs: 1,
      updatedAt: Date.now() - 31 * 60 * 1000, // 31 minutes ago
      createdAt: Date.now() - 35 * 60 * 1000,
    };
    localStorage.setItem(key, JSON.stringify(expired));

    const result = recoverPartialSearch("search-3");
    expect(result).toBeNull();
    // Should also clean up the expired entry
    expect(localStorage.getItem(key)).toBeNull();
  });

  test("clearPartialSearch removes the entry", () => {
    savePartialSearch("search-4", { data: true }, ["BA"], 2);
    expect(localStorage.getItem("search_partial_search-4")).toBeTruthy();

    clearPartialSearch("search-4");
    expect(localStorage.getItem("search_partial_search-4")).toBeNull();
  });

  test("cleanupExpiredPartials removes only expired entries", () => {
    // Fresh entry (within TTL)
    savePartialSearch("fresh-1", { fresh: true }, ["SP"], 1);

    // Expired entry (>30 min)
    const expiredKey = "search_partial_expired-1";
    localStorage.setItem(
      expiredKey,
      JSON.stringify({
        partialResult: { old: true },
        searchId: "expired-1",
        ufsCompleted: ["RJ"],
        totalUfs: 1,
        updatedAt: Date.now() - 31 * 60 * 1000,
        createdAt: Date.now() - 35 * 60 * 1000,
      })
    );

    cleanupExpiredPartials();

    // Fresh should remain
    expect(localStorage.getItem("search_partial_fresh-1")).toBeTruthy();
    // Expired should be removed
    expect(localStorage.getItem(expiredKey)).toBeNull();
  });

  test("savePartialSearch preserves createdAt on update", () => {
    const before = Date.now() - 1000;
    const key = "search_partial_search-5";
    localStorage.setItem(
      key,
      JSON.stringify({
        partialResult: { v: 1 },
        searchId: "search-5",
        ufsCompleted: ["SP"],
        totalUfs: 3,
        updatedAt: before,
        createdAt: before,
      })
    );

    savePartialSearch("search-5", { v: 2 }, ["SP", "RJ"], 3);

    const data = JSON.parse(localStorage.getItem(key)!);
    expect(data.createdAt).toBe(before);
    expect(data.updatedAt).toBeGreaterThan(before);
    expect(data.partialResult).toEqual({ v: 2 });
  });
});
