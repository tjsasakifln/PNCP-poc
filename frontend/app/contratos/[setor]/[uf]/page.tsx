import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  generateSectorUfParams,
  getSectorFromSlug,
  getUfPrep,
  ALL_UFS,
  UF_NAMES,
  fetchSectorUfBlogStats,
} from '@/lib/programmatic';
import { formatBRL } from '@/lib/sectors';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

export const revalidate = 86400; // 24h ISR — AC11

export function generateStaticParams() {
  return generateSectorUfParams();
}

type Props = { params: Promise<{ setor: string; uf: string }> };

interface ContratosStats {
  sector_id: string;
  sector_name: string;
  uf: string;
  total_contracts: number;
  total_value: number;
  avg_value: number;
  top_orgaos: { nome: string; cnpj: string; total_contratos: number; valor_total: number }[];
  top_fornecedores: { nome: string; cnpj: string; total_contratos: number; valor_total: number }[];
  monthly_trend: { month: string; count: number; value: number }[];
  sample_contracts: { objeto: string; orgao: string; fornecedor: string; valor: number | null; data_assinatura: string }[];
  last_updated: string;
  aviso_legal: string;
}

async function fetchContratosStats(setor: string, uf: string): Promise<ContratosStats | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/contratos/${setor}/${uf}/stats`, {
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

  // AC1: fetch paralelo de contratos e editais
  const [data, blogStats] = await Promise.all([
    fetchContratosStats(setor, ufUpper.toLowerCase()),
    fetchSectorUfBlogStats(setor, uf), // AC8: retorna null em caso de falha
  ]);

  const totalContracts = data?.total_contracts ?? 0;
  const totalEditais = blogStats?.total_editais ?? 0;

  // AC4/AC5: noindex apenas quando AMBOS os datasets estão zerados
  const shouldIndex = totalContracts >= 1 || totalEditais >= 1;

  // AC7: description dinâmica — menciona editais quando disponíveis
  let description: string;
  if (totalContracts > 0 && totalEditais > 0) {
    description = `${totalContracts.toLocaleString('pt-BR')} contratos firmados em ${sector.name} ${getUfPrep(ufUpper)} ${ufName} — ${totalEditais} editais abertos agora. Dados PNCP atualizados.`;
  } else if (totalContracts > 0) {
    description = `Quanto o governo gasta em ${sector.name} ${getUfPrep(ufUpper)} ${ufName}? Veja ${totalContracts.toLocaleString('pt-BR')} contratos firmados, principais órgãos compradores e fornecedores. Dados PNCP atualizados.`;
  } else if (totalEditais > 0) {
    description = `${totalEditais} editais abertos em ${sector.name} ${getUfPrep(ufUpper)} ${ufName} agora. Acompanhe oportunidades de licitação e o histórico de contratos públicos.`;
  } else {
    description = `Dados de contratos públicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}. Fonte: Portal Nacional de Contratações Públicas.`;
  }

  return {
    title: `Contratos Publicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} ${year} — SmartLic`,
    description,
    alternates: { canonical: buildCanonical(`/contratos/${setor}/${uf}`) }, // AC6
    openGraph: {
      title: `Contratos Publicos: ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Transparencia em gastos publicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: shouldIndex, follow: true }, // AC4/AC5
  };
}

export default async function ContratosSetorUfPage({ params }: Props) {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound();

  const ufUpper = uf.toUpperCase();
  if (!ALL_UFS.includes(ufUpper)) notFound();

  const ufName = UF_NAMES[ufUpper] || ufUpper;

  // AC1: fetch paralelo — contratos históricos + editais ativos
  const [data, blogStats] = await Promise.all([
    fetchContratosStats(setor, ufUpper.toLowerCase()),
    fetchSectorUfBlogStats(setor, uf), // AC8: null se falhar, página degrada graciosamente
  ]);

  const year = new Date().getFullYear();
  const totalContracts = data?.total_contracts ?? 0;
  const totalEditais = blogStats?.total_editais ?? 0;

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Contratos Publicos', url: '/contratos' },
    { name: sector.name, url: `/contratos/${setor}/${uf}` },
    { name: ufName, url: `/contratos/${setor}/${uf}` },
  ];

  const faqItems = [
    {
      question: `Quanto o governo de ${ufName} gasta em ${sector.name}?`,
      answer: data
        ? `Nos contratos registrados no PNCP, ${ufName} tem ${data.total_contracts} contratos de ${sector.name} com valor total de ${formatBRL(data.total_value)}.`
        : `Consulte os dados atualizados nesta pagina para ver os contratos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}.`,
    },
    {
      question: `Quais orgaos de ${ufName} mais contratam ${sector.name}?`,
      answer: data && data.top_orgaos.length > 0
        ? `Os maiores compradores sao: ${data.top_orgaos.slice(0, 3).map((o) => o.nome).join(', ')}.`
        : `Veja a lista completa de orgaos compradores nesta pagina.`,
    },
    ...(totalEditais > 0
      ? [
          {
            question: `Ha editais abertos de ${sector.name} em ${ufName} agora?`,
            answer: `Sim, ha ${totalEditais} ${totalEditais === 1 ? 'edital aberto' : 'editais abertos'} de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} nos ultimos 30 dias. Acesse o SmartLic para ver todos com detalhes de valor e prazos.`,
          },
        ]
      : []),
    {
      question: `Como consultar contratos publicos de ${sector.name}?`,
      answer: `O SmartLic agrega dados do PNCP e permite consultar contratos por setor e estado. Os dados sao atualizados diariamente.`,
    },
  ];

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: `Contratos Publicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Dados de contratos publicos do setor ${sector.name} ${getUfPrep(ufUpper)} ${ufName}, Brasil.`,
      url: `https://smartlic.tech/contratos/${setor}/${uf}`,
      temporalCoverage: `${year - 2}/${year}`,
      spatialCoverage: { '@type': 'Place', name: ufName },
      license: 'https://www.gov.br/compras/pt-br',
      creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
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
            Contratos Publicos de {sector.name} {getUfPrep(ufUpper)} {ufName}
          </h1>
          <p className="text-gray-500 text-sm mb-6">
            {data?.last_updated ? getFreshnessLabel(data.last_updated) : 'Dados do PNCP'}
            {' · Fonte: Portal Nacional de Contratacoes Publicas'}
          </p>

          {/* AC4: empty state apenas quando AMBOS os datasets estão zerados */}
          {totalContracts === 0 && totalEditais === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-500">
                Nenhum contrato de {sector.name} encontrado {getUfPrep(ufUpper)} {ufName} no periodo consultado.
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Os dados sao indexados diariamente do PNCP. Volte em breve.
              </p>
            </div>
          ) : (
            <>
              {/* Seções de contratos históricos — visíveis somente quando há dados */}
              {data && totalContracts > 0 && (
                <>
                  {/* KPI Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                    <div className="bg-white rounded-lg shadow-sm border p-5">
                      <p className="text-sm text-gray-500">Total de Contratos</p>
                      <p className="text-2xl font-bold text-gray-900">{data.total_contracts.toLocaleString('pt-BR')}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border p-5">
                      <p className="text-sm text-gray-500">Valor Total</p>
                      <p className="text-2xl font-bold text-green-700">{formatBRL(data.total_value)}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border p-5">
                      <p className="text-sm text-gray-500">Valor Medio</p>
                      <p className="text-2xl font-bold text-gray-900">{formatBRL(data.avg_value)}</p>
                    </div>
                  </div>

                  {/* Top Orgaos */}
                  {data.top_orgaos.length > 0 && (
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
                            {data.top_orgaos.map((o) => (
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

                  {/* Top Fornecedores */}
                  {data.top_fornecedores.length > 0 && (
                    <section className="mb-8">
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Principais Fornecedores</h2>
                      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-gray-600">
                            <tr>
                              <th className="text-left px-4 py-3">Fornecedor</th>
                              <th className="text-right px-4 py-3">Contratos</th>
                              <th className="text-right px-4 py-3">Valor Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {data.top_fornecedores.map((f) => (
                              <tr key={f.cnpj} className="hover:bg-gray-50">
                                <td className="px-4 py-2">
                                  <Link href={`/cnpj/${f.cnpj}`} className="text-blue-600 hover:underline">
                                    {f.nome}
                                  </Link>
                                </td>
                                <td className="text-right px-4 py-2">{f.total_contratos}</td>
                                <td className="text-right px-4 py-2 text-green-700">{formatBRL(f.valor_total)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  )}

                  {/* Sample Contracts */}
                  {data.sample_contracts.length > 0 && (
                    <section className="mb-8">
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Contratos Recentes</h2>
                      <div className="space-y-3">
                        {data.sample_contracts.map((c, i) => (
                          <div key={i} className="bg-white rounded-lg shadow-sm border p-4">
                            <p className="font-medium text-gray-900 text-sm">{c.objeto}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
                              <span>Orgao: {c.orgao}</span>
                              <span>Fornecedor: {c.fornecedor}</span>
                              {c.valor && <span className="text-green-700">{formatBRL(c.valor)}</span>}
                              <span>{c.data_assinatura}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Monthly Trend */}
                  {data.monthly_trend.some((m) => m.count > 0) && (
                    <section className="mb-8">
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Evolucao Mensal</h2>
                      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-gray-600">
                            <tr>
                              <th className="text-left px-4 py-3">Mes</th>
                              <th className="text-right px-4 py-3">Contratos</th>
                              <th className="text-right px-4 py-3">Valor</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {data.monthly_trend.filter((m) => m.count > 0).map((m) => (
                              <tr key={m.month} className="hover:bg-gray-50">
                                <td className="px-4 py-2">{m.month}</td>
                                <td className="text-right px-4 py-2">{m.count}</td>
                                <td className="text-right px-4 py-2 text-green-700">{formatBRL(m.value)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </section>
                  )}
                </>
              )}

              {/* AC2/AC3: Seção "Editais Abertos Agora" — abaixo dos contratos, só quando total_editais > 0 */}
              {totalEditais > 0 && blogStats && (
                <section className="mb-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-3">Editais Abertos Agora</h2>
                  <div className="bg-white rounded-lg shadow-sm border p-5">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
                      <div>
                        <p className="text-sm text-gray-500">Editais nos últimos 30 dias</p>
                        <p className="text-2xl font-bold text-blue-700">{totalEditais.toLocaleString('pt-BR')}</p>
                      </div>
                      {blogStats.value_range_min > 0 && (
                        <div>
                          <p className="text-sm text-gray-500">Faixa de valores</p>
                          <p className="font-semibold text-gray-900">
                            {formatBRL(blogStats.value_range_min)} – {formatBRL(blogStats.value_range_max)}
                          </p>
                        </div>
                      )}
                      {blogStats.avg_value > 0 && (
                        <div>
                          <p className="text-sm text-gray-500">Valor médio por edital</p>
                          <p className="font-semibold text-gray-900">{formatBRL(blogStats.avg_value)}</p>
                        </div>
                      )}
                    </div>
                    <Link
                      href="/buscar"
                      className="inline-block px-5 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-sm"
                    >
                      Ver todos no SmartLic →
                    </Link>
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
              <Link href={`/fornecedores/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Fornecedores de {sector.name} {getUfPrep(ufUpper)} {ufName}
              </Link>
              <Link href={`/alertas-publicos/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Alertas de {sector.name} {getUfPrep(ufUpper)} {ufName}
              </Link>
              <Link href={`/blog/licitacoes/${setor}/${uf}`} className="text-blue-600 hover:underline">
                Licitacoes de {sector.name} {getUfPrep(ufUpper)} {ufName}
              </Link>
              <Link href="/contratos" className="text-blue-600 hover:underline">
                Todos os Setores
              </Link>
            </div>
          </section>

          {/* Lead Capture */}
          <section className="mt-12 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore contratos de {sector.name} {getUfPrep(ufUpper)} {ufName}
            </h2>
            <p className="text-gray-600 mb-4">
              Receba alertas quando novos contratos forem publicados no PNCP.
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
