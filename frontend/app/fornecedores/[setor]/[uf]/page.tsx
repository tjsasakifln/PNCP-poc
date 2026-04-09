import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { generateSectorUfParams, getSectorFromSlug, ALL_UFS, UF_NAMES } from '@/lib/programmatic';
import { formatBRL } from '@/lib/sectors';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateSectorUfParams();
}

type Props = { params: Promise<{ setor: string; uf: string }> };

interface SupplierEntry {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

interface FornecedoresStats {
  sector_id: string;
  sector_name: string;
  uf: string;
  total_suppliers: number;
  supplier_ranking: SupplierEntry[];
  top_orgaos_compradores: { nome: string; cnpj: string; total_contratos: number; valor_total: number }[];
  last_updated: string;
  aviso_legal: string;
}

async function fetchFornecedoresStats(setor: string, uf: string): Promise<FornecedoresStats | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/fornecedores/${setor}/${uf}/stats`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) return {};
  const ufUpper = uf.toUpperCase();
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const year = new Date().getFullYear();
  const data = await fetchFornecedoresStats(setor, ufUpper.toLowerCase());
  const hasData = !!(data && data.total_suppliers > 0);

  return {
    title: `Fornecedores de ${sector.name} em ${ufName} ${year} — SmartLic`,
    description: `Quais empresas vendem ${sector.name} para o governo de ${ufName}? Ranking de fornecedores com valor de contratos. Dados PNCP.`,
    alternates: { canonical: buildCanonical(`/fornecedores/${setor}/${uf}`) },
    openGraph: {
      title: `Fornecedores: ${sector.name} em ${ufName}`,
      description: `Empresas que vendem ${sector.name} para o governo de ${ufName}`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: hasData, follow: true },
  };
}

export default async function FornecedoresSetorUfPage({ params }: Props) {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const ufUpper = uf.toUpperCase();
  if (!ALL_UFS.includes(ufUpper)) notFound();

  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const data = await fetchFornecedoresStats(setor, ufUpper.toLowerCase());
  const year = new Date().getFullYear();

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Fornecedores do Governo', url: '/fornecedores' },
    { name: sector.name, url: `/fornecedores/${setor}/${uf}` },
    { name: ufName, url: `/fornecedores/${setor}/${uf}` },
  ];

  const faqItems = [
    {
      question: `Quais empresas fornecem ${sector.name} para o governo de ${ufName}?`,
      answer: data && data.supplier_ranking.length > 0
        ? `Os maiores fornecedores sao: ${data.supplier_ranking.slice(0, 3).map((s) => s.nome).join(', ')}. Veja o ranking completo nesta pagina.`
        : `Consulte os dados atualizados nesta pagina para ver os fornecedores de ${sector.name} em ${ufName}.`,
    },
    {
      question: `Como se tornar fornecedor de ${sector.name} para o governo?`,
      answer: `Para vender ${sector.name} para o governo, cadastre-se no PNCP e participe de licitacoes. O SmartLic ajuda a encontrar oportunidades relevantes.`,
    },
    {
      question: `Quantos fornecedores de ${sector.name} existem em ${ufName}?`,
      answer: data
        ? `Existem ${data.total_suppliers} fornecedores de ${sector.name} registrados em ${ufName} no PNCP.`
        : `Veja o total atualizado de fornecedores nesta pagina.`,
    },
  ];

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: `Fornecedores de ${sector.name} em ${ufName}`,
      description: `Ranking de fornecedores do setor ${sector.name} em ${ufName}, Brasil.`,
      url: `https://smartlic.tech/fornecedores/${setor}/${uf}`,
      temporalCoverage: `${year - 2}/${year}`,
      spatialCoverage: { '@type': 'Place', name: ufName },
      license: 'https://www.gov.br/compras/pt-br',
      creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
    },
    {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: `Top Fornecedores de ${sector.name} em ${ufName}`,
      numberOfItems: data?.supplier_ranking.length || 0,
      itemListElement: (data?.supplier_ranking || []).slice(0, 10).map((s, i) => ({
        '@type': 'ListItem',
        position: i + 1,
        name: s.nome,
        url: `https://smartlic.tech/cnpj/${s.cnpj}`,
      })),
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
      mainEntity: faqItems.map((f) => ({
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Fornecedores de {sector.name} em {ufName}
          </h1>
          <p className="text-gray-500 text-sm mb-6">
            {data?.last_updated ? getFreshnessLabel(data.last_updated) : 'Dados do PNCP'}
            {' · Fonte: Portal Nacional de Contratacoes Publicas'}
          </p>

          {!data || data.total_suppliers === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-500">
                Nenhum fornecedor de {sector.name} encontrado em {ufName} no periodo consultado.
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Os dados sao indexados diariamente do PNCP. Volte em breve.
              </p>
            </div>
          ) : (
            <>
              {/* KPI */}
              <div className="bg-white rounded-lg shadow-sm border p-5 mb-8 inline-block">
                <p className="text-sm text-gray-500">Total de Fornecedores</p>
                <p className="text-2xl font-bold text-gray-900">{data.total_suppliers.toLocaleString('pt-BR')}</p>
              </div>

              {/* Supplier Ranking */}
              <section className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-3">
                  Ranking de Fornecedores
                </h2>
                <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600">
                      <tr>
                        <th className="text-left px-4 py-3 w-10">#</th>
                        <th className="text-left px-4 py-3">Empresa</th>
                        <th className="text-right px-4 py-3">Contratos</th>
                        <th className="text-right px-4 py-3">Valor Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {data.supplier_ranking.map((s, i) => (
                        <tr key={s.cnpj} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-gray-400">{i + 1}</td>
                          <td className="px-4 py-2">
                            <Link href={`/cnpj/${s.cnpj}`} className="text-blue-600 hover:underline">
                              {s.nome}
                            </Link>
                          </td>
                          <td className="text-right px-4 py-2">{s.total_contratos}</td>
                          <td className="text-right px-4 py-2 text-green-700">{formatBRL(s.valor_total)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Top Buying Orgs */}
              {data.top_orgaos_compradores.length > 0 && (
                <section className="mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">Principais Orgaos Compradores</h2>
                  <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 text-gray-600">
                        <tr>
                          <th className="text-left px-4 py-3">Orgao</th>
                          <th className="text-right px-4 py-3">Contratos</th>
                          <th className="text-right px-4 py-3">Valor Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {data.top_orgaos_compradores.map((o) => (
                          <tr key={o.cnpj} className="hover:bg-gray-50">
                            <td className="px-4 py-2">
                              <Link href={`/orgaos/${o.cnpj}`} className="text-blue-600 hover:underline">
                                {o.nome}
                              </Link>
                            </td>
                            <td className="text-right px-4 py-2">{o.total_contratos}</td>
                            <td className="text-right px-4 py-2 text-green-700">{formatBRL(o.valor_total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
            </>
          )}

          {/* FAQ */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Perguntas Frequentes</h2>
            <div className="space-y-4">
              {faqItems.map((f, i) => (
                <details key={i} className="bg-white rounded-lg shadow-sm border p-4 group">
                  <summary className="font-medium text-gray-900 cursor-pointer">{f.question}</summary>
                  <p className="mt-2 text-sm text-gray-600">{f.answer}</p>
                </details>
              ))}
            </div>
          </section>

          {/* Internal Linking */}
          <section className="border-t border-gray-200 pt-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Paginas Relacionadas</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              <Link href={`/contratos/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Contratos de {sector.name} em {ufName}
              </Link>
              <Link href={`/alertas-publicos/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Alertas de {sector.name} em {ufName}
              </Link>
              <Link href={`/blog/licitacoes/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Licitacoes de {sector.name} em {ufName}
              </Link>
              <Link href="/fornecedores" className="text-blue-600 hover:underline">
                Todos os Setores
              </Link>
            </div>
          </section>

          {/* Lead Capture */}
          <section className="mt-12 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Encontre licitacoes de {sector.name} em {ufName}
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic monitora editais e contratos do PNCP automaticamente.
            </p>
            <Link
              href="/signup"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teste gratis por 14 dias
            </Link>
          </section>

          <p className="text-xs text-gray-400 mt-8">{data?.aviso_legal || 'Dados do PNCP. Atualizacao diaria.'}</p>
        </div>
      </main>
      <Footer />
    </>
  );
}
