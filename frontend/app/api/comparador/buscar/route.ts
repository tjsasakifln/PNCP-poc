import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const q = searchParams.get('q') || '';
  const uf = searchParams.get('uf') || '';

  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (uf) params.set('uf', uf);

  try {
    const res = await fetch(`${BACKEND_URL}/v1/comparador/buscar?${params}`, {
      next: { revalidate: 3600 },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ bids: [], total: 0, query: q, uf: uf || null }, { status: 200 });
  }
}
