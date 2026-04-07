import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const ids = searchParams.get('ids') || '';

  const params = new URLSearchParams();
  if (ids) params.set('ids', ids);

  try {
    const res = await fetch(`${BACKEND_URL}/v1/comparador/bids?${params}`, {
      next: { revalidate: 3600 },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ bids: [], total: 0 }, { status: 200 });
  }
}
