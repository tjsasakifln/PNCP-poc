/**
 * Tests for reliability score calculation (GTM-RESILIENCE-A05 AC18).
 */
import {
  calculateReliability,
  freshnessScore,
  methodScore,
  deriveMethod,
  minutesSince,
} from "../../app/buscar/utils/reliability";

describe("freshnessScore", () => {
  it("returns 1.0 for < 5 minutes", () => {
    expect(freshnessScore(0)).toBe(1.0);
    expect(freshnessScore(4)).toBe(1.0);
  });

  it("returns 0.7 for 5-59 minutes", () => {
    expect(freshnessScore(5)).toBe(0.7);
    expect(freshnessScore(59)).toBe(0.7);
  });

  it("returns 0.4 for 1-6 hours", () => {
    expect(freshnessScore(60)).toBe(0.4);
    expect(freshnessScore(359)).toBe(0.4);
  });

  it("returns 0.1 for > 6 hours", () => {
    expect(freshnessScore(360)).toBe(0.1);
    expect(freshnessScore(1440)).toBe(0.1);
  });
});

describe("methodScore", () => {
  it("returns 1.0 for live", () => {
    expect(methodScore("live")).toBe(1.0);
  });

  it("returns 0.8 for cache_fresh", () => {
    expect(methodScore("cache_fresh")).toBe(0.8);
  });

  it("returns 0.4 for cache_stale", () => {
    expect(methodScore("cache_stale")).toBe(0.4);
  });
});

describe("deriveMethod", () => {
  it("returns live for undefined/live/degraded response state", () => {
    expect(deriveMethod(undefined)).toBe("live");
    expect(deriveMethod("live")).toBe("live");
    expect(deriveMethod("degraded")).toBe("live");
  });

  it("returns cache_fresh for cached + fresh", () => {
    expect(deriveMethod("cached", "fresh")).toBe("cache_fresh");
  });

  it("returns cache_stale for cached + stale or no status", () => {
    expect(deriveMethod("cached", "stale")).toBe("cache_stale");
    expect(deriveMethod("cached")).toBe("cache_stale");
  });

  it("returns cache_stale for empty_failure", () => {
    expect(deriveMethod("empty_failure")).toBe("cache_stale");
  });
});

describe("calculateReliability", () => {
  it("AC18: coverage=100%, freshness<5min, method=live -> Alta", () => {
    const result = calculateReliability(100, 0, "live");
    expect(result.level).toBe("Alta");
    expect(result.score).toBe(1.0);
  });

  it("AC18: coverage=50%, freshness>6h, method=cache_stale -> Baixa", () => {
    const result = calculateReliability(50, 400, "cache_stale");
    // 0.5*0.5 + 0.1*0.3 + 0.4*0.2 = 0.25 + 0.03 + 0.08 = 0.36
    expect(result.level).toBe("Baixa");
    expect(result.score).toBe(0.36);
  });

  it("coverage=78%, freshness=30min, method=live -> Media", () => {
    const result = calculateReliability(78, 30, "live");
    // 0.78*0.5 + 0.7*0.3 + 1.0*0.2 = 0.39 + 0.21 + 0.20 = 0.80
    expect(result.level).toBe("Media");
    expect(result.score).toBe(0.8);
  });

  it("coverage=0%, -> Baixa", () => {
    const result = calculateReliability(0, 0, "live");
    // 0*0.5 + 1.0*0.3 + 1.0*0.2 = 0 + 0.30 + 0.20 = 0.50
    expect(result.level).toBe("Media");
    expect(result.score).toBe(0.5);
  });

  it("clamps coverage to 0-100", () => {
    const result = calculateReliability(150, 0, "live");
    // clamped to 100: 1.0*0.5 + 1.0*0.3 + 1.0*0.2 = 1.0
    expect(result.score).toBe(1.0);
  });
});

describe("minutesSince", () => {
  it("returns 0 for future timestamp", () => {
    const future = new Date(Date.now() + 60000).toISOString();
    expect(minutesSince(future)).toBe(0);
  });

  it("returns correct minutes for past timestamp", () => {
    const tenMinAgo = new Date(Date.now() - 10 * 60000).toISOString();
    const result = minutesSince(tenMinAgo);
    // Allow 1 minute tolerance for test execution time
    expect(result).toBeGreaterThanOrEqual(9);
    expect(result).toBeLessThanOrEqual(11);
  });
});
