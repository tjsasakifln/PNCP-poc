/**
 * STAB-006 AC2: Tests for humanized error messages.
 */

import { getHumanizedError } from "../../lib/error-messages";

describe("getHumanizedError (STAB-006 AC2)", () => {
  test("timeout error (524) returns yellow tone with scope reduction", () => {
    const result = getHumanizedError(524, "Gateway Timeout");
    expect(result.tone).toBe("yellow");
    expect(result.suggestReduceScope).toBe(true);
    expect(result.actionLabel).toBe("Tentar novamente");
    expect(result.secondaryActionLabel).toBe("Reduzir escopo");
    expect(result.message).toContain("demorou");
  });

  test("504 timeout returns yellow tone", () => {
    const result = getHumanizedError(504, "Gateway Timeout");
    expect(result.tone).toBe("yellow");
    expect(result.suggestReduceScope).toBe(true);
  });

  test("message containing 'timeout' triggers timeout path", () => {
    const result = getHumanizedError(null, "Request timeout exceeded");
    expect(result.tone).toBe("yellow");
    expect(result.suggestReduceScope).toBe(true);
  });

  test("partial failure shows count", () => {
    const result = getHumanizedError(null, null, 5, 10);
    expect(result.tone).toBe("blue");
    expect(result.message).toContain("5 de 10 estados");
    expect(result.suggestReduceScope).toBe(false);
  });

  test("502 error returns blue tone (server updating)", () => {
    const result = getHumanizedError(502, "Bad Gateway");
    expect(result.tone).toBe("blue");
    expect(result.message).toContain("atualizando");
    expect(result.suggestReduceScope).toBe(false);
  });

  test("503 error returns blue tone", () => {
    const result = getHumanizedError(503, "Service Unavailable");
    expect(result.tone).toBe("blue");
  });

  test("429 rate limit returns yellow tone", () => {
    const result = getHumanizedError(429, "Too Many Requests");
    expect(result.tone).toBe("yellow");
    expect(result.message).toContain("simultâneas");
  });

  test("network error returns yellow tone", () => {
    const result = getHumanizedError(null, "Failed to fetch");
    expect(result.tone).toBe("yellow");
    expect(result.message).toContain("conexão");
  });

  test("unknown error returns blue tone with generic message", () => {
    const result = getHumanizedError(null, null);
    expect(result.tone).toBe("blue");
    expect(result.actionLabel).toBe("Tentar novamente");
  });

  test("partial failure with 0 completed is not treated as partial", () => {
    const result = getHumanizedError(null, null, 0, 10);
    // 0 of 10 is not "partial" — it's a full failure
    expect(result.tone).toBe("blue");
    expect(result.message).not.toContain("de 10 estados");
  });
});
