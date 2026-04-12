/**
 * STORY-445: /api/new-bids-count proxy
 *
 * GET  → backend GET  /v1/notifications/new-bids-count
 * DELETE → backend DELETE /v1/notifications/new-bids-count
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

function getAuthHeader(req: NextRequest): string | null {
  return req.headers.get("authorization");
}

export async function GET(req: NextRequest): Promise<NextResponse> {
  const auth = getAuthHeader(req);
  if (!auth) {
    return NextResponse.json({ count: 0 }, { status: 200 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/v1/notifications/new-bids-count`, {
      headers: { Authorization: auth },
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({ count: 0 });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ count: 0 });
  }
}

export async function DELETE(req: NextRequest): Promise<NextResponse> {
  const auth = getAuthHeader(req);
  if (!auth) {
    return NextResponse.json({ ok: true });
  }

  try {
    await fetch(`${BACKEND_URL}/v1/notifications/new-bids-count`, {
      method: "DELETE",
      headers: { Authorization: auth },
    });
  } catch {
    // Best-effort — do not surface errors to client
  }
  return NextResponse.json({ ok: true });
}
