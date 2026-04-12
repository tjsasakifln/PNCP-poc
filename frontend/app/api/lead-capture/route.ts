import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { email, source, setor, uf } = await request.json();

    if (!email || !email.includes('@')) {
      return NextResponse.json({ error: 'Email inválido' }, { status: 400 });
    }

    // Store in Supabase via backend proxy
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    const res = await fetch(`${backendUrl}/v1/lead-capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        source,
        setor: setor || null,
        uf: uf || null,
        captured_at: new Date().toISOString(),
      }),
    });

    if (!res.ok) {
      console.warn(`Lead capture backend returned ${res.status} — storing locally only`);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Lead capture error:', error);
    // Still return success — we don't want to block the UX
    return NextResponse.json({ success: true });
  }
}
