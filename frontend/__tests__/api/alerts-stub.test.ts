/**
 * @jest-environment node
 *
 * UX-434: Stub for /api/alerts must return 200 (never 404) to eliminate
 * console errors during authenticated navigation.
 */
import { GET, POST } from "@/app/api/alerts/route";
import { NextRequest } from "next/server";

const AUTH_HEADER = "Bearer test-token-ux434";

describe("GET /api/alerts (UX-434 stub)", () => {
  it("returns 401 when Authorization header is missing", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts");
    const res = await GET(req);
    expect(res.status).toBe(401);
  });

  it("returns 200 with empty array when authenticated", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts", {
      headers: { Authorization: AUTH_HEADER },
    });
    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body).toHaveLength(0);
  });

  it("never returns 404", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts", {
      headers: { Authorization: AUTH_HEADER },
    });
    const res = await GET(req);
    expect(res.status).not.toBe(404);
  });
});

describe("POST /api/alerts (UX-434 stub)", () => {
  it("returns 401 when Authorization header is missing", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts", {
      method: "POST",
      body: JSON.stringify({ name: "Alerta Teste" }),
    });
    const res = await POST(req);
    expect(res.status).toBe(401);
  });

  it("returns 200 when authenticated", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts", {
      method: "POST",
      headers: { Authorization: AUTH_HEADER },
      body: JSON.stringify({ name: "Alerta Teste" }),
    });
    const res = await POST(req);
    expect(res.status).toBe(200);
  });

  it("never returns 404", async () => {
    const req = new NextRequest("http://localhost:3000/api/alerts", {
      method: "POST",
      headers: { Authorization: AUTH_HEADER },
      body: JSON.stringify({}),
    });
    const res = await POST(req);
    expect(res.status).not.toBe(404);
  });
});
