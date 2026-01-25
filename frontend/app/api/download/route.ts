import { NextRequest, NextResponse } from "next/server";
import { downloadCache } from "../buscar/route";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json(
      { message: "ID obrigatório" },
      { status: 400 }
    );
  }

  const buffer = downloadCache.get(id);

  if (!buffer) {
    return NextResponse.json(
      { message: "Download expirado ou inválido" },
      { status: 404 }
    );
  }

  const filename = `bidiq_uniformes_${new Date().toISOString().split("T")[0]}.xlsx`;

  // Convert Buffer to Uint8Array for Next.js Response
  const uint8Array = new Uint8Array(buffer);

  return new NextResponse(uint8Array, {
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": `attachment; filename="${filename}"`
    }
  });
}
