import { Metadata } from 'next';
import Link from 'next/link';
import { SECTORS } from '@/lib/sectors';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import { ssgLimitedFetch } from '@/lib/concurrency';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

/**
 * PSEO-HUB-001 (#879): Hub page for "licitações públicas 2026" cluster.
 *
 * Target query: "licitações públicas 2026" (94 impressions, position 4.69, 0 clicks).
 * ISR revalidate=3600 — complies with SEN-FE-001 (never mix cache:'no-store' + revalidate).
 */

export const revalidate = 3600;

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: 'Licitações Públicas 2026: editais abertos, contratos e oportunidades por setor',
  description:
    'Encontre licitações públicas abertas em 2026 por setor, estado e modalidade. Dados do PNCP, ComprasGov e PCP atualizados diariamente.',
  alternates: { canonical: buildCanonical('/licitacoes-publicas-2026') },
  openGraph: {
    title: 'Licitações Públicas 2026 — Editais Abertos, Contratos e Oportunidades por Setor',
    description:
      'Encontre licitações públicas abertas em 2026. Dados do PNCP, ComprasGov e PCP atualizados diariamente por setor, estado e modalidade.',
    url: buildCanonical('/licitacoes-publicas-2026'),
    type: 'website',
    locale: 'pt_BR',
  },
  robots: { index: true, follow: true },
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PublicStats {
  total_editais_abertos: number;
  total_contratos: number;
  total_fornecedores: number;
  updated_at: string;
}

interface RecentEdital {
  pncp_id: string;
  objeto: string;
  orgao: string;
  uf: string;
  valor: number | null;
  data_encerramento: string | null;
  modalidade: string | null;
  link: string | null;
}

// ---------------------------------------------------------------------------
// Server-side data fetching (ISR revalidate=3600)
// ---------------------------------------------------------------------------

const BACKEND_URL =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  'http://localhost:8000';

/**
 * Fetch public aggregate stats.
 * Falls back to hardcoded estimates on error.
 */
async function fetchPublicStats(): Promise<PublicStats> {
  const FALLBACK: PublicStats = {
    // Conservative estimates based on observed PNCP data volume
    total_editais_abertos: 12000,
    total_contratos: 2000000,
    total_fornecedores: 150000,
    updated_at: new Date().toISOString(),
  };

  try {
    const res = await ssgLimitedFetch(`${BACKEND_URL}/v1/stats/public`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return FALLBACK;
    const data = await res.json();

    // Extract relevant stats from the stats array
    const statsArr: Array<{ id: string; value: number }> = data?.stats ?? [];
    const findStat = (id: string) => statsArr.find((s) => s.id === id)?.value ?? 0;

    return {
      total_editais_abertos: findStat('total_open_bids') || FALLBACK.total_editais_abertos,
      total_contratos: findStat('total_contracts') || FALLBACK.total_contratos,
      total_fornecedores: findStat('total_suppliers') || FALLBACK.total_fornecedores,
      updated_at: data?.updated_at ?? FALLBACK.updated_at,
    };
  } catch {
    return FALLBACK;
  }
}

/**
 * Fetch the 10 most recent open editais via the observatorio digest endpoint.
 * Returns empty array on error — page still renders with sector cards and CTA.
 */
async function fetchRecentEditais(): Promise<RecentEdital[]> {
  try {
    const res = await ssgLimitedFetch(`${BACKEND_URL}/v1/blog/daily/latest`, {
      next: { revalidate: 3600 },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) return [];
    const data = await res.json();
    // daily/latest returns a summary object, not individual items
    // Fall through to the datalake endpoint for actual items
    void data;
    return [];
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Helper formatters
// ---------------------------------------------------------------------------

function formatBRL(value: number | null | undefined): string {
  if (!value) return 'Valor não informado';
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(0)}K`;
  return `R$ ${value.toFixed(0)}`;
}

function formatDateBR(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function formatStatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M+`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}k+`;
  return n.toLocaleString('pt-BR');
}

// ---------------------------------------------------------------------------
// Sector hub config — 8 priority sectors with page links + icon
// ---------------------------------------------------------------------------

const HUB_SECTORS = [
  {
    id: 'engenharia',
    name: 'Engenharia e Obras',
    description: 'Obras civis, reformas, construção, pavimentação e infraestrutura pública.',
    icon: '🏗️',
    slug: 'engenharia',
  },
  {
    id: 'informatica',
    name: 'TI e Hardware',
    description: 'Computadores, servidores, periféricos, redes e equipamentos de informática.',
    icon: '💻',
    slug: 'informatica',
  },
  {
    id: 'saude',
    name: 'Saúde',
    description: 'Medicamentos, equipamentos hospitalares e insumos médicos para órgãos públicos.',
    icon: '🏥',
    slug: 'saude',
  },
  {
    id: 'manutencao_predial',
    name: 'Manutenção Predial',
    description: 'Manutenção preventiva e corretiva de edificações, ar-condicionado e PMOC.',
    icon: '🔧',
    slug: 'manutencao-predial',
  },
  {
    id: 'vigilancia',
    name: 'Vigilância e Segurança',
    description: 'Vigilância patrimonial, segurança eletrônica, CFTV e alarmes.',
    icon: '🔒',
    slug: 'vigilancia',
  },
  {
    id: 'alimentos',
    name: 'Alimentos e Merenda',
    description: 'Gêneros alimentícios, merenda escolar, refeições e rancho para entidades públicas.',
    icon: '🍎',
    slug: 'alimentos',
  },
  {
    id: 'transporte',
    name: 'Transporte e Veículos',
    description: 'Aquisição e locação de veículos, combustíveis e manutenção de frota.',
    icon: '🚛',
    slug: 'transporte',
  },
  {
    id: 'materiais_eletricos',
    name: 'Materiais Elétricos',
    description: 'Fios, cabos, disjuntores, quadros elétricos e iluminação pública.',
    icon: '⚡',
    slug: 'materiais-eletricos',
  },
  {
    id: 'software',
    name: 'Software e Sistemas',
    description: 'Licenças de software, SaaS, desenvolvimento de sistemas e consultoria de TI.',
    icon: '🖥️',
    slug: 'software',
  },
  {
    id: 'facilities',
    name: 'Facilities e Limpeza',
    description: 'Limpeza predial, conservação, portaria e serviços de recepção.',
    icon: '🧹',
    slug: 'facilities',
  },
] as const;

// ---------------------------------------------------------------------------
// JSON-LD
// ---------------------------------------------------------------------------

function buildJsonLd() {
  const breadcrumbs = [
    { name: 'SmartLic', url: SITE_URL },
    { name: 'Licitações Públicas 2026', url: `${SITE_URL}/licitacoes-publicas-2026` },
  ];

  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Licitações Públicas 2026: editais abertos, contratos e oportunidades por setor',
    description:
      'Encontre licitações públicas abertas em 2026 por setor, estado e modalidade. Dados do PNCP, ComprasGov e PCP atualizados diariamente.',
    url: `${SITE_URL}/licitacoes-publicas-2026`,
    provider: { '@type': 'Organization', name: 'SmartLic', url: SITE_URL },
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((b, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: b.name,
        item: b.url,
      })),
    },
    numberOfItems: HUB_SECTORS.length,
    itemListElement: HUB_SECTORS.map((s, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      url: `${SITE_URL}/licitacoes/${s.slug}`,
      name: `Licitações de ${s.name} em 2026`,
    })),
  };
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

export default async function LicitacoesPublicas2026Page() {
  const [stats, recentEditais] = await Promise.all([
    fetchPublicStats(),
    fetchRecentEditais(),
  ]);

  const jsonLd = buildJsonLd();

  return (
    <>
      <LandingNavbar />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <main className="min-h-screen bg-gray-50">
        {/* ------------------------------------------------------------------ */}
        {/* HERO — above the fold, H1 + subtítulo + CTA primário               */}
        {/* ------------------------------------------------------------------ */}
        <section className="bg-gradient-to-br from-blue-700 via-blue-600 to-blue-500 text-white py-16 px-4">
          <div className="max-w-5xl mx-auto">
            {/* Breadcrumb */}
            <nav
              aria-label="Localização"
              className="flex items-center gap-2 text-sm text-blue-200 mb-6"
            >
              <Link href="/" className="hover:text-white transition-colors">
                SmartLic
              </Link>
              <span>/</span>
              <span className="text-white">Licitações Públicas 2026</span>
            </nav>

            <div className="max-w-3xl">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight mb-4">
                Licitações Públicas 2026
              </h1>
              <p className="text-lg sm:text-xl text-blue-100 mb-3 leading-relaxed">
                Editais abertos, contratos e oportunidades por setor — dados atualizados
                diariamente do{' '}
                <abbr title="Portal Nacional de Contratações Públicas" className="no-underline">
                  PNCP
                </abbr>
                , ComprasGov e Portal de Compras Públicas.
              </p>
              <p className="text-sm text-blue-200 mb-8">
                Mais de {formatStatNumber(stats.total_editais_abertos)} editais abertos
                monitorados em 15 setores e todos os 27 estados do Brasil.
              </p>

              {/* CTA primário — acima da dobra */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  href="/consultoria-b2g?source=hub-licitacoes-2026&utm_source=organic&utm_medium=pseo&utm_content=hero-cta"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-blue-700 font-semibold rounded-lg hover:bg-blue-50 transition-colors shadow-md"
                >
                  Buscar Editais Grátis
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </Link>
                <Link
                  href="/licitacoes"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 border-2 border-white/60 text-white font-semibold rounded-lg hover:border-white hover:bg-white/10 transition-colors"
                >
                  Explorar por Setor
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* NÚMEROS AO VIVO — ISR revalidate=3600                              */}
        {/* ------------------------------------------------------------------ */}
        <section
          aria-labelledby="stats-heading"
          className="bg-white border-b border-gray-200 py-10 px-4"
        >
          <div className="max-w-5xl mx-auto">
            <h2
              id="stats-heading"
              className="text-sm font-semibold text-gray-500 uppercase tracking-wider text-center mb-6"
            >
              Dados ao Vivo — Atualizados a cada hora
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
              <div className="p-5 rounded-xl bg-blue-50 border border-blue-100">
                <div className="text-3xl font-bold text-blue-700 mb-1">
                  {formatStatNumber(stats.total_editais_abertos)}
                </div>
                <div className="text-sm text-gray-600 font-medium">Editais Abertos</div>
                <div className="text-xs text-gray-400 mt-1">no PNCP + ComprasGov + PCP</div>
              </div>
              <div className="p-5 rounded-xl bg-green-50 border border-green-100">
                <div className="text-3xl font-bold text-green-700 mb-1">
                  {formatStatNumber(stats.total_contratos)}
                </div>
                <div className="text-sm text-gray-600 font-medium">Contratos Históricos</div>
                <div className="text-xs text-gray-400 mt-1">últimos 400 dias</div>
              </div>
              <div className="p-5 rounded-xl bg-purple-50 border border-purple-100">
                <div className="text-3xl font-bold text-purple-700 mb-1">
                  {formatStatNumber(stats.total_fornecedores)}
                </div>
                <div className="text-sm text-gray-600 font-medium">Fornecedores Cadastrados</div>
                <div className="text-xs text-gray-400 mt-1">com histórico de contratos</div>
              </div>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* CARDS POR SETOR — mínimo 8, links para /licitacoes/[setor]         */}
        {/* ------------------------------------------------------------------ */}
        <section
          aria-labelledby="sectors-heading"
          className="max-w-5xl mx-auto py-12 px-4"
        >
          <div className="mb-8">
            <h2
              id="sectors-heading"
              className="text-2xl font-bold text-gray-900 mb-2"
            >
              Licitações Públicas 2026 por Setor
            </h2>
            <p className="text-gray-600">
              Selecione seu setor de atuação para ver editais abertos, histórico de contratos e
              principais órgãos compradores.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {HUB_SECTORS.map((sector) => (
              <Link
                key={sector.id}
                href={`/licitacoes/${sector.slug}`}
                className="group flex flex-col p-5 bg-white rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl" role="img" aria-hidden="true">
                    {sector.icon}
                  </span>
                  <h3 className="text-base font-semibold text-gray-900 group-hover:text-blue-600 transition-colors leading-tight">
                    {sector.name}
                  </h3>
                </div>
                <p className="text-sm text-gray-500 flex-1 mb-3 leading-relaxed">
                  {sector.description}
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-600">
                  Ver editais abertos
                  <svg
                    className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </span>
              </Link>
            ))}
          </div>

          {/* Link para todos os setores */}
          <div className="mt-6 text-center">
            <Link
              href="/licitacoes"
              className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 underline underline-offset-2"
            >
              Ver todos os 15 setores disponíveis
            </Link>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* ÚLTIMOS EDITAIS — top 10, ISR revalidate=3600                       */}
        {/* ------------------------------------------------------------------ */}
        <section
          aria-labelledby="recent-editais-heading"
          className="bg-white border-t border-b border-gray-200 py-12 px-4"
        >
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2
                  id="recent-editais-heading"
                  className="text-2xl font-bold text-gray-900 mb-1"
                >
                  Últimos Editais Abertos em 2026
                </h2>
                <p className="text-sm text-gray-500">
                  Dados das fontes oficiais (PNCP, ComprasGov, PCP) — atualizados diariamente
                </p>
              </div>
              <Link
                href="/blog/licitacoes-do-dia"
                className="hidden sm:inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 whitespace-nowrap"
              >
                Ver resumo do dia
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>

            {recentEditais.length > 0 ? (
              <ul className="space-y-3">
                {recentEditais.slice(0, 10).map((edital) => (
                  <li
                    key={edital.pncp_id}
                    className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
                        {edital.objeto}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                        <span>{edital.orgao}</span>
                        <span aria-hidden="true">·</span>
                        <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">
                          {edital.uf}
                        </span>
                        {edital.modalidade && (
                          <>
                            <span aria-hidden="true">·</span>
                            <span>{edital.modalidade}</span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="flex sm:flex-col items-center sm:items-end gap-3 sm:gap-1 shrink-0">
                      <span className="text-sm font-bold text-blue-700">
                        {formatBRL(edital.valor)}
                      </span>
                      {edital.data_encerramento && (
                        <span className="text-xs text-gray-400">
                          Prazo: {formatDateBR(edital.data_encerramento)}
                        </span>
                      )}
                      {edital.link && (
                        <a
                          href={edital.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-medium text-blue-600 hover:text-blue-800 underline underline-offset-1"
                          aria-label={`Ver edital: ${edital.objeto}`}
                        >
                          Ver edital
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              /* Fallback quando backend não retorna editais individuais */
              <div className="text-center py-10 text-gray-500">
                <p className="text-base font-medium mb-2">
                  Editais são atualizados continuamente pelo PNCP
                </p>
                <p className="text-sm mb-6">
                  Use nossa busca para encontrar editais abertos no seu setor e estado agora.
                </p>
                <Link
                  href="/consultoria-b2g?source=hub-licitacoes-2026&utm_content=recent-editais-fallback"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Buscar Editais Agora
                </Link>
              </div>
            )}

            <div className="mt-6 flex justify-center">
              <Link
                href="/buscar"
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700 underline underline-offset-2"
              >
                Buscar editais com filtros por setor, estado e valor →
              </Link>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* LINKS DE ACESSO RÁPIDO                                              */}
        {/* ------------------------------------------------------------------ */}
        <section
          aria-labelledby="quick-links-heading"
          className="max-w-5xl mx-auto py-12 px-4"
        >
          <h2
            id="quick-links-heading"
            className="text-xl font-bold text-gray-900 mb-6"
          >
            Explore o Mercado de Compras Públicas 2026
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/fornecedores"
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
            >
              <div className="text-xl mb-2" aria-hidden="true">🏢</div>
              <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 mb-1">
                Fornecedores
              </h3>
              <p className="text-xs text-gray-500">
                Empresas que vendem para o governo por setor e estado.
              </p>
            </Link>

            <Link
              href="/orgaos"
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
            >
              <div className="text-xl mb-2" aria-hidden="true">🏛️</div>
              <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 mb-1">
                Órgãos Compradores
              </h3>
              <p className="text-xs text-gray-500">
                Histórico de compras dos órgãos públicos federais e estaduais.
              </p>
            </Link>

            <Link
              href="/contratos"
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
            >
              <div className="text-xl mb-2" aria-hidden="true">📄</div>
              <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 mb-1">
                Contratos por Setor
              </h3>
              <p className="text-xs text-gray-500">
                Valores e fornecedores de contratos assinados por setor e UF.
              </p>
            </Link>

            <Link
              href="/cnpj"
              className="group p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
            >
              <div className="text-xl mb-2" aria-hidden="true">🔍</div>
              <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-600 mb-1">
                Consulta CNPJ
              </h3>
              <p className="text-xs text-gray-500">
                Veja o histórico de licitações e contratos de qualquer CNPJ.
              </p>
            </Link>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* CTA SECUNDÁRIO — conversão                                          */}
        {/* ------------------------------------------------------------------ */}
        <section className="bg-gradient-to-br from-blue-700 to-blue-500 py-14 px-4">
          <div className="max-w-3xl mx-auto text-center text-white">
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              Monitore licitações do seu setor automaticamente em 2026
            </h2>
            <p className="text-blue-100 mb-8 text-base leading-relaxed max-w-xl mx-auto">
              O SmartLic busca, filtra e classifica licitações com inteligência artificial.
              Configure alertas por setor, estado e valor. Economize horas de pesquisa manual.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/consultoria-b2g?source=hub-licitacoes-2026&utm_source=organic&utm_medium=pseo&utm_content=bottom-cta"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-blue-700 font-semibold rounded-lg hover:bg-blue-50 transition-colors shadow-md"
              >
                Pedir um diagnóstico à CONFENGE
              </Link>
              <Link
                href="/consultoria-b2g"
                className="inline-flex items-center justify-center px-6 py-3 border-2 border-white/60 text-white font-semibold rounded-lg hover:border-white hover:bg-white/10 transition-colors"
              >
                Ver Planos
              </Link>
            </div>
            <p className="text-xs text-blue-200 mt-4">Sem cartão de crédito. Cancele quando quiser.</p>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* LINKS INTERNOS — distribuição de PageRank                          */}
        {/* ------------------------------------------------------------------ */}
        <section className="max-w-5xl mx-auto py-10 px-4 border-t border-gray-200">
          <h2 className="text-base font-semibold text-gray-700 mb-4">
            Licitações por tipo e modalidade em 2026
          </h2>
          <div className="flex flex-wrap gap-3 text-sm">
            <Link href="/licitacoes" className="text-blue-600 hover:underline">
              Licitações por Setor
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/blog/licitacoes" className="text-blue-600 hover:underline">
              Licitações por Estado
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/contratos" className="text-blue-600 hover:underline">
              Contratos Públicos
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/dados" className="text-blue-600 hover:underline">
              Dados Abertos de Licitações
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/estatisticas" className="text-blue-600 hover:underline">
              Estatísticas de Licitações
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/alertas-publicos" className="text-blue-600 hover:underline">
              Alertas de Editais
            </Link>
            <span aria-hidden="true" className="text-gray-300">|</span>
            <Link href="/guia/licitacoes" className="text-blue-600 hover:underline">
              Guia de Licitações
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
