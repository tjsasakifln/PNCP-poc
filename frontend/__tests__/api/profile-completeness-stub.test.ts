/**
 * @jest-environment node
 *
 * UX-434: Stub for /api/profile-completeness must return 200 (never 404) to
 * eliminate console errors during authenticated navigation on Dashboard.
 */
import { GET } from "@/app/api/profile-completeness/route";
import { NextRequest } from "next/server";

const AUTH_HEADER = "Bearer test-token-ux434";

describe("GET /api/profile-completeness (UX-434 stub)", () => {
  it("returns 401 when Authorization header is missing", async () => {
    const req = new NextRequest(
      "http://localhost:3000/api/profile-completeness",
    );
    const res = await GET(req);
    expect(res.status).toBe(401);
  });

  it("returns 200 with default completeness data when authenticated", async () => {
    const req = new NextRequest(
      "http://localhost:3000/api/profile-completeness",
      { headers: { Authorization: AUTH_HEADER } },
    );
    const res = await GET(req);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toMatchObject({
      completeness_pct: null,
      is_complete: false,
      filled_fields: 0,
      total_fields: 0,
      missing_fields: [],
    });
  });

  it("never returns 404", async () => {
    const req = new NextRequest(
      "http://localhost:3000/api/profile-completeness",
      { headers: { Authorization: AUTH_HEADER } },
    );
    const res = await GET(req);
    expect(res.status).not.toBe(404);
  });
});
