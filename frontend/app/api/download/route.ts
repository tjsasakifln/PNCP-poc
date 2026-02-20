import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

// STORY-210 AC5: Allowed domains for redirect URLs (Supabase storage only)
const ALLOWED_REDIRECT_HOSTS = [
  "fqqyovlzdzimiwfofdjk.supabase.co",
  "fqqyovlzdzimiwfofdjk.supabase.in",
];

// STORY-210 AC5: UUID v4 regex for download ID validation
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function GET(request: NextRequest) {
  // Require authentication for downloads
  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return NextResponse.json(
      { message: "Autenticacao necessaria. Faca login para continuar." },
      { status: 401 }
    );
  }

  // CRIT-004 AC3: Forward X-Request-ID and X-Correlation-ID for tracing
  const requestId = request.headers.get("X-Request-ID");
  const correlationId = request.headers.get("X-Correlation-ID");
  if (requestId) {
    console.log(`[download] Request ID: ${requestId}`);
  }
  if (correlationId) {
    console.log(`[download] Correlation ID: ${correlationId}`);
  }

  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get("id");
  const url = searchParams.get("url");

  // STORY-202 CROSS-C02: Priority 1 - Signed URL from object storage (redirect)
  if (url) {
    // STORY-210 AC5: Validate redirect URL against allowed domains
    try {
      const parsed = new URL(url);
      if (parsed.protocol !== "https:") {
        return NextResponse.json(
          { message: "URL de download inválida: protocolo não permitido" },
          { status: 400 }
        );
      }
      if (!ALLOWED_REDIRECT_HOSTS.includes(parsed.hostname)) {
        console.warn(`[download] Blocked redirect to unauthorized host: ${parsed.hostname}`);
        return NextResponse.json(
          { message: "URL de download inválida: domínio não autorizado" },
          { status: 400 }
        );
      }
    } catch {
      return NextResponse.json(
        { message: "URL de download inválida" },
        { status: 400 }
      );
    }

    console.log(`✅ Redirecting to signed URL (object storage)`);
    return NextResponse.redirect(url);
  }

  // Priority 2: Legacy filesystem download by ID
  if (!id) {
    return NextResponse.json(
      { message: "ID ou URL obrigatório" },
      { status: 400 }
    );
  }

  // STORY-210 AC5: Validate ID is a UUID to prevent path traversal
  if (!UUID_REGEX.test(id)) {
    console.warn(`[download] Blocked invalid download ID: ${id.substring(0, 50)}`);
    return NextResponse.json(
      { message: "ID de download inválido" },
      { status: 400 }
    );
  }

  // Read from filesystem (legacy mode / storage fallback)
  const tmpDir = tmpdir();
  const filePath = join(tmpDir, `bidiq_${id}.xlsx`);

  try {
    const buffer = await readFile(filePath);
    const appNameSlug = (process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech").replace(/[\s.]+/g, '_');
    const filename = `${appNameSlug}_${new Date().toISOString().split("T")[0]}.xlsx`;

    console.log(`✅ Download served from filesystem: ${id} (${buffer.length} bytes) [legacy mode]`);

    // Convert Buffer to Uint8Array for Next.js Response
    const uint8Array = new Uint8Array(buffer);

    return new NextResponse(uint8Array, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": `attachment; filename="${filename}"`
      }
    });
  } catch (error) {
    console.error(`❌ Download failed for ${id}:`, error);
    return NextResponse.json(
      { message: "Download expirado ou inválido. Faça uma nova busca para gerar o Excel." },
      { status: 404 }
    );
  }
}
