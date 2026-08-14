import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import { ssgLimitedFetch } from '@/lib/concurrency';
import EmptyStateSEO from '@/components/seo/EmptyStateSEO';
import { getUfPrep } from '@/lib/programmatic';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import { AdvisoryDisclaimer } from '@/components/legal/AdvisoryDisclaimer';
import { LeadCapture } from '@/components/LeadCapture';
import AlertEntityCta from '@/components/seo/AlertEntityCta';
import PreviewCTA from '@/app/components/programmatic/PreviewCTA';
import { resolveJourney } from '@/lib/seo/relatedResolver';
import { JourneyLinks } from '@/app/components/navigation/JourneyLinks';
import { MunicipioUrgency } from '@/components/pseo/MunicipioUrgency';

// Sprint 4 Parte 13: páginas de municípios com licitações abertas
// ISR 24h — dados do PNCP atualizados diariamente
export const revalidate = 3600;

const _MAX_STATIC_MUNICIPIOS = 200;

type Props = { params: Promise<{ slug: string }> };

interface LicitacaoRecente {
  objeto: string;
  orgao: string;
  valor: number | null;
  data_publicacao: string;
  modalidade: string;
}

interface FaqItem {
  question: string;
  answer: string;
}

interface AtividadeRecente {
  contagem_30d: number;
  contagem_90d: number;
  valor_total_30d: number;
  tendencia_12m: string;
  tendencia_percentual: number;
  ultimo_evento_data: string | null;
  sazonalidade_mes_pico: number | null;
}

interface MunicipioProfile {
  slug: string;
  nome: string;
  uf: string;
  ibge_code: string;
  populacao: number;
  pib_per_capita: number | null;
  total_licitacoes_abertas: number;
  valor_total_licitacoes: number;
  licitacoes_recentes: LicitacaoRecente[];
  faq_items: FaqItem[];
  last_updated: string;
  aviso_legal: string;
  atividade_recente: AtividadeRecente;
}

async function fetchProfile(slug: string): Promise<MunicipioProfile | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  // SEO-FE-ISR-001 (#1038): no try/catch — let network/timeout errors propagate so
  // ISR keeps the last-good cached page rather than caching a null-driven EmptyState.
  const res = await ssgLimitedFetch(`${backendUrl}/v1/municipios/${slug}/profile`, {
    next: { revalidate: 3600 }, // 1h ISR
    signal: AbortSignal.timeout(15_000),
  });
  if (res.status >= 500) {
    // Transient backend error — throw so ISR preserves last-good cache.
    throw new Error(`municipios_profile_backend_5xx:${res.status}`);
  }
  // 4xx (incl. 404) → genuine "no data" — render EmptyStateSEO.
  if (!res.ok) return null;
  return await res.json();
}

export async function generateStaticParams() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await ssgLimitedFetch(`${backendUrl}/v1/sitemap/municipios`, {
      next: { revalidate: 3600 }, // SEN-FE-001: align with page revalidate=3600; never mix cache:'no-store' + revalidate
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    const slugs: string[] = (data.slugs || []).slice(0, _MAX_STATIC_MUNICIPIOS);
    return slugs.map((slug) => ({ slug }));
  } catch {
    return [];
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  // SEO-FE-ISR-001 (#1038): swallow transient throws in metadata phase.
  let profile: MunicipioProfile | null = null;
  try {
    profile = await fetchProfile(slug);
  } catch {
    profile = null;
  }

  if (!profile) {
    return {
      title: `Município ${slug} — SmartLic`,
      robots: { index: false, follow: false },
      alternates: { canonical: buildCanonical(`/municipios/${slug}`) },
    };
  }

  const popFmt = profile.populacao
    ? profile.populacao.toLocaleString('pt-BR') + ' hab.'
    : '';

  const prep = getUfPrep(profile.uf.toUpperCase());

  return {
    title: `Licitações abertas ${prep} ${profile.nome}-${profile.uf} | SmartLic`,
    description:
      `Consulte os ${profile.total_licitacoes_abertas} editais abertos em ${profile.nome}-${profile.uf}. ` +
      (popFmt ? `${popFmt}. ` : '') +
      'Dados diários das fontes oficiais com histórico de compras públicas e indicadores do IBGE.',
    alternates: { canonical: buildCanonical(`/municipios/${slug}`) },
    openGraph: {
      title: `Licitações em ${profile.nome}-${profile.uf}`,
      description: `${profile.total_licitacoes_abertas} editais abertos — fontes oficiais`,
      type: 'website',
      locale: 'pt_BR',
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(`Licitações em ${profile.nome}-${profile.uf}`)}&subtitle=${encodeURIComponent(`${profile.total_licitacoes_abertas} editais abertos — fontes oficiais`)}`,
          width: 1200,
          height: 630,
          alt: `Licitações em ${profile.nome}-${profile.uf} | SmartLic`,
        },
      ],
    },
    robots: { index: true, follow: true },
  };
}

export default async function MunicipioSlugPage({ params }: Props) {
  const { slug } = await params;

  // Validação básica de formato: apenas letras minúsculas, números e hífens
  if (!/^[a-z0-9-]+$/.test(slug)) notFound(); // adr-seo-001-allow: slug fails basic format check — not a valid municipio identifier

  let profile: MunicipioProfile | null;
  try {
    profile = await fetchProfile(slug);
  } catch {
    // Transient fetch failure (timeout/5xx) during SSG build or ISR revalidation —
    // render EmptyStateSEO so the build succeeds and ISR retries on next request.
    profile = null;
  }
  // ADR-SEO-001: data absence → EmptyStateSEO (not notFound) to prevent ISR-cached 404s
  if (!profile) {
    return (
      <EmptyStateSEO
        title="Município sem licitações registradas ainda"
        description="Este município não possui licitações públicas registradas nas fontes oficiais no momento. Os dados são indexados diariamente — volte em breve."
        ctaHref="/municipios"
        ctaLabel="Ver outros municípios"
      />
    );
  }

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Municípios', url: '/municipios' },
    { name: `${profile.nome}-${profile.uf}`, url: `/municipios/${slug}` },
  ];

  // SEO-Sprint2 P6.6: filter FAQ answers shorter than 300 chars
  const eligibleFaqsMunicipios = (profile.faq_items ?? []).filter(
    (f: { question: string; answer: string }) => f.answer.replace(/<[^>]*>/g, '').length >= 300
  );

  // CONV-002b: preview items for PreviewCTA — 3 licitações reais + 3 blurred
  const previewItems = profile.licitacoes_recentes.slice(0, 6).map((l) => ({
    orgao: l.orgao,
    objeto: l.objeto,
    valor_estimado: l.valor,
    data_limite: null as string | null,
    data_publicacao: l.data_publicacao,
    link_interno: `/municipios/${slug}`,
  }));

  // CONV-017 (#1332): Build intent-progressive journey for this municipio.
  const journey = resolveJourney({
    type: 'municipio',
    value: slug,
    currentUrl: `/municipios/${slug}`,
    name: profile.nome,
    uf: profile.uf,
  });

  const jsonLd = [
    {
      // SEO-Sprint2 P6.4: AdministrativeArea (was City) with containedInPlace hierarchy
      '@context': 'https://schema.org',
      '@type': 'AdministrativeArea',
      name: `${profile.nome} — ${profile.uf}`,
      containedInPlace: {
        '@type': 'AdministrativeArea',
        name: profile.uf,
        containedInPlace: { '@type': 'Country', name: 'Brasil' },
      },
      identifier: {
        '@type': 'PropertyValue',
        name: 'Código IBGE',
        value: profile.ibge_code,
      },
      url: `https://smartlic.tech/municipios/${slug}`,
    },
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: `Licitações abertas em ${profile.nome}-${profile.uf}`,
      description: `${profile.total_licitacoes_abertas} editais abertos registrados nas fontes oficiais para órgãos sediados em ${profile.nome}-${profile.uf}.`,
      creator: { '@type': 'Organization', name: 'SmartLic' },
      license: 'https://creativecommons.org/licenses/by/4.0/',
      url: `https://smartlic.tech/municipios/${slug}`,
    },
    {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((b, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: b.name,
        item: `https://smartlic.tech${b.url}`,
      })),
    },
    ...(eligibleFaqsMunicipios.length > 0
      ? [
          {
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            mainEntity: eligibleFaqsMunicipios.map((f: { question: string; answer: string }) => ({
              '@type': 'Question',
              name: f.question,
              acceptedAnswer: { '@type': 'Answer', text: f.answer },
            })),
          },
        ]
      : []),
  ];

  return (
    <>
      <LandingNavbar />
      {/* CONV-002b: Sticky bottom mobile CTA — contextual */}
      <div
        className="fixed bottom-0 left-0 right-0 z-40 sm:hidden bg-brand-navy text-white px-4 py-3 shadow-lg"
        data-testid="pseo-sticky-cta"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium">
            {profile.total_licitacoes_abertas} editais · {profile.nome}-{profile.uf}
          </span>
          <Link
            href={`/consultoria-b2g?ref=municipios-${slug}-sticky`}
            className="px-4 py-2 bg-brand-blue rounded-lg text-sm font-semibold whitespace-nowrap"
          >
            Receber alertas →
          </Link>
        </div>
      </div>
      <main className="min-h-screen bg-gray-50 pt-20 pb-16">
        {jsonLd.map((ld, i) => (
          <script
            key={i}
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }}
          />
        ))}

        {/* Breadcrumb */}
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 text-sm text-gray-500">
          {breadcrumbs.map((b, i) => (
            <span key={b.url + i}>
              {i > 0 && <span className="mx-1">/</span>}
              {i < breadcrumbs.length - 1 ? (
                <Link href={b.url} className="hover:text-blue-600">{b.name}</Link>
              ) : (
                <span className="text-gray-900 font-medium">{b.name}</span>
              )}
            </span>
          ))}
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-1">
            Licitações em {profile.nome}-{profile.uf}
          </h1>
          <p className="text-sm text-gray-400 mb-6">
            {profile.last_updated ? getFreshnessLabel(profile.last_updated) : 'Dados das fontes oficiais'}
            {' · Fonte: Portal Nacional de Contratações Públicas e IBGE'}
          </p>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Editais Abertos</p>
              <p className="text-2xl font-bold text-blue-700">
                {profile.total_licitacoes_abertas.toLocaleString('pt-BR')}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Valor Total Estimado</p>
              <p className="text-2xl font-bold text-green-700">
                {formatBRL(profile.valor_total_licitacoes)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">População</p>
              <p className="text-2xl font-bold text-gray-900">
                {profile.populacao ? profile.populacao.toLocaleString('pt-BR') : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">Estimativa IBGE</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">PIB per Capita</p>
              <p className="text-2xl font-bold text-gray-900">
                {profile.pib_per_capita
                  ? `R$ ${profile.pib_per_capita.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}`
                  : '—'}
              </p>
              {profile.pib_per_capita && (
                <p className="text-xs text-gray-400 mt-1">Fonte: IBGE</p>
              )}
            </div>
          </div>

          {/* CONV-016: urgency signal — recent bid activity */}
          <MunicipioUrgency
            atividade_recente={profile.atividade_recente}
            nome={profile.nome}
            uf={profile.uf}
          />

          {/* Licitações Recentes */}
          {profile.licitacoes_recentes.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                Editais Recentes
              </h2>
              <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600">
                    <tr>
                      <th className="text-left px-4 py-3">Objeto</th>
                      <th className="text-left px-4 py-3">Órgão</th>
                      <th className="text-left px-4 py-3">Modalidade</th>
                      <th className="text-right px-4 py-3">Valor Estimado</th>
                      <th className="text-right px-4 py-3">Publicação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {profile.licitacoes_recentes.map((l, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 max-w-xs">
                          <span className="line-clamp-2">{l.objeto}</span>
                        </td>
                        <td className="px-4 py-2 text-gray-600 max-w-xs">
                          <span className="line-clamp-1">{l.orgao}</span>
                        </td>
                        <td className="px-4 py-2 text-gray-500 whitespace-nowrap">
                          {l.modalidade}
                        </td>
                        <td className="text-right px-4 py-2 text-green-700 whitespace-nowrap">
                          {l.valor != null ? formatBRL(l.valor) : '—'}
                        </td>
                        <td className="text-right px-4 py-2 text-gray-500 whitespace-nowrap">
                          {l.data_publicacao || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* CONV-002b: PreviewCTA — 3 editais reais + 3 blurred (degustação) */}
          {profile.licitacoes_recentes.length >= 3 && (
            <div className="mb-8">
              <PreviewCTA
                setor="municipio-editais"
                setorLabel={`${profile.nome}-${profile.uf}`}
                ufLabel={profile.uf}
                totalOpen={profile.total_licitacoes_abertas}
                items={previewItems}
              />
            </div>
          )}

          {/* FAQ */}
          {profile.faq_items.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Perguntas Frequentes</h2>
              <div className="space-y-4">
                {profile.faq_items.map((f, i) => (
                  <details key={i} className="bg-white rounded-lg shadow-sm border p-4">
                    <summary className="font-medium text-gray-900 cursor-pointer">{f.question}</summary>
                    <p className="mt-2 text-sm text-gray-600">{f.answer}</p>
                  </details>
                ))}
              </div>
            </section>
          )}

          {/* CONV-017 (#1332): JourneyLinks replaces flat "Páginas Relacionadas" */}
          <JourneyLinks journey={journey} sourceTemplate="municipio" />

          {/* CONV-002b: Contextual CTA — trial + "Só quero ver os dados" */}
          <section className="mt-4 rounded-2xl border border-brand-blue/30 bg-brand-blue/5 dark:bg-brand-blue/10 p-6 sm:p-8">
            <p className="text-lg text-gray-900 dark:text-white mb-4">
              Quer receber alertas de editais em {profile.nome}-{profile.uf}?
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href={`/consultoria-b2g?ref=municipios-${slug}&source=municipio-page`}
                className="inline-block px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-center"
              >
                Receber alertas grátis 14 dias →
              </Link>
              <Link
                href="/observatorio"
                className="inline-block px-6 py-3 bg-white dark:bg-gray-900 text-brand-navy dark:text-white font-medium rounded-lg border border-gray-300 dark:border-gray-700 hover:border-brand-blue transition-colors text-center"
              >
                Só quero ver os dados
              </Link>
            </div>
          </section>

          {/* Lead magnet — email capture before hard trial gate */}
          <div className="mt-6">
            <LeadCapture
              source="municipio-page"
              uf={profile.uf}
              heading={`Receba alertas semanais de editais em ${profile.nome}-${profile.uf}`}
              description="Novos editais toda semana no seu email. Sem spam — cancele a qualquer momento."
            />
          </div>

          {/* CONV-014: Alert CTA — receber editais do município */}
          <div className="mt-6">
            <AlertEntityCta
              entityType="municipio"
              entityId={slug}
              entityLabel={`${profile.nome}-${profile.uf}`}
            />
          </div>

          {/* REPO-015: Consultoria-b2g CTA with municipio pre-fill */}
          <section className="mt-6 rounded-xl border border-blue-200 bg-blue-50 dark:bg-blue-950/30 dark:border-blue-800 p-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">
              Quer inteligência B2G para este município?
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Diagnóstico gratuito. Sem compromisso.
            </p>
            <Link
              href={`/consultoria-b2g?modalidade=radar&municipio=${slug}`}
              className="inline-block rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
              data-cta-source="pseo-municipios"
            >
              Solicitar diagnóstico B2G
            </Link>
          </section>

          <p className="text-xs text-gray-400 mt-8">{profile.aviso_legal}</p>
          {/* REPO-020 (#772): Advisory disclaimer for algorithmic data aggregations */}
          <AdvisoryDisclaimer variant="full" />
        </div>
      </main>
      <Footer />
    </>
  );
}

function formatBRL(value: number): string {
  if (value >= 1_000_000_000) {
    return `R$ ${(value / 1_000_000_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} bi`;
  }
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} mi`;
  }
  if (value >= 1_000) {
    return `R$ ${(value / 1_000).toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} mil`;
  }
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
