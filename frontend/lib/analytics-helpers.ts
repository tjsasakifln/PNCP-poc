/**
 * Analytics helper utilities.
 * STORY-370 AC6: getDaysInTrial helper.
 */

/**
 * Calculate number of days the user has been in trial.
 * @param trialStartedAt - ISO date string (e.g., profile.created_at)
 * @returns Days since trial started, or -1 if trialStartedAt is null/invalid
 */
export function getDaysInTrial(trialStartedAt: string | null | undefined): number {
  if (!trialStartedAt) return -1;
  try {
    const startMs = new Date(trialStartedAt).getTime();
    if (isNaN(startMs)) return -1;
    return Math.floor((Date.now() - startMs) / (1000 * 60 * 60 * 24));
  } catch {
    return -1;
  }
}
