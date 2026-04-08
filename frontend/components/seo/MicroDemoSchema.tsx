const SITE_URL = 'https://smartlic.tech';

const VARIANT_META: Record<string, { name: string; description: string }> = {
  busca: {
    name: 'SmartLic — Como Funciona a Busca Multi-Fonte',
    description:
      'Demonstração animada de como o SmartLic busca licitações em PNCP, PCP e ComprasGov simultaneamente.',
  },
  resultado: {
    name: 'SmartLic — Resultados com Score de Viabilidade',
    description:
      'Demonstração animada dos resultados de busca com score de viabilidade por edital.',
  },
  viabilidade: {
    name: 'SmartLic — Análise de Viabilidade 4 Fatores',
    description:
      'Demonstração animada da análise de viabilidade considerando modalidade, prazo, valor e geografia.',
  },
};

export function MicroDemoSchema({ variant }: { variant: string }) {
  const meta = VARIANT_META[variant];
  if (!meta) return null;

  const schema = {
    '@context': 'https://schema.org',
    '@type': 'VideoObject',
    name: meta.name,
    description: meta.description,
    thumbnailUrl: `${SITE_URL}/api/og?title=${encodeURIComponent(meta.name)}`,
    uploadDate: '2026-04-07',
    duration: 'PT5S',
    contentUrl: `${SITE_URL}/demo#${variant}`,
    embedUrl: `${SITE_URL}/demo#${variant}`,
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}
