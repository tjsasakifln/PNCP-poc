/**
 * STORY-CONV-003b AC5: rollout distribution + determinism tests.
 *
 * Requirements:
 * - Same email → same bucket (stable across refresh).
 * - 50% rollout → ~50% of 1000 emails go to "card" branch (tolerance ±5%).
 * - PCT=0 → all legacy; PCT=100 → all card.
 */
import {
  computeRolloutBranch,
  bucketFromHash,
  sha256Hash,
} from "../../app/signup/hooks/useRolloutBranch";

describe("rollout hash", () => {
  it("is stable: same email always maps to same bucket", async () => {
    const email = "founder@example.com.br";
    const h1 = await sha256Hash(email);
    const h2 = await sha256Hash(email);
    expect(bucketFromHash(h1)).toBe(bucketFromHash(h2));
  });

  it("normalizes email casing before hashing", async () => {
    const a = await computeRolloutBranch("Foo@Bar.com", 50);
    const b = await computeRolloutBranch("foo@bar.com", 50);
    expect(a).toBe(b);
  });

  it("PCT=0 routes everyone to legacy", async () => {
    for (const email of ["a@x.com", "b@x.com", "c@x.com"]) {
      expect(await computeRolloutBranch(email, 0)).toBe("legacy");
    }
  });

  it("PCT=100 routes everyone to card", async () => {
    for (const email of ["a@x.com", "b@x.com", "c@x.com"]) {
      expect(await computeRolloutBranch(email, 100)).toBe("card");
    }
  });

  it("50/50 distribution over N=1000 is within ±5%", async () => {
    const N = 1000;
    let cardCount = 0;
    for (let i = 0; i < N; i++) {
      // Use varied domains so we don't accidentally hit the same hash bucket
      // cluster. Real emails are the distribution; synthetic still exercises
      // the uniformity of SHA-256.
      const email = `user${i}+seed@example.com`;
      const branch = await computeRolloutBranch(email, 50);
      if (branch === "card") cardCount++;
    }
    const pct = (cardCount / N) * 100;
    expect(pct).toBeGreaterThanOrEqual(45);
    expect(pct).toBeLessThanOrEqual(55);
  });

  it("bucketFromHash always returns 0-99", async () => {
    const emails = [
      "alice@corp.com.br",
      "bob@foo.io",
      "c@d.e",
      "loong.user.name+tag@sub.domain.co.uk",
    ];
    for (const e of emails) {
      const b = bucketFromHash(await sha256Hash(e));
      expect(b).toBeGreaterThanOrEqual(0);
      expect(b).toBeLessThanOrEqual(99);
    }
  });
});
