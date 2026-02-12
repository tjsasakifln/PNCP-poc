import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

export async function GET(request: NextRequest) {
  // Require authentication for downloads
  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return NextResponse.json(
      { message: "Autenticacao necessaria. Faca login para continuar." },
      { status: 401 }
    );
  }

  // STORY-202 SYS-M01: Forward X-Request-ID if present for tracing
  const requestId = request.headers.get("X-Request-ID");
  if (requestId) {
    console.log(`[download] Request ID: ${requestId}`);
  }

  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get("id");
  const url = searchParams.get("url");

  // STORY-202 CROSS-C02: Priority 1 - Signed URL from object storage (redirect)
  if (url) {
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
