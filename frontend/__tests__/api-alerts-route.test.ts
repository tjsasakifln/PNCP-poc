/**
 * @jest-environment node
 *
 * UX-434: /api/alerts is now a stub returning 200 (never proxying to backend).
 * Previous proxy tests (STORY-301) replaced — stub eliminates 404 console errors.
 */
import { GET, POST } from "../app/api/alerts/route";
import { NextRequest } from "next/server";

const AUTH = "Bearer test-token-123";

describe("/api/alerts route handlers", () => {
  describe("GET /api/alerts", () => {
    it("returns 200 with empty array when authenticated", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts", {
        headers: { Authorization: AUTH },
      });
      const res = await GET(req);
      expect(res.status).toBe(200);
      const data = await res.json();
      expect(Array.isArray(data)).toBe(true);
      expect(data).toHaveLength(0);
    });

    it("returns 401 when no authorization header", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts");
      const res = await GET(req);
      const data = await res.json();
      expect(res.status).toBe(401);
      expect(data.message).toBeDefined();
    });

    it("never returns 404 (AC3/AC4 — stub eliminates ghost 404s)", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts", {
        headers: { Authorization: AUTH },
      });
      const res = await GET(req);
      expect(res.status).not.toBe(404);
    });
  });

  describe("POST /api/alerts", () => {
    it("returns 200 when authenticated", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts", {
        method: "POST",
        headers: { Authorization: AUTH },
        body: JSON.stringify({ name: "Alerta Teste" }),
      });
      const res = await POST(req);
      expect(res.status).toBe(200);
    });

    it("returns 401 for POST without auth header", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts", {
        method: "POST",
        body: JSON.stringify({ name: "Test" }),
      });
      const res = await POST(req);
      const data = await res.json();
      expect(res.status).toBe(401);
      expect(data.message).toBeDefined();
    });

    it("never returns 404", async () => {
      const req = new NextRequest("http://localhost:3000/api/alerts", {
        method: "POST",
        headers: { Authorization: AUTH },
        body: JSON.stringify({}),
      });
      const res = await POST(req);
      expect(res.status).not.toBe(404);
    });
  });
});
