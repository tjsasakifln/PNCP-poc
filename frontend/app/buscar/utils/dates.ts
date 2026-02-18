/**
 * GTM-FIX-032 AC5: Robust timezone-safe date helpers for search filters.
 *
 * Replaces the fragile `new Date(new Date().toLocaleString(...))` pattern
 * with Intl.DateTimeFormat for reliable São Paulo timezone handling.
 */

/**
 * Get current date in São Paulo timezone as YYYY-MM-DD string.
 * Uses Intl.DateTimeFormat("en-CA") which natively formats as YYYY-MM-DD.
 */
export function getBrtDate(): string {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(new Date());
}

/**
 * Add (or subtract) days from a YYYY-MM-DD date string.
 * Uses noon UTC to avoid DST boundary edge cases.
 */
export function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T12:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().split("T")[0];
}
