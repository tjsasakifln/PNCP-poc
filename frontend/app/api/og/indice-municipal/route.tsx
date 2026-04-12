import { ImageResponse } from 'next/og';
import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const cidade = searchParams.get('cidade') || 'Município';
  const uf = searchParams.get('uf') || 'UF';
  const scoreRaw = searchParams.get('score');
  const score = scoreRaw != null ? Math.min(100, Math.max(0, parseInt(scoreRaw, 10))) : null;
  const rankingNacional = searchParams.get('ranking_nacional');
  const periodo = searchParams.get('periodo') || '2026-Q1';

  // Score color thresholds (matches frontend scoreColor logic)
  const scoreColor =
    score == null ? '#94A3B8' : score >= 60 ? '#22C55E' : score >= 40 ? '#F59E0B' : '#EF4444';
  const scoreDisplay = score != null ? score.toFixed(0) : '—';

  return new ImageResponse(
    (
      <div
        style={{
          width: '1200px',
          height: '630px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #0A1E3F 0%, #0D2B5E 50%, #116DFF 100%)',
          padding: '48px',
          fontFamily: 'sans-serif',
          gap: '24px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div
            style={{ color: '#93C5FD', fontSize: '20px', fontWeight: 600, letterSpacing: '0.05em' }}
          >
            SmartLic
          </div>
          <div style={{ color: '#CBD5E1', fontSize: '16px' }}>
            Índice de Transparência Municipal
          </div>
        </div>

        {/* Score circle */}
        <div
          style={{
            width: '160px',
            height: '160px',
            borderRadius: '50%',
            border: `6px solid ${scoreColor}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(255,255,255,0.05)',
          }}
        >
          <div
            style={{ color: scoreColor, fontSize: '56px', fontWeight: 800, lineHeight: 1 }}
          >
            {scoreDisplay}
          </div>
          <div style={{ color: '#CBD5E1', fontSize: '13px', marginTop: '4px' }}>de 100</div>
        </div>

        {/* City name */}
        <div
          style={{
            color: '#FFFFFF',
            fontSize: '48px',
            fontWeight: 700,
            textAlign: 'center',
            lineHeight: 1.1,
          }}
        >
          {cidade.length > 22 ? cidade.slice(0, 22) + '…' : cidade} / {uf}
        </div>

        {/* Ranking + Period */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {rankingNacional && (
            <div
              style={{
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '24px',
                padding: '8px 20px',
                color: '#F0F9FF',
                fontSize: '18px',
                fontWeight: 600,
              }}
            >
              #{rankingNacional} nacional
            </div>
          )}
          <div
            style={{
              background: 'rgba(255,255,255,0.1)',
              borderRadius: '24px',
              padding: '8px 20px',
              color: '#CBD5E1',
              fontSize: '16px',
            }}
          >
            {periodo}
          </div>
        </div>

        {/* Footer URL */}
        <div
          style={{ color: '#64748B', fontSize: '14px', position: 'absolute', bottom: '32px' }}
        >
          smartlic.tech/indice-municipal
        </div>
      </div>
    ),
    { width: 1200, height: 630 }
  );
}
