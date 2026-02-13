/**
 * @jest-environment node
 *
 * STORY-218 Track 4 (AC12-AC14): Rewritten download route tests.
 * Replaces deprecated downloadCache-based tests with fs/promises mocks.
 *
 * Covers:
 *   - Authentication (Bearer token requirement)
 *   - Signed URL redirect (allowed hosts, protocol enforcement, open redirect prevention)
 *   - Legacy filesystem download (valid UUID, file found/not found)
 *   - Input validation (missing params, invalid UUID, path traversal)
 */

/* -------------------------------------------------------------------------- */
/*  Mocks — must be declared before any import that triggers the route module */
/* -------------------------------------------------------------------------- */

const mockReadFile = jest.fn();

jest.mock("fs/promises", () => ({
  readFile: (...args: unknown[]) => mockReadFile(...args),
}));

/* -------------------------------------------------------------------------- */
/*  Imports                                                                   */
/* -------------------------------------------------------------------------- */

import { GET } from "@/app/api/download/route";
import { NextRequest } from "next/server";

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

const BASE_URL = "http://localhost:3000/api/download";

const VALID_UUID = "550e8400-e29b-41d4-a716-446655440000";

/** Allowed Supabase host taken from the route's ALLOWED_REDIRECT_HOSTS. */
const ALLOWED_HOST = "fqqyovlzdzimiwfofdjk.supabase.co";

/**
 * Build a NextRequest with an optional Bearer token and query string.
 */
function buildRequest(
  params: Record<string, string> = {},
  options: { auth?: boolean; authValue?: string; headers?: Record<string, string> } = {}
): NextRequest {
  const url = new URL(BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const headers: Record<string, string> = { ...(options.headers ?? {}) };
  if (options.auth !== false) {
    headers["Authorization"] = options.authValue ?? "Bearer test-jwt-token";
  }

  return new NextRequest(url.toString(), { headers });
}

/* -------------------------------------------------------------------------- */
/*  Test suite                                                                */
/* -------------------------------------------------------------------------- */

describe("GET /api/download", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Suppress expected console.warn / console.error / console.log noise.
    jest.spyOn(console, "log").mockImplementation();
    jest.spyOn(console, "warn").mockImplementation();
    jest.spyOn(console, "error").mockImplementation();
    process.env.NEXT_PUBLIC_APP_NAME = "SmartLic.tech";
  });

  /* ======================================================================== */
  /*  1. Authentication                                                       */
  /* ======================================================================== */

  describe("Authentication", () => {
    it("should return 401 when Authorization header is missing", async () => {
      const request = buildRequest({ id: VALID_UUID }, { auth: false });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toContain("Autenticacao necessaria");
    });

    it("should return 401 when Authorization header is not Bearer", async () => {
      const request = buildRequest(
        { id: VALID_UUID },
        { auth: false, headers: { Authorization: "Basic dXNlcjpwYXNz" } }
      );

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(401);
      expect(data.message).toContain("Autenticacao necessaria");
    });
  });

  /* ======================================================================== */
  /*  2. Signed URL redirect                                                  */
  /* ======================================================================== */

  describe("Signed URL redirect", () => {
    it("should redirect (307) when url param points to an allowed host", async () => {
      const signedUrl = `https://${ALLOWED_HOST}/storage/v1/object/sign/exports/file.xlsx?token=abc`;
      const request = buildRequest({ url: signedUrl });

      const response = await GET(request);

      expect(response.status).toBe(307);
      expect(response.headers.get("Location")).toBe(signedUrl);
    });

    it("should return 400 when url param uses non-https protocol", async () => {
      const httpUrl = `http://${ALLOWED_HOST}/file.xlsx`;
      const request = buildRequest({ url: httpUrl });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toContain("protocolo");
    });

    it("should return 400 when url param points to an unauthorized host (open redirect prevention)", async () => {
      const evilUrl = "https://evil.example.com/phishing";
      const request = buildRequest({ url: evilUrl });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toMatch(/dom[ií]nio n[aã]o autorizado/i);
    });

    it("should return 400 when url param is a malformed URL", async () => {
      const request = buildRequest({ url: "not-a-valid-url" });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toContain("URL de download");
    });

    it("should accept second allowed Supabase host (.supabase.in)", async () => {
      const signedUrl = "https://fqqyovlzdzimiwfofdjk.supabase.in/storage/v1/object/sign/file.xlsx?token=xyz";
      const request = buildRequest({ url: signedUrl });

      const response = await GET(request);

      expect(response.status).toBe(307);
      expect(response.headers.get("Location")).toBe(signedUrl);
    });
  });

  /* ======================================================================== */
  /*  3. Missing parameters                                                   */
  /* ======================================================================== */

  describe("Missing parameters", () => {
    it("should return 400 when neither id nor url is provided", async () => {
      const request = buildRequest();

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toBe("ID ou URL obrigatório");
    });
  });

  /* ======================================================================== */
  /*  4. UUID validation (path traversal prevention)                          */
  /* ======================================================================== */

  describe("UUID validation", () => {
    it("should return 400 for a plaintext non-UUID id", async () => {
      const request = buildRequest({ id: "not-a-uuid" });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toBe("ID de download inválido");
    });

    it("should return 400 for a path traversal attempt in id", async () => {
      const request = buildRequest({ id: "../../etc/passwd" });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toBe("ID de download inválido");
    });

    it("should return 400 for special characters in id", async () => {
      const request = buildRequest({ id: "test%20with%20spaces" });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.message).toBe("ID de download inválido");
    });
  });

  /* ======================================================================== */
  /*  5. Filesystem download (legacy mode)                                    */
  /* ======================================================================== */

  describe("Filesystem download (legacy mode)", () => {
    it("should return 200 with Excel content when file exists", async () => {
      const testData = Buffer.from("fake-excel-binary-data");
      mockReadFile.mockResolvedValueOnce(testData);

      const request = buildRequest({ id: VALID_UUID });

      const response = await GET(request);

      expect(response.status).toBe(200);
      expect(response.headers.get("Content-Type")).toBe(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      );

      // Verify binary content round-trips correctly
      const arrayBuffer = await response.arrayBuffer();
      const responseBuffer = Buffer.from(arrayBuffer);
      expect(responseBuffer.toString()).toBe("fake-excel-binary-data");
    });

    it("should set Content-Disposition with app name and current date", async () => {
      const testData = Buffer.from("excel");
      mockReadFile.mockResolvedValueOnce(testData);

      const request = buildRequest({ id: VALID_UUID });

      const response = await GET(request);
      const contentDisposition = response.headers.get("Content-Disposition");

      expect(contentDisposition).toContain("attachment");
      expect(contentDisposition).toContain("SmartLic_tech");

      const today = new Date().toISOString().split("T")[0];
      expect(contentDisposition).toContain(today);
      expect(contentDisposition).toContain(".xlsx");
    });

    it("should use fallback app name when NEXT_PUBLIC_APP_NAME is unset", async () => {
      delete process.env.NEXT_PUBLIC_APP_NAME;
      const testData = Buffer.from("excel");
      mockReadFile.mockResolvedValueOnce(testData);

      const request = buildRequest({ id: VALID_UUID });

      const response = await GET(request);
      const contentDisposition = response.headers.get("Content-Disposition");

      // Fallback is "SmartLic.tech" hardcoded in route, which becomes "SmartLic_tech"
      expect(contentDisposition).toContain("SmartLic_tech");
    });

    it("should call readFile with correct path based on UUID", async () => {
      const testData = Buffer.from("excel");
      mockReadFile.mockResolvedValueOnce(testData);

      const request = buildRequest({ id: VALID_UUID });

      await GET(request);

      expect(mockReadFile).toHaveBeenCalledTimes(1);
      const calledPath = mockReadFile.mock.calls[0][0] as string;
      expect(calledPath).toContain(`bidiq_${VALID_UUID}.xlsx`);
    });

    it("should return 404 when the file does not exist on disk", async () => {
      const error = new Error("ENOENT: no such file or directory") as NodeJS.ErrnoException;
      error.code = "ENOENT";
      mockReadFile.mockRejectedValueOnce(error);

      const request = buildRequest({ id: VALID_UUID });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.message).toContain("Download expirado ou inválido");
    });

    it("should return 404 when readFile throws any error", async () => {
      mockReadFile.mockRejectedValueOnce(new Error("Permission denied"));

      const request = buildRequest({ id: VALID_UUID });

      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.message).toContain("Download expirado ou inválido");
    });
  });
});
