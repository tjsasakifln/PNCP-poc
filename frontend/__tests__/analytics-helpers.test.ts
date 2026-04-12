/**
 * STORY-370 AC7: Tests for analytics-helpers.ts
 */
import { getDaysInTrial } from '../lib/analytics-helpers';

describe('getDaysInTrial', () => {
  it('returns -1 for null input', () => {
    expect(getDaysInTrial(null)).toBe(-1);
  });

  it('returns -1 for undefined input', () => {
    expect(getDaysInTrial(undefined)).toBe(-1);
  });

  it('returns -1 for invalid date string', () => {
    expect(getDaysInTrial('not-a-date')).toBe(-1);
  });

  it('returns 0 for today', () => {
    const today = new Date().toISOString();
    const result = getDaysInTrial(today);
    expect(result).toBeGreaterThanOrEqual(0);
    expect(result).toBeLessThan(1);
  });

  it('returns approximately 7 for a date 7 days ago', () => {
    const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
    const result = getDaysInTrial(sevenDaysAgo);
    expect(result).toBeGreaterThanOrEqual(6);
    expect(result).toBeLessThanOrEqual(8);
  });

  it('returns positive value for past date', () => {
    const past = new Date(Date.now() - 100 * 24 * 60 * 60 * 1000).toISOString();
    expect(getDaysInTrial(past)).toBeGreaterThan(0);
  });
});
