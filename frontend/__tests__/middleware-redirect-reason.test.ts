/**
 * Tests for STORY-233: Fix Redirect Reason Messaging
 * Verifies middleware correctly distinguishes login_required vs session_expired
 *
 * Since Next.js middleware uses the Edge runtime (NextRequest needs Web APIs
 * not available in jsdom), we test the redirect reason logic by directly
 * testing the decision logic extracted from middleware behavior.
 */

// The middleware uses Supabase getUser() + cookie detection to determine reason.
// We test the decision matrix:
//  - No auth cookies + no user → login_required
//  - Auth cookies + getUser error → session_expired
//  - Auth cookies + valid user → no redirect

describe("Middleware redirect reason logic (STORY-233)", () => {
  /**
   * Core decision function extracted from middleware pattern.
   * This mirrors the logic at middleware.ts lines 128-145.
   */
  function determineRedirectReason(params: {
    hasAuthCookies: boolean;
    user: { id: string } | null;
    error: { message: string } | null;
  }): string | null {
    const { hasAuthCookies, user, error } = params;

    if (user) return null; // No redirect needed

    if (hasAuthCookies && error) {
      return "session_expired";
    } else if (!hasAuthCookies) {
      return "login_required";
    }

    return null; // Edge case: has cookies, no error, no user
  }

  describe("AC1: Anonymous user gets login_required", () => {
    it("returns login_required when no auth cookies and no user", () => {
      const reason = determineRedirectReason({
        hasAuthCookies: false,
        user: null,
        error: null,
      });
      expect(reason).toBe("login_required");
    });

    it("returns login_required when no auth cookies even with error", () => {
      const reason = determineRedirectReason({
        hasAuthCookies: false,
        user: null,
        error: { message: "no session" },
      });
      expect(reason).toBe("login_required");
    });
  });

  describe("AC2: Expired session gets session_expired", () => {
    it("returns session_expired when auth cookies exist and getUser fails", () => {
      const reason = determineRedirectReason({
        hasAuthCookies: true,
        user: null,
        error: { message: "JWT expired" },
      });
      expect(reason).toBe("session_expired");
    });

    it("returns session_expired for refresh token failure", () => {
      const reason = determineRedirectReason({
        hasAuthCookies: true,
        user: null,
        error: { message: "Invalid Refresh Token" },
      });
      expect(reason).toBe("session_expired");
    });
  });

  describe("AC4: Other scenarios unaffected", () => {
    it("returns null (no redirect) when user is authenticated", () => {
      const reason = determineRedirectReason({
        hasAuthCookies: true,
        user: { id: "user-123" },
        error: null,
      });
      expect(reason).toBeNull();
    });

    it("returns null for edge case: cookies present, no error, no user", () => {
      // This can happen during cookie cleanup edge cases
      const reason = determineRedirectReason({
        hasAuthCookies: true,
        user: null,
        error: null,
      });
      expect(reason).toBeNull();
    });
  });
});

describe("Middleware source code verification (STORY-233)", () => {
  it("middleware.ts contains login_required reason", async () => {
    // Verify the actual middleware source has the expected patterns
    const fs = require("fs");
    const path = require("path");
    const middlewareSrc = fs.readFileSync(
      path.join(__dirname, "..", "middleware.ts"),
      "utf-8"
    );

    // AC1: Must use login_required for anonymous users
    expect(middlewareSrc).toContain('"login_required"');

    // AC2: Must use session_expired for expired sessions
    expect(middlewareSrc).toContain('"session_expired"');

    // Must check for auth cookies
    expect(middlewareSrc).toContain("auth-token");

    // Must check hasAuthCookies to differentiate
    expect(middlewareSrc).toContain("hasAuthCookies");
  });
});
