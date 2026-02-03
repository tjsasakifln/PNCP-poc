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

  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json(
      { message: "ID obrigatório" },
      { status: 400 }
    );
  }

  // Read from filesystem instead of memory cache
  const tmpDir = tmpdir();
  const filePath = join(tmpDir, `bidiq_${id}.xlsx`);

  try {
    const buffer = await readFile(filePath);
    const appNameSlug = (process.env.NEXT_PUBLIC_APP_NAME || "Smart_PNCP").replace(/\s+/g, '_');
    const filename = `${appNameSlug}_${new Date().toISOString().split("T")[0]}.xlsx`;

    console.log(`✅ Download served: ${id} (${buffer.length} bytes)`);

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
