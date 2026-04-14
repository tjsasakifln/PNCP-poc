import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 4 Parte 13: páginas de municípios com licitações abertas
// ISR 24h — dados do PNCP atualizados diariamente
export const revalidate = 86400;

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
}

async function fetchProfile(slug: string): Promise<MunicipioProfile | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/municipios/${slug}/profile`, {
      next: { revalidate: 86400 },
      signal: AbortSignal.timeout(10000),
    });
    if (res.status === 404) return null;
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function generateStaticParams() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/sitemap/municipios`, {
      cache: 'no-store',
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
  const profile = await fetchProfile(slug);

  if (!profile) {
    return {
      title: `Município ${slug} — SmartLic`,
      robots: { index: false, follow: false },
    };
  }

  const popFmt = profile.populacao
    ? profile.populacao.toLocaleString('pt-BR') + ' hab.'
    : '';

  return {
    title: `Licitações em ${profile.nome}-${profile.uf} — ${profile.total_licitacoes_abertas} editais abertos`,
    description:
      `Consulte os ${profile.total_licitacoes_abertas} editais abertos em ${profile.nome}-${profile.uf}. ` +
      (popFmt ? `${popFmt}. ` : '') +
      'Dados diários do PNCP com histórico de compras públicas e indicadores do IBGE.',
    alternates: { canonical: buildCanonical(`/municipios/${slug}`) },
    openGraph: {
      title: `Licitações em ${profile.nome}-${profile.uf}`,
      description: `${profile.total_licitacoes_abertas} editais abertos — PNCP`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: true, follow: true },
  };
}

export default async function MunicipioSlugPage({ params }: Props) {
  const { slug } = await params;

  // Validação básica de formato: apenas letras minúsculas, números e hífens
  if (!/^[a-z0-9-]+$/.test(slug)) notFound();

  const profile = await fetchProfile(slug);
  if (!profile) notFound();

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Municípios', url: '/municipios' },
    { name: `${profile.nome}-${profile.uf}`, url: `/municipios/${slug}` },
  ];

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'City',
      name: profile.nome,
      containedInPlace: {
        '@type': 'State',
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
      description: `${profile.total_licitacoes_abertas} editais abertos registrados no PNCP para órgãos sediados em ${profile.nome}-${profile.uf}.`,
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
    {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: profile.faq_items.map((f) => ({
        '@type': 'Question',
        name: f.question,
        acceptedAnswer: { '@type': 'Answer', text: f.answer },
      })),
    },
  ];

  return (
    <>
      <LandingNavbar />
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
            {profile.last_updated ? getFreshnessLabel(profile.last_updated) : 'Dados do PNCP'}
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

          {/* Links relacionados */}
          <section className="border-t border-gray-200 pt-8 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Páginas Relacionadas</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              <Link href="/municipios" className="text-blue-600 hover:underline">
                Todos os Municípios
              </Link>
              <Link
                href={`/fornecedores`}
                className="text-blue-600 hover:underline"
              >
                Fornecedores em {profile.uf}
              </Link>
              <Link href="/licitacoes" className="text-blue-600 hover:underline">
                Licitações por Setor
              </Link>
            </div>
          </section>

          {/* CTA */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore editais em {profile.nome}-{profile.uf}
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia licitações abertas no PNCP e avisa quando surgem
              oportunidades relevantes para sua empresa no município e região.
            </p>
            <Link
              href="/signup"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teste grátis por 14 dias
            </Link>
          </section>

          <p className="text-xs text-gray-400 mt-8">{profile.aviso_legal}</p>
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
