/**
 * Calculate the difference in days between two date strings.
 *
 * @param date1 - ISO date string (YYYY-MM-DD)
 * @param date2 - ISO date string (YYYY-MM-DD)
 * @returns Number of days between the two dates (always positive)
 */
export function dateDiffInDays(date1: string, date2: string): number {
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}
