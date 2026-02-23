/**
 * @jest-environment node
 */

/**
 * CRIT-017: Tests for proxy-error-handler.ts
 *
 * AC11: proxy returns structured error when backend returns HTML
 * AC12: proxy returns structured error when backend returns 502
 * AC13: proxy returns structured error when fetch throws (network error)
 */

import {
  sanitizeProxyError,
  sanitizeNetworkError,
  createUnavailableResponse,
} from "../lib/proxy-error-handler";

const EXPECTED_MSG =
  "Nossos servidores estão sendo atualizados. Tente novamente em alguns instantes.";

describe("proxy-error-handler", () => {
  // ─── AC3: "Application not found" (Railway) ──────────────────────
  describe("Railway infrastructure errors", () => {
    it("sanitizes 'Application not found' plain text (502)", () => {
      const result = sanitizeProxyError(502, "Application not found", "text/html");
      expect(result).not.toBeNull();
      const body = result!.json ? undefined : null;
      // NextResponse.json stores data internally — verify via status + headers
      expect(result!.status).toBe(502);
      expect(result!.headers.get("X-Error-Source")).toBe("proxy");
    });

    it("sanitizes 'Application not found' even with 404 status", () => {
      const result = sanitizeProxyError(404, "Application not found", "text/plain");
      expect(result).not.toBeNull();
      expect(result!.headers.get("X-Error-Source")).toBe("proxy");
    });

    it("sanitizes 'Application not found' regardless of content-type", () => {
      const result = sanitizeProxyError(502, "Application not found", "application/json");
      expect(result).not.toBeNull();
      expect(result!.headers.get("X-Error-Source")).toBe("proxy");
    });
  });

  // ─── AC4: "Bad Gateway" (nginx) ──────────────────────────────────
  describe("nginx infrastructure errors", () => {
    it("sanitizes 'Bad Gateway' HTML", () => {
      const html = "<html><body><h1>502 Bad Gateway</h1></body></html>";
      const result = sanitizeProxyError(502, html, "text/html");
      expect(result).not.toBeNull();
      expect(result!.headers.get("X-Error-Source")).toBe("proxy");
    });

    it("sanitizes 'Service Unavailable' text", () => {
      const result = sanitizeProxyError(503, "Service Unavailable", "text/plain");
      expect(result).not.toBeNull();
      expect(result!.status).toBe(503);
    });

    it("sanitizes 'Gateway Timeout' text", () => {
      const result = sanitizeProxyError(504, "Gateway Timeout", "text/plain");
      expect(result).not.toBeNull();
      expect(result!.status).toBe(504);
    });
  });

  // ─── AC1: Non-JSON responses ─────────────────────────────────────
  describe("non-JSON error responses", () => {
    it("sanitizes text/html error response", () => {
      const result = sanitizeProxyError(500, "Internal Server Error", "text/html");
      expect(result).not.toBeNull();
      expect(result!.status).toBe(503); // 500 is not in UNAVAILABLE_STATUSES, remapped to 503
    });

    it("sanitizes text/plain error response", () => {
      const result = sanitizeProxyError(400, "Some random error", "text/plain");
      expect(result).not.toBeNull();
    });

    it("sanitizes response with null content-type on error", () => {
      const result = sanitizeProxyError(500, "error", null);
      expect(result).not.toBeNull();
    });

    it("does NOT sanitize 200 OK with non-JSON (not an error)", () => {
      const result = sanitizeProxyError(200, "OK", "text/plain");
      expect(result).toBeNull();
    });
  });

  // ─── AC2: 502/503/504 status codes ──────────────────────────────
  describe("unavailable status codes (502/503/504)", () => {
    it("sanitizes 502 with unstructured JSON body", () => {
      const result = sanitizeProxyError(
        502,
        '{"status": "error"}',
        "application/json",
      );
      expect(result).not.toBeNull();
      expect(result!.status).toBe(502);
    });

    it("sanitizes 503 with empty body", () => {
      const result = sanitizeProxyError(503, "", "application/json");
      expect(result).not.toBeNull();
    });

    it("sanitizes 504 with non-JSON body", () => {
      const result = sanitizeProxyError(504, "timeout", "text/plain");
      expect(result).not.toBeNull();
      expect(result!.status).toBe(504);
    });

    it("passes through 502 with structured backend error (has detail)", () => {
      const body = JSON.stringify({ detail: "PNCP rate limited" });
      const result = sanitizeProxyError(502, body, "application/json");
      expect(result).toBeNull(); // safe to pass through
    });

    it("passes through 503 with structured backend error (has message)", () => {
      const body = JSON.stringify({ message: "Quota exceeded" });
      const result = sanitizeProxyError(503, body, "application/json");
      expect(result).toBeNull();
    });

    it("passes through 502 with structured backend error (has error_code)", () => {
      const body = JSON.stringify({ error_code: "RATE_LIMIT" });
      const result = sanitizeProxyError(502, body, "application/json");
      expect(result).toBeNull();
    });
  });

  // ─── Non-502/503/504 JSON errors pass through ───────────────────
  describe("non-unavailable status codes", () => {
    it("passes through 401 JSON error", () => {
      const body = JSON.stringify({ detail: "Not authenticated" });
      const result = sanitizeProxyError(401, body, "application/json");
      expect(result).toBeNull();
    });

    it("passes through 400 JSON error", () => {
      const body = JSON.stringify({ detail: "Validation error" });
      const result = sanitizeProxyError(400, body, "application/json");
      expect(result).toBeNull();
    });

    it("passes through 429 JSON error", () => {
      const body = JSON.stringify({ detail: "Rate limited" });
      const result = sanitizeProxyError(429, body, "application/json");
      expect(result).toBeNull();
    });

    it("passes through 500 JSON error with structured detail", () => {
      const body = JSON.stringify({ detail: "Internal error" });
      const result = sanitizeProxyError(500, body, "application/json");
      expect(result).toBeNull();
    });
  });

  // ─── HTML error pages ─────────────────────────────────────────────
  describe("HTML error pages", () => {
    it("sanitizes <!DOCTYPE html> pages", () => {
      const html = "<!DOCTYPE html><html><body>Error</body></html>";
      const result = sanitizeProxyError(502, html, "text/html");
      expect(result).not.toBeNull();
    });

    it("sanitizes <html> pages without doctype", () => {
      const html = "<html><head></head><body>502</body></html>";
      const result = sanitizeProxyError(502, html, "text/html");
      expect(result).not.toBeNull();
    });
  });

  // ─── AC5: X-Error-Source header ──────────────────────────────────
  describe("X-Error-Source header (AC5)", () => {
    it("sets X-Error-Source: proxy on sanitized responses", () => {
      const result = sanitizeProxyError(502, "Application not found", "text/html");
      expect(result).not.toBeNull();
      expect(result!.headers.get("X-Error-Source")).toBe("proxy");
    });

    it("createUnavailableResponse sets X-Error-Source: proxy", () => {
      const result = createUnavailableResponse(503);
      expect(result.headers.get("X-Error-Source")).toBe("proxy");
      expect(result.status).toBe(503);
    });

    it("createUnavailableResponse defaults to 503 for non-standard status", () => {
      const result = createUnavailableResponse(400);
      expect(result.status).toBe(503);
    });
  });

  // ─── AC13: Network errors ────────────────────────────────────────
  describe("sanitizeNetworkError (AC13)", () => {
    it("returns sanitized response for connection refused", () => {
      const result = sanitizeNetworkError(new Error("connect ECONNREFUSED"));
      expect(result).not.toBeNull();
      expect(result.status).toBe(503);
      expect(result.headers.get("X-Error-Source")).toBe("proxy");
    });

    it("returns sanitized response for fetch failed", () => {
      const result = sanitizeNetworkError(new TypeError("fetch failed"));
      expect(result.status).toBe(503);
    });

    it("returns sanitized response for non-Error objects", () => {
      const result = sanitizeNetworkError("some string error");
      expect(result.status).toBe(503);
    });
  });

  // ─── Response body content verification ──────────────────────────
  describe("response body content", () => {
    it("createUnavailableResponse contains friendly PT-BR message", async () => {
      const result = createUnavailableResponse(503);
      const body = await result.json();
      expect(body.error).toBe(EXPECTED_MSG);
      expect(body.message).toBe(EXPECTED_MSG);
      expect(body.error_code).toBe("BACKEND_UNAVAILABLE");
      expect(body.retry_after_seconds).toBe(30);
    });

    it("sanitized response never contains 'Application not found'", async () => {
      const result = sanitizeProxyError(502, "Application not found", "text/html");
      const body = await result!.json();
      expect(body.error).not.toContain("Application not found");
      expect(body.message).not.toContain("Application not found");
      expect(body.error_code).toBe("BACKEND_UNAVAILABLE");
    });

    it("sanitized response never contains 'Bad Gateway'", async () => {
      const result = sanitizeProxyError(502, "<h1>Bad Gateway</h1>", "text/html");
      const body = await result!.json();
      expect(body.error).not.toContain("Bad Gateway");
      expect(body.message).not.toContain("Bad Gateway");
    });
  });

  // ─── GTM-UX-004 T1: Never returns "pending" as silent fallback ──────────
  describe("GTM-UX-004 T1: Never returns 'pending' as silent fallback", () => {
    it("sanitizeProxyError on 502 body does NOT contain 'pending'", async () => {
      const result = sanitizeProxyError(502, "Bad Gateway", "text/html");
      expect(result).not.toBeNull();
      const body = await result!.json();
      expect(body.status).not.toBe("pending");
      expect(body.error).not.toContain("pending");
    });

    it("sanitizeProxyError on 503 body does NOT contain 'pending'", async () => {
      const result = sanitizeProxyError(503, "Service Unavailable", "text/html");
      expect(result).not.toBeNull();
      const body = await result!.json();
      expect(body.status).not.toBe("pending");
    });

    it("sanitizeNetworkError body does NOT contain 'pending'", async () => {
      const result = sanitizeNetworkError(new Error("ECONNREFUSED"));
      const body = await result.json();
      expect(body.status).not.toBe("pending");
      expect(body.error).not.toContain("pending");
    });
  });
});
