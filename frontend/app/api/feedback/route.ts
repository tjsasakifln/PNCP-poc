/**
 * GTM-RESILIENCE-D05: Feedback API proxy.
 *
 * POST /api/feedback → POST BACKEND_URL/v1/feedback
 * DELETE /api/feedback?id=xxx → DELETE BACKEND_URL/v1/feedback/{id}
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const authHeader = request.headers.get("authorization") || "";

    // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
    const correlationId = request.headers.get("X-Correlation-ID");
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: authHeader,
    };
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    const res = await fetch(`${BACKEND_URL}/v1/feedback`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("Feedback proxy error:", error);
    return NextResponse.json(
      { error: "Failed to submit feedback" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const feedbackId = searchParams.get("id");

    if (!feedbackId) {
      return NextResponse.json({ error: "Missing id parameter" }, { status: 400 });
    }

    const authHeader = request.headers.get("authorization") || "";

    // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
    const correlationId = request.headers.get("X-Correlation-ID");
    const headers: Record<string, string> = {
      Authorization: authHeader,
    };
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    const res = await fetch(`${BACKEND_URL}/v1/feedback/${feedbackId}`, {
      method: "DELETE",
      headers,
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error("Feedback delete proxy error:", error);
    return NextResponse.json(
      { error: "Failed to delete feedback" },
      { status: 500 }
    );
  }
}
