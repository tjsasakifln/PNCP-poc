/**
 * STORY-447: /api/export/pdf proxy
 *
 * Forwards POST requests to backend POST /v1/export/pdf and streams
 * the resulting PDF bytes back to the browser as application/pdf.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const auth = req.headers.get("authorization");
  if (!auth) {
    return NextResponse.json(
      { detail: "Não autorizado" },
      { status: 401 }
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Corpo da requisição inválido" }, { status: 400 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/v1/export/pdf`, {
      method: "POST",
      headers: {
        Authorization: auth,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errText = await res.text().catch(() => "Erro desconhecido");
      return NextResponse.json(
        { detail: errText },
        { status: res.status }
      );
    }

    const pdfBuffer = await res.arrayBuffer();
    const contentDisposition =
      res.headers.get("content-disposition") ??
      'attachment; filename="SmartLic_edital.pdf"';

    return new NextResponse(pdfBuffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": contentDisposition,
        "Content-Length": String(pdfBuffer.byteLength),
      },
    });
  } catch (err) {
    console.error("[export/pdf] Backend error:", err);
    return NextResponse.json(
      { detail: "Erro ao gerar PDF. Tente novamente." },
      { status: 502 }
    );
  }
}
