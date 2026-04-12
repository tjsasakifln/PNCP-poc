import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 6 Parte 13: páginas de benchmark de preços por código CATMAT
// ISR 24h — dados do PNCP atualizados diariamente
export const revalidate = 86400;

const _MAX_STATIC_CATMATS = 200;

type Props = { params: Promise<{ catmat: string }> };

interface ContratoReferencia {
  objeto: string;
  orgao: string;
  valor: number;
  data_assinatura: string;
  uf: string;
}

interface FaqItem {
  question: string;
  answer: string;
}

interface ItemProfile {
  catmat: string;
  nome_item: string;
  categoria: string;
  total_contratos: number;
  valor_p10: number | null;
  valor_p50: number | null;
  valor_p90: number | null;
  valor_medio: number | null;
  unidade_referencia: string;
  contratos_referencia: ContratoReferencia[];
  faq_items: FaqItem[];
  periodo_referencia: string;
  last_updated: string;
  aviso_legal: string;
}

async function fetchProfile(catmat: string): Promise<ItemProfile | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/itens/${catmat}/profile`, {
      next: { revalidate: 86400 },
    });
    if (res.status === 404 || res.status === 400) return null;
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function generateStaticParams() {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/sitemap/itens`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    const data = await res.json();
    const catmats: string[] = (data.catmats || []).slice(0, _MAX_STATIC_CATMATS);
    return catmats.map((catmat) => ({ catmat }));
  } catch {
    return [];
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { catmat } = await params;
  const profile = await fetchProfile(catmat);

  if (!profile) {
    return {
      title: `CATMAT ${catmat} — SmartLic`,
      robots: { index: false, follow: false },
    };
  }

  const p50Fmt = profile.valor_p50 != null ? formatBRL(profile.valor_p50) : '';

  return {
    title: `Preço de Mercado: ${profile.nome_item} (CATMAT ${catmat}) | Benchmark Governo`,
    description:
      `Quanto o governo paga por ${profile.nome_item}? ` +
      (p50Fmt ? `Preço mediano (P50): ${p50Fmt}. ` : '') +
      `Baseado em ${profile.total_contratos} contratos reais do PNCP.`,
    alternates: { canonical: buildCanonical(`/itens/${catmat}`) },
    openGraph: {
      title: `${profile.nome_item} — Preço Governo (CATMAT ${catmat})`,
      description: p50Fmt ? `Mediana: ${p50Fmt} · ${profile.total_contratos} contratos PNCP` : `${profile.total_contratos} contratos PNCP`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: true, follow: true },
  };
}

export default async function ItemCatmatPage({ params }: Props) {
  const { catmat } = await params;

  if (!/^\d{1,9}$/.test(catmat)) notFound();

  const profile = await fetchProfile(catmat);
  if (!profile) notFound();

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Benchmark de Preços', url: '/itens' },
    { name: `CATMAT ${catmat}`, url: `/itens/${catmat}` },
  ];

  // Gráfico de barras proporcional para P10/P50/P90
  const maxValor = profile.valor_p90 ?? profile.valor_medio ?? 1;

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: profile.nome_item,
      description: `${profile.nome_item} — código CATMAT ${catmat}`,
      category: profile.categoria,
      offers: {
        '@type': 'AggregateOffer',
        priceCurrency: 'BRL',
        lowPrice: profile.valor_p10,
        highPrice: profile.valor_p90,
        price: profile.valor_p50,
        offerCount: profile.total_contratos,
      },
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
          <div className="mb-1">
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
              {profile.categoria}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">
            {profile.nome_item}
          </h1>
          <p className="text-sm text-gray-500 mb-1">
            CATMAT {catmat}
          </p>
          <p className="text-xs text-gray-400 mb-6">
            {profile.last_updated ? getFreshnessLabel(profile.last_updated) : 'Dados do PNCP'}
            {' · '}{profile.periodo_referencia}
          </p>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Preço Mediano (P50)</p>
              <p className="text-2xl font-bold text-blue-700">
                {profile.valor_p50 != null ? formatBRL(profile.valor_p50) : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">50% dos contratos abaixo</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Preço Mínimo (P10)</p>
              <p className="text-2xl font-bold text-green-700">
                {profile.valor_p10 != null ? formatBRL(profile.valor_p10) : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">10% dos contratos abaixo</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Preço Máximo (P90)</p>
              <p className="text-2xl font-bold text-red-700">
                {profile.valor_p90 != null ? formatBRL(profile.valor_p90) : '—'}
              </p>
              <p className="text-xs text-gray-400 mt-1">10% dos contratos acima</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Contratos Analisados</p>
              <p className="text-2xl font-bold text-gray-900">
                {profile.total_contratos.toLocaleString('pt-BR')}
              </p>
              <p className="text-xs text-gray-400 mt-1">{profile.unidade_referencia}</p>
            </div>
          </div>

          {/* Visualização de distribuição de preços */}
          {profile.valor_p10 != null && profile.valor_p50 != null && profile.valor_p90 != null && (
            <section className="mb-8 bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Distribuição de Preços</h2>
              <div className="space-y-3">
                {[
                  { label: 'P10 (mínimo)', value: profile.valor_p10, color: 'bg-green-500' },
                  { label: 'Média',        value: profile.valor_medio ?? profile.valor_p50, color: 'bg-blue-400' },
                  { label: 'P50 (mediana)',value: profile.valor_p50,  color: 'bg-blue-600' },
                  { label: 'P90 (máximo)', value: profile.valor_p90,  color: 'bg-red-500' },
                ].map((bar) => (
                  <div key={bar.label} className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-28 shrink-0">{bar.label}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                      <div
                        className={`h-4 rounded-full ${bar.color}`}
                        style={{ width: `${Math.max(4, ((bar.value ?? 0) / maxValor) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-gray-700 w-28 text-right shrink-0">
                      {bar.value != null ? formatBRL(bar.value) : '—'}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-3">
                Valores referem-se ao preço total do contrato, não ao preço unitário.
              </p>
            </section>
          )}

          {/* Contratos de referência */}
          {profile.contratos_referencia.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                Contratos de Referência
              </h2>
              <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600">
                    <tr>
                      <th className="text-left px-4 py-3">Objeto</th>
                      <th className="text-left px-4 py-3">Órgão Comprador</th>
                      <th className="text-right px-4 py-3">Valor</th>
                      <th className="text-right px-4 py-3">Data</th>
                      <th className="text-center px-4 py-3">UF</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {profile.contratos_referencia.map((c, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 max-w-xs">
                          <span className="line-clamp-2">{c.objeto}</span>
                        </td>
                        <td className="px-4 py-2 text-gray-600">{c.orgao}</td>
                        <td className="text-right px-4 py-2 text-green-700 whitespace-nowrap">
                          {formatBRL(c.valor)}
                        </td>
                        <td className="text-right px-4 py-2 text-gray-500 whitespace-nowrap">
                          {c.data_assinatura || '—'}
                        </td>
                        <td className="text-center px-4 py-2 text-gray-500">{c.uf || '—'}</td>
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
              <Link href="/itens" className="text-blue-600 hover:underline">
                Benchmark de Preços — Todos os Itens
              </Link>
              <Link href="/fornecedores" className="text-blue-600 hover:underline">
                Diretório de Fornecedores
              </Link>
              <Link href="/licitacoes" className="text-blue-600 hover:underline">
                Licitações por Setor
              </Link>
            </div>
          </section>

          {/* CTA */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore licitações de {profile.nome_item}
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia editais abertos no PNCP e identifica automaticamente
              oportunidades para os produtos e serviços do seu portfólio.
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
