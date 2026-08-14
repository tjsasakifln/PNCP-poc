import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      email,
      source,
      setor,
      uf,
      // CONV-003-4: new fields for PartialReportPreview
      sector_id,       // maps to sector on backend
      source_page,     // maps to origin_url on backend
      report_type,     // maps to source on backend (e.g. "partial_preview")
      // REPO-014: extended fields for DiagnosticForm
      nome,
      empresa,
      cnpj,
      modalidade_interesse,
      mensagem,
      telefone,
      // UTM params forwarded from the client
      utm_source,
      utm_medium,
      utm_campaign,
      utm_content,
      utm_term,
      cta_id,
      route_family,
      landing_url,
    } = body as Record<string, string | undefined>;

    const phoneDigits = typeof telefone === 'string' ? telefone.replace(/\D/g, '') : '';
    const hasPhone = phoneDigits.length >= 10 && phoneDigits.length <= 13;

    if ((!email || !email.includes('@')) && !hasPhone) {
      return NextResponse.json(
        { error: 'Email ou telefone inválido' },
        { status: 400 },
      );
    }

    // Resolve fields: normalize new CONV-003-4 naming to backend field names
    const resolvedSource = report_type || source || 'partial_preview';
    const resolvedSector = sector_id || setor || null;
    const resolvedOriginUrl = source_page || null;

    // Store in Supabase via backend proxy
    const backendUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL;
    const res = await fetch(`${backendUrl}/v1/lead-capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        source: resolvedSource,
        sector: resolvedSector,
        origin_url: resolvedOriginUrl,
        uf: uf || null,
        nome: nome || null,
        empresa: empresa || null,
        cnpj: cnpj || null,
        modalidade_interesse: modalidade_interesse || null,
        mensagem: mensagem || null,
        telefone: telefone || null,
        utm_source: utm_source || null,
        utm_medium: utm_medium || null,
        utm_campaign: utm_campaign || null,
        utm_content: utm_content || null,
        utm_term: utm_term || null,
        cta_id: cta_id || null,
        route_family: route_family || null,
        landing_url: landing_url || resolvedOriginUrl,
        captured_at: new Date().toISOString(),
      }),
    });

    if (!res.ok) {
      const requestId = res.headers.get('x-request-id');
      console.warn('Lead capture backend returned non-OK response', {
        status: res.status,
        requestId,
      });
      return NextResponse.json(
        { success: false, error: `Erro ao processar (${res.status})` },
        { status: 502 },
      );
    }

    const payload = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    return NextResponse.json({
      success: true,
      receipt_id: payload.receipt_id ?? null,
      handoff_state: payload.handoff_state ?? null,
    });
  } catch (error) {
    console.error('Lead capture error:', error);
    return NextResponse.json(
      { success: false, error: 'Serviço indisponível. Tente novamente.' },
      { status: 502 },
    );
  }
}
