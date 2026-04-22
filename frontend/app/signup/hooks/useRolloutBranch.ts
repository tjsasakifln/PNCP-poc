/**
 * Deterministic A/B rollout branch (STORY-CONV-003b AC3).
 *
 * SHA-256(email) % 100 < rolloutPct → "card" branch (collect card at
 * signup). Stable per email so a refresh does not move a user across
 * branches mid-flow.
 *
 * Uses the Web Crypto API (`crypto.subtle.digest`). In jsdom test
 * environments `crypto.subtle` is polyfilled — `@testing-library` setups
 * already ship with it.
 */
export async function sha256Hash(input: string): Promise<Uint8Array> {
  const bytes = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return new Uint8Array(digest);
}

/**
 * Map the hash to a 0-99 bucket by reading the first 4 bytes as an
 * unsigned big-endian int and reducing mod 100. Using 32 bits keeps the
 * distribution close to uniform (cf. 8 bits would give 256 % 100 = 56
 * buckets with +1, skewing slightly).
 */
export function bucketFromHash(hash: Uint8Array): number {
  const view = new DataView(hash.buffer, hash.byteOffset, 4);
  return view.getUint32(0, false) % 100;
}

export function readRolloutPctFromEnv(): number {
  const raw = process.env.NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT;
  if (!raw) return 0;
  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed)) return 0;
  return Math.max(0, Math.min(100, parsed));
}

export type RolloutBranch = "card" | "legacy";

/**
 * Compute the rollout branch for a given email without a React hook —
 * exported so tests can exercise the distribution without rendering.
 */
export async function computeRolloutBranch(
  email: string,
  rolloutPct: number,
): Promise<RolloutBranch> {
  if (rolloutPct <= 0) return "legacy";
  if (rolloutPct >= 100) return "card";
  const hash = await sha256Hash(email.toLowerCase().trim());
  const bucket = bucketFromHash(hash);
  return bucket < rolloutPct ? "card" : "legacy";
}
