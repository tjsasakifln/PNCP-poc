import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../lib/serverAuth";

const BACKEND_URL = process.env.BACKEND_URL;

/**
 * SEO-PLAYBOOK P6: Share analysis proxy.
 * POST /api/share — create shareable link (auth required)
 */
export async function POST(request: NextRequest) {
  try {
    const refreshedToken = await getRefreshedToken();
    const authHeader = refreshedToken
      ? `Bearer ${refreshedToken}`
      : request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { message: "Autenticação necessária." },
        { status: 401 }
      );
    }

    const body = await request.json();

    const res = await fetch(`${BACKEND_URL}/v1/share/analise`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("[share-proxy] POST error:", error);
    return NextResponse.json(
      { message: "Erro ao criar link de compartilhamento." },
      { status: 502 }
    );
  }
}
