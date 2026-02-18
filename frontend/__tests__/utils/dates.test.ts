/**
 * GTM-FIX-032 AC7.10-AC7.11: Tests for date utility helpers.
 */

import { getBrtDate, addDays } from "../../app/buscar/utils/dates";

describe("getBrtDate", () => {
  it("AC7.10: returns YYYY-MM-DD format", () => {
    const result = getBrtDate();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("returns a valid date that can be parsed", () => {
    const result = getBrtDate();
    const parsed = new Date(result + "T12:00:00Z");
    expect(parsed.getTime()).not.toBeNaN();
  });

  it("returns 10-character string", () => {
    const result = getBrtDate();
    expect(result.length).toBe(10);
  });

  it("returns zero-padded month and day", () => {
    const result = getBrtDate();
    const [year, month, day] = result.split("-");
    expect(year.length).toBe(4);
    expect(month.length).toBe(2);
    expect(day.length).toBe(2);
  });
});

describe("addDays", () => {
  it("AC7.11: subtracting 10 days works correctly", () => {
    const result = addDays("2026-02-18", -10);
    expect(result).toBe("2026-02-08");
  });

  it("AC7.11: handles month boundary (Feb → Jan)", () => {
    const result = addDays("2026-02-05", -10);
    expect(result).toBe("2026-01-26");
  });

  it("AC7.11: handles year boundary (Jan → Dec)", () => {
    const result = addDays("2026-01-05", -10);
    expect(result).toBe("2025-12-26");
  });

  it("adding positive days works", () => {
    const result = addDays("2026-02-18", 5);
    expect(result).toBe("2026-02-23");
  });

  it("adding 0 days returns same date", () => {
    const result = addDays("2026-02-18", 0);
    expect(result).toBe("2026-02-18");
  });

  it("handles leap year (Feb 29)", () => {
    // 2028 is a leap year
    const result = addDays("2028-02-28", 1);
    expect(result).toBe("2028-02-29");
  });

  it("handles non-leap year (Feb 28 → Mar 1)", () => {
    const result = addDays("2026-02-28", 1);
    expect(result).toBe("2026-03-01");
  });

  it("returns YYYY-MM-DD format", () => {
    const result = addDays("2026-02-18", -10);
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
