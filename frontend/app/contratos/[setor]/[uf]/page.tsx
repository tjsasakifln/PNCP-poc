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
import {
  buildCanonical,
  buildOperationalTitle,
  buildOperationalDescription,
  getFreshnessLabel,
} from '@/lib/seo';
import { ssgLimitedFetch } from '@/lib/concurrency';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SeoBannerCta from '@/app/components/landing/SeoBannerCta';
import AlertEntityCta from '@/components/seo/AlertEntityCta';
import { PseoPageTracker } from '@/app/components/seo/PseoPageTracker';
import { PseoLink } from '@/app/components/seo/PseoLink';
import PreviewCTA from '@/app/components/programmatic/PreviewCTA';
import SectorUfIntelReportCTA from '@/app/components/SectorUfIntelReportCTA';
import { OpportunitySignalsPanel } from '@/app/components/OpportunitySignalsPanel';
import { resolveJourney } from '@/lib/seo/relatedResolver';
import { JourneyLinks } from '@/app/components/navigation/JourneyLinks';
import { ContratosUrgency } from '@/components/pseo/ContratosUrgency';

export const revalidate = 14400; // 4h ISR (reduzido de 24h para melhorar freshness dos dados)

export function generateStaticParams() {
  return generateSectorUfParams();
}

type Props = { params: Promise<{ setor: string; uf: string }> };

interface AtividadeRecente {
  contagem_30d: number;
  contagem_90d: number;
  valor_total_30d: number;
  tendencia_12m: string;
  tendencia_percentual: number;
  ultimo_evento_data: string | null;
  sazonalidade_mes_pico: number | null;
}

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
  atividade_recente: AtividadeRecente;
}

async function fetchContratosStats(setor: string, uf: string): Promise<ContratosStats | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await ssgLimitedFetch(`${backendUrl}/v1/contratos/${setor}/${uf}/stats`, {
      next: { revalidate: 14400 },
      signal: AbortSignal.timeout(10000),
    });
    if (res.status >= 500) {
      // Transient backend error — throw so ISR preserves last-good cache.
      throw new Error(`contratos_stats_backend_5xx:${res.status}`);
    }
    // 4xx (incl. 404) → genuine "no data" — render EmptyStateSEO.
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    if (err instanceof Error && err.message.startsWith('contratos_stats_backend_5xx')) throw err;
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
  // CONV-006b: operational promise title/description
  const totalValue = data ? `R$ ${(data.total_value / 1_000_000).toFixed(1)} mi` : undefined;
  const ufLabel = `${getUfPrep(ufUpper)} ${ufName}`;
  const sectorUf = `${sector.name} ${ufLabel}`;

  const ctx = {
    subject: sectorUf,
    sector: sector.name,
    uf: ufUpper,
    ufName,
    count: totalContracts,
    value: totalValue,
    orgao: data?.top_orgaos?.[0]?.nome,
    objeto: data?.sample_contracts?.[0]?.objeto,
  };
  const description = buildOperationalDescription('contrato', ctx);

  return {
    title: buildOperationalTitle('contrato', ctx),
    description,
    alternates: { canonical: buildCanonical(`/contratos/${setor}/${uf}`) }, // AC6
    openGraph: {
      title: `Contratos Públicos: ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Transparência em gastos públicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      type: 'website',
      locale: 'pt_BR',
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(`Contratos Públicos: ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`)}&subtitle=${encodeURIComponent(`${totalContracts.toLocaleString('pt-BR')} contratos firmados — fontes oficiais`)}`,
          width: 1200,
          height: 630,
          alt: `Contratos Públicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} | SmartLic`,
        },
      ],
    },
    robots: { index: shouldIndex, follow: true }, // AC4/AC5
  };
}

export default async function ContratosSetorUfPage({ params }: Props) {
  const { setor, uf } = await params;
  const sector = getSectorFromSlug(setor);
  if (!sector) notFound(); // adr-seo-001-allow: setor not in static sector catalog — true 404

  const ufUpper = uf.toUpperCase();
  if (!ALL_UFS.includes(ufUpper)) notFound(); // adr-seo-001-allow: uf not in canonical UF list — true 404

  const ufName = UF_NAMES[ufUpper] || ufUpper;

  // AC1: fetch paralelo — contratos históricos + editais ativos
  const [data, blogStats] = await Promise.all([
    fetchContratosStats(setor, ufUpper.toLowerCase()),
    fetchSectorUfBlogStats(setor, uf), // AC8: null se falhar, página degrada graciosamente
  ]);

  const year = new Date().getFullYear();
  const totalContracts = data?.total_contracts ?? 0;
  const totalEditais = blogStats?.total_editais ?? 0;

  // CONV-002 (#1311): Build signal data from existing contratos stats
  const contratosSignals: Array<{ icon: string; label: string; value: string; description: string }> = [];
  if (data && totalContracts > 0) {
    contratosSignals.push({
      icon: '📊',
      label: 'Total de Contratos',
      value: totalContracts.toLocaleString('pt-BR'),
      description: `Contratos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
    });
    contratosSignals.push({
      icon: '💰',
      label: 'Valor Total',
      value: formatBRL(data.total_value),
      description: 'Montante global contratado no período',
    });
    contratosSignals.push({
      icon: '💵',
      label: 'Valor Médio',
      value: formatBRL(data.avg_value),
      description: 'Ticket médio por contrato firmado',
    });
    if (data.top_orgaos.length > 0) {
      contratosSignals.push({
        icon: '🏛️',
        label: 'Principais Órgãos',
        value: `${data.top_orgaos.length} órgãos compradores`,
        description: data.top_orgaos.slice(0, 3).map((o) => o.nome).join(', '),
      });
    }
    if (data.top_fornecedores.length > 0) {
      contratosSignals.push({
        icon: '🏢',
        label: 'Fornecedores Recorrentes',
        value: `${data.top_fornecedores.length} fornecedores`,
        description: data.top_fornecedores.slice(0, 3).map((f) => f.nome).join(', '),
      });
    }
  }

  // CONV-017 (#1332): Build intent-progressive journey for this contrato page.
  const journey = resolveJourney({
    type: 'contrato',
    value: setor,
    currentUrl: `/contratos/${setor}/${uf}`,
    sectorSlug: setor,
    sectorName: sector.name,
    uf: ufUpper,
    ufName,
  });

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Contratos Públicos', url: '/contratos' },
    { name: sector.name, url: `/contratos/${setor}/${uf}` },
    { name: ufName, url: `/contratos/${setor}/${uf}` },
  ];

  const faqItems = [
    {
      question: `Quanto o governo de ${ufName} gasta em ${sector.name}?`,
      answer: data
        ? `Nos contratos registrados nas fontes oficiais, ${ufName} tem ${data.total_contracts} contratos de ${sector.name} com valor total de ${formatBRL(data.total_value)}.`
        : `Consulte os dados atualizados nesta página para ver os contratos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}.`,
    },
    {
      question: `Quais órgãos de ${ufName} mais contratam ${sector.name}?`,
      answer: data && data.top_orgaos.length > 0
        ? `Os maiores compradores são: ${data.top_orgaos.slice(0, 3).map((o) => o.nome).join(', ')}.`
        : `Veja a lista completa de órgãos compradores nesta página.`,
    },
    ...(totalEditais > 0
      ? [
          {
            question: `Há editais abertos de ${sector.name} em ${ufName} agora?`,
            answer: `Sim, há ${totalEditais} ${totalEditais === 1 ? 'edital aberto' : 'editais abertos'} de ${sector.name} ${getUfPrep(ufUpper)} ${ufName} nos últimos 30 dias. Acesse o SmartLic para ver todos com detalhes de valor e prazos.`,
          },
        ]
      : []),
    {
      question: `Como consultar contratos públicos de ${sector.name}?`,
      answer: `O SmartLic agrega dados das fontes oficiais e permite consultar contratos por setor e estado. Os dados são atualizados diariamente.`,
    },
  ];

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Dataset',
      name: `Contratos Públicos de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`,
      description: `Dados de contratos públicos do setor ${sector.name} ${getUfPrep(ufUpper)} ${ufName}, Brasil.`,
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
      {/* CONV-009b (#1325): pSEO analytics — scroll depth + engagement */}
      <PseoPageTracker
        sourceTemplate="contrato_page"
        entityId={`${setor}/${uf}`}
        setor={setor}
        uf={ufUpper}
      />
      <LandingNavbar />
      {/* CONV-002b: Sticky bottom mobile CTA — contextual */}
      <div
        className="fixed bottom-0 left-0 right-0 z-40 sm:hidden bg-brand-navy text-white px-4 py-3 shadow-lg"
        data-testid="pseo-sticky-cta"
      >
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-medium">
            {totalContracts} contratos · {sector.name} {ufName}
          </span>
          <Link
            href={`/consultoria-b2g?ref=contratos-${setor}-${uf}-sticky`}
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Contratos Públicos de {sector.name} {getUfPrep(ufUpper)} {ufName}
          </h1>
          <p className="text-gray-500 text-sm mb-6">
            {data?.last_updated ? getFreshnessLabel(data.last_updated) : 'Dados das fontes oficiais'}
            {' · Fonte: Portal Nacional de Contratações Públicas'}
          </p>

          {/* AC4: empty state apenas quando AMBOS os datasets estão zerados */}
          {totalContracts === 0 && totalEditais === 0 ? (
            <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
              <p className="text-gray-500">
                Nenhum contrato de {sector.name} encontrado {getUfPrep(ufUpper)} {ufName} no periodo consultado.
              </p>
              <p className="text-sm text-gray-400 mt-2">
                Os dados são indexados diariamente das fontes oficiais. Volte em breve.
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
                      <p className="text-sm text-gray-500">Valor Médio</p>
                      <p className="text-2xl font-bold text-gray-900">{formatBRL(data.avg_value)}</p>
                    </div>
                  </div>

                  {/* CONV-016: urgency signal — recent contract activity */}
                  <ContratosUrgency
                    atividade_recente={data.atividade_recente}
                    sectorName={data.sector_name}
                    ufLabel={ufName}
                  />

                  {/* CONV-002 (#1311): OpportunitySignalsPanel — sinais do mercado de contratos */}
                  {contratosSignals.length > 0 && (
                    <div className="mb-8">
                      <OpportunitySignalsPanel
                        sourceTemplate="contrato_page"
                        entityId={`${setor}/${uf}`}
                        setor={setor}
                        uf={ufUpper}
                        heading={`Mercado de ${sector.name} ${getUfPrep(ufUpper)} ${ufName}`}
                        subheading="Visão consolidada dos contratos públicos"
                        signals={contratosSignals}
                        compact
                        cta={{
                          label: 'Explorar contratos similares',
                          href: `/consultoria-b2g?ref=contratos-${setor}-${uf}&utm_source=pseo&utm_medium=organic&utm_content=contrato_page`,
                          secondaryLabel: 'Desbloquear órgãos compradores do segmento',
                          secondaryHref: `/consultoria-b2g?ref=contratos-organs-${setor}`,
                        }}
                      />
                    </div>
                  )}

                  {/* #633: Mapa de Oportunidade Setorial — first microtransaction CTA */}
                  <div className="mb-8">
                    <SectorUfIntelReportCTA
                      sectorName={setor}
                      uf={ufUpper.toLowerCase()}
                      variant="inline"
                    />
                  </div>

                  {/* Top Orgaos */}
                  {data.top_orgaos.length > 0 && (
                    <section className="mb-8">
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Principais Órgãos Compradores</h2>
                      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-gray-600">
                            <tr>
                              <th className="text-left px-4 py-3">Órgão</th>
                              <th className="text-right px-4 py-3">Contratos</th>
                              <th className="text-right px-4 py-3">Valor Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {data.top_orgaos.map((o) => (
                              <tr key={o.cnpj} className="hover:bg-gray-50">
                                <td className="px-4 py-2">
                                  <Link href={`/contratos/orgao/${o.cnpj}`} className="text-blue-600 hover:underline">
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

                  {/* Inline CTA mid-page — após tabela de fornecedores */}
                  <div className="my-6 rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <p className="text-sm text-gray-700">
                      <strong>{totalContracts.toLocaleString('pt-BR')} contratos</strong> de{' '}
                      {sector.name} em {ufName}
                      {totalEditais > 0 && (
                        <>
                          {' '}
                          — <strong>{totalEditais} editais abertos</strong> agora
                        </>
                      )}
                      .
                    </p>
                    <PseoLink
                      href={`/consultoria-b2g?ref=contratos-mid&setor=${setor}&uf=${uf}`}
                      className="text-sm font-bold text-white bg-green-600 hover:bg-green-700 px-4 py-2 rounded-md whitespace-nowrap w-full sm:w-auto text-center"
                      eventName="pseo_alert_signup"
                      sourceTemplate="contrato_page"
                      setor={setor}
                      uf={ufUpper}
                    >
                      Ver editais agora →
                    </PseoLink>
                  </div>

                  {/* Sample Contracts */}
                  {data.sample_contracts.length > 0 && (
                    <section className="mb-8">
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Contratos Recentes</h2>
                      <div className="space-y-3">
                        {data.sample_contracts.map((c, i) => (
                          <div key={i} className="bg-white rounded-lg shadow-sm border p-4">
                            <p className="font-medium text-gray-900 text-sm">{c.objeto}</p>
                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
                              <span>Órgão: {c.orgao}</span>
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
                      <h2 className="text-xl font-semibold text-gray-900 mb-3">Evolução Mensal</h2>
                      <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-gray-600">
                            <tr>
                              <th className="text-left px-4 py-3">Mês</th>
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

                  {/* CONV-002b: PreviewCTA — 3 contratos reais + 3 blurred (degustação) */}
                  {data.sample_contracts.length > 0 && (
                    <section className="mb-8">
                      <PreviewCTA
                        setor={setor}
                        uf={ufUpper.toLowerCase()}
                        setorLabel={sector.name}
                        ufLabel={ufName}
                        totalOpen={totalContracts}
                      />
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
                    <PseoLink
                      href={`/consultoria-b2g?ref=contratos-mid&setor=${setor}&uf=${uf}`}
                      className="inline-block px-5 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-sm"
                      eventName="pseo_alert_signup"
                      sourceTemplate="contrato_page"
                      setor={setor}
                      uf={ufUpper}
                    >
                      Ver todos os editais de {sector.name} em {ufName} →
                    </PseoLink>
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

          {/* CONV-017 (#1332): JourneyLinks replaces flat "Páginas Relacionadas" */}
          <JourneyLinks journey={journey} sourceTemplate="contrato" />

          {/* CONV-002b: Lead Capture — contextual CTA + "Só quero ver os dados" */}
          <section className="mt-12 rounded-2xl border border-brand-blue/30 bg-brand-blue/5 dark:bg-brand-blue/10 p-6 sm:p-8">
            <p className="text-lg text-gray-900 dark:text-white mb-4">
              Quer receber os próximos contratos de {sector.name} em {ufName}?
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <PseoLink
                href={`/consultoria-b2g?ref=contratos-${setor}-${uf}`}
                className="inline-block px-6 py-3 bg-brand-blue text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-center"
                eventName="pseo_alert_signup"
                sourceTemplate="contrato_page"
                setor={setor}
                uf={ufUpper}
              >
                Receber alertas grátis 14 dias →
              </PseoLink>
              <Link
                href={`/observatorio/${setor}`}
                className="inline-block px-6 py-3 bg-white dark:bg-gray-900 text-brand-navy dark:text-white font-medium rounded-lg border border-gray-300 dark:border-gray-700 hover:border-brand-blue transition-colors text-center"
              >
                Só quero ver os dados
              </Link>
            </div>
          </section>

          {/* CONV-014: Alert CTA — criar alerta de setor em UF */}
          <div className="mt-8">
            <AlertEntityCta
              entityType="setor"
              entityId={setor}
              entityLabel={sector.name}
              uf={ufUpper}
            />
          </div>

          <p className="text-xs text-gray-400 mt-8">{data?.aviso_legal || 'Dados das fontes oficiais. Atualização diária.'}</p>
        </div>
      </main>
      <SeoBannerCta setor={setor} uf={uf} />
      <Footer />
    </>
  );
}
