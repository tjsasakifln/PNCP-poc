import { NextRequest, NextResponse } from "next/server";
import { readFile } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";

export async function GET(request: NextRequest) {
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
    const filename = `descomplicita_${new Date().toISOString().split("T")[0]}.xlsx`;

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
