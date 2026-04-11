import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import SchemaMarkup from '@/components/blog/SchemaMarkup';
import BlogCTA from '@/components/blog/BlogCTA';
import RelatedPages from '@/components/blog/RelatedPages';
import HistoricalContractsFallback from '@/components/blog/HistoricalContractsFallback';
import {
  generateLicitacoesParams,
  fetchSectorUfBlogStats,
  getSectorFromSlug,
  formatBRL,
  getRegionalEditorial,
  ALL_UFS,
  UF_NAMES,
} from '@/lib/programmatic';
import {
  fetchContratosSetorUfStats,
  buildContractsContext,
  generateLicitacoesFAQsWithFallback,
} from '@/lib/contracts-fallback';
import { getCitiesByUf } from '@/lib/cities';
import { getFreshnessLabel } from '@/lib/seo';

/**
 * MKT-003 AC1: Sector × UF programmatic page.
 *
 * Route: /blog/licitacoes/{setor}/{uf}
 * Optional ?modalidade=6 query param for SEO-CAC-ZERO A1 modalidade variants.
 * ISR 24h. Phase 1: 5 sectors × 5 UFs = 25 pages.
 */

const MODALIDADE_MAP: Record<number, { name: string; slug: string; description: string; legalBasis: string; typicalProcess: string }> = {
  4: {
    name: 'Concorrência Eletrônica',
    slug: 'concorrencia-eletronica',
    description: 'Modalidade para contratações de maior valor, conduzida integralmente em ambiente digital. Permite ampla participação de fornecedores com critérios objetivos de julgamento.',
    legalBasis: 'Art. 6º, XXXVIII e Arts. 33-39 da Lei 14.133/2021',
    typicalProcess: 'Publicação do edital → Fase de propostas (mín. 35 dias úteis) → Julgamento → Habilitação → Adjudicação → Homologação',
  },
  5: {
    name: 'Concorrência Presencial',
    slug: 'concorrencia-presencial',
    description: 'Modalidade para contratações de maior valor realizada em sessão presencial. Utilizada quando a natureza do objeto requer avaliação in loco ou demonstração física.',
    legalBasis: 'Art. 6º, XXXVIII e Arts. 33-39 da Lei 14.133/2021',
    typicalProcess: 'Publicação do edital → Entrega de envelopes → Abertura de propostas → Habilitação → Adjudicação → Homologação',
  },
  6: {
    name: 'Pregão Eletrônico',
    slug: 'pregao-eletronico',
    description: 'Modalidade mais utilizada em licitações públicas brasileiras. Destinada à aquisição de bens e serviços comuns, conduzida integralmente em plataforma digital com fase de lances.',
    legalBasis: 'Art. 6º, XLI e Arts. 28-32 da Lei 14.133/2021; Decreto 10.024/2019',
    typicalProcess: 'Publicação do edital → Fase de propostas (mín. 8 dias úteis) → Fase de lances → Negociação → Habilitação → Adjudicação',
  },
  7: {
    name: 'Pregão Presencial',
    slug: 'pregao-presencial',
    description: 'Modalidade para bens e serviços comuns realizada em sessão presencial com lances verbais. Cada vez menos utilizada após obrigatoriedade do formato eletrônico.',
    legalBasis: 'Art. 6º, XLI da Lei 14.133/2021 (uso restrito)',
    typicalProcess: 'Publicação do edital → Credenciamento → Classificação inicial → Lances verbais → Negociação → Habilitação',
  },
  8: {
    name: 'Dispensa de Licitação',
    slug: 'dispensa',
    description: 'Contratação direta sem competição entre fornecedores, permitida em casos específicos previstos em lei, como valores abaixo do limite ou situações emergenciais.',
    legalBasis: 'Arts. 74-75 da Lei 14.133/2021',
    typicalProcess: 'Justificativa da contratação → Pesquisa de preços → Parecer jurídico → Autorização → Empenho → Contrato',
  },
  12: {
    name: 'Credenciamento',
    slug: 'credenciamento',
    description: 'Processo pelo qual a Administração convoca interessados para prestar serviços ou fornecer bens, credenciando todos que atendam às condições exigidas.',
    legalBasis: 'Art. 79 da Lei 14.133/2021',
    typicalProcess: 'Chamamento público → Inscrição → Análise documental → Credenciamento → Convocação por rodízio ou demanda',
  },
};

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return generateLicitacoesParams();
}

function getMonthYear(): string {
  const now = new Date();
  const months = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ];
  return `${months[now.getMonth()]} ${now.getFullYear()}`;
}

function getTrendIndicator(trend: { period: string; count: number }[]): {
  text: string;
  direction: 'up' | 'down' | 'stable';
  pct: number;
} {
  if (!trend || trend.length < 2) return { text: 'Estável', direction: 'stable', pct: 0 };
  const latest = trend[trend.length - 1].count;
  const previous = trend[trend.length - 2].count;
  if (previous === 0) return { text: 'Novo', direction: 'up', pct: 0 };
  const pct = Math.round(((latest - previous) / previous) * 100);
  if (pct > 5) return { text: `+${pct}%`, direction: 'up', pct };
  if (pct < -5) return { text: `${pct}%`, direction: 'down', pct };
  return { text: 'Estável', direction: 'stable', pct: 0 };
}

export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<{ setor: string; uf: string }>;
  searchParams?: Promise<{ modalidade?: string }>;
}): Promise<Metadata> {
  const { setor, uf } = await params;
  const resolvedSearch = searchParams ? await searchParams : {};
  const modalidadeCode = resolvedSearch?.modalidade ? parseInt(resolvedSearch.modalidade, 10) : null;
  const modalidadeInfo = modalidadeCode ? (MODALIDADE_MAP[modalidadeCode] ?? null) : null;

  const ufUpper = uf.toUpperCase();
  const sector = getSectorFromSlug(setor);
  if (!sector || !ALL_UFS.includes(ufUpper)) return { title: 'Página não encontrada' };

  const stats = await fetchSectorUfBlogStats(setor, ufUpper);
  const total = stats?.total_editais ?? 0;
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  // Canonical sempre aponta para URL base sem parâmetros (ISSUE-SEO-002).
  // ?modalidade=X é comportamento de UI — não deve ser indexado como página separada.
  const canonicalUrl = `https://smartlic.tech/blog/licitacoes/${setor}/${uf}`;
  const modalidadeSuffix = modalidadeInfo ? ` — ${modalidadeInfo.name}` : '';

  return {
    title: `${total > 0 ? `${total} ` : ''}Licitações de ${sector.name} em ${ufName}${modalidadeSuffix} — ${getMonthYear()}`,
    description: `Encontre ${total > 0 ? total : ''} licitações de ${sector.name.toLowerCase()}${modalidadeInfo ? ` via ${modalidadeInfo.name}` : ''} em ${ufName}. Dados ao vivo de PNCP, PCP e ComprasGov. Filtre por valor, modalidade e prazo. Teste grátis.`,
    alternates: { canonical: canonicalUrl },
    openGraph: {
      title: `${total > 0 ? `${total} ` : ''}Licitações de ${sector.name} em ${ufName}${modalidadeSuffix} — ${getMonthYear()} | SmartLic`,
      description: `${total > 0 ? `${total} editais` : 'Editais'} de ${sector.name.toLowerCase()} em ${ufName}${modalidadeInfo ? ` (${modalidadeInfo.name})` : ''}. Dados ao vivo consolidados de 3 fontes oficiais.`,
      url: canonicalUrl,
      type: 'article',
      locale: 'pt_BR',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Licitações de ${sector.name} em ${ufName}${modalidadeSuffix} | SmartLic`,
    },
  };
}

export default async function LicitacoesSectorUfPage({
  params,
  searchParams,
}: {
  params: Promise<{ setor: string; uf: string }>;
  searchParams?: Promise<{ modalidade?: string }>;
}) {
  const { setor, uf } = await params;
  const resolvedSearch = searchParams ? await searchParams : {};
  const modalidadeCode = resolvedSearch?.modalidade ? parseInt(resolvedSearch.modalidade, 10) : null;
  const modalidadeInfo = modalidadeCode ? (MODALIDADE_MAP[modalidadeCode] ?? null) : null;

  const ufUpper = uf.toUpperCase();
  const sector = getSectorFromSlug(setor);
  if (!sector || !ALL_UFS.includes(ufUpper)) notFound();

  const stats = await fetchSectorUfBlogStats(setor, ufUpper);
  const ufName = UF_NAMES[ufUpper] || ufUpper;
  const monthYear = getMonthYear();

  // Zero-state fallback: if no open editais, try to surface historical contracts
  // from pncp_supplier_contracts so the page still delivers real value (and the
  // FAQ stops contradicting the "0 editais" counter).
  const hasZeroEditais = !stats || stats.total_editais === 0;
  const contractsFallback = hasZeroEditais
    ? await fetchContratosSetorUfStats(setor, ufUpper)
    : null;
  const contractsContext = buildContractsContext(contractsFallback);

  const faqs = generateLicitacoesFAQsWithFallback(
    sector.name,
    ufName,
    stats?.total_editais,
    stats?.avg_value,
    contractsContext,
  );
  const modalidadeFaqs = modalidadeInfo ? [
    {
      question: `Como funciona o ${modalidadeInfo.name} para ${sector.name} em ${ufName}?`,
      answer: `${modalidadeInfo.typicalProcess}. Para o setor de ${sector.name} em ${ufName}, o SmartLic monitora automaticamente todos os editais publicados nesta modalidade.`,
    },
    {
      question: `Quantos editais de ${modalidadeInfo.name} de ${sector.name} abrem por mês em ${ufName}?`,
      answer: `Nos últimos 30 dias, ${stats?.total_editais ?? 0} editais de ${sector.name} foram publicados em ${ufName}. A proporção de ${modalidadeInfo.name} varia conforme o período.`,
    },
    {
      question: `Qual a base legal do ${modalidadeInfo.name}?`,
      answer: `O ${modalidadeInfo.name} é regulamentado por ${modalidadeInfo.legalBasis}. ${modalidadeInfo.description}`,
    },
  ] : [];
  const allFaqs = [...modalidadeFaqs, ...faqs];
  const editorial = getRegionalEditorial(sector.name, ufUpper, ufName);
  const slug = `licitacoes/${setor}/${uf}`;
  const url = `https://smartlic.tech/blog/${slug}`;
  const trend = stats?.trend_90d ? getTrendIndicator(stats.trend_90d) : null;

  // Modality percentages
  const totalModCount = stats?.top_modalidades?.reduce((s, m) => s + m.count, 0) ?? 0;

  const breadcrumbs = [
    { name: 'SmartLic', url: 'https://smartlic.tech' },
    { name: 'Blog', url: 'https://smartlic.tech/blog' },
    { name: 'Licitações', url: 'https://smartlic.tech/blog/licitacoes' },
    { name: sector.name, url: `https://smartlic.tech/licitacoes/${setor}` },
    { name: ufName, url },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />

      <SchemaMarkup
        pageType="sector-uf"
        title={`Licitações de ${sector.name} em ${ufName}${modalidadeInfo ? ` — ${modalidadeInfo.name}` : ''} — ${monthYear}`}
        description={`${stats?.total_editais ?? 0} licitações de ${sector.name} em ${ufName}`}
        url={url}
        sectorName={sector.name}
        uf={ufUpper}
        totalEditais={stats?.total_editais}
        breadcrumbs={breadcrumbs}
        faqs={allFaqs}
        dataPoints={[
          { name: 'Total de Editais', value: stats?.total_editais ?? 0 },
          { name: 'Valor Mínimo', value: stats?.value_range_min ?? 0 },
          { name: 'Valor Máximo', value: stats?.value_range_max ?? 0 },
          { name: 'Valor Médio', value: stats?.avg_value ?? 0 },
        ]}
      />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6">
              <Link href="/blog" className="hover:text-brand-blue">Blog</Link>
              <span>/</span>
              <Link href="/blog/licitacoes" className="hover:text-brand-blue">Licitações</Link>
              <span>/</span>
              <Link href={`/licitacoes/${setor}`} className="hover:text-brand-blue">
                {sector.name}
              </Link>
              <span>/</span>
              <span className="text-ink">{ufName}</span>
            </nav>

            {/* AC2: H1 with month and year; modalidade suffix when ?modalidade= param present */}
            <h1
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-ink tracking-tight mb-4"
            >
              Licitações de {sector.name} em {ufName}
              {modalidadeInfo ? ` — ${modalidadeInfo.name}` : ''} — {monthYear}
            </h1>

            {modalidadeInfo && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-brand-blue/10 text-brand-blue mb-3">
                {modalidadeInfo.name}
              </span>
            )}

            <p className="text-base sm:text-lg text-ink-secondary max-w-2xl leading-relaxed">
              {stats?.total_editais ?? 0} editais publicados nos últimos 30 dias.
              {stats?.value_range_min && stats?.value_range_max
                ? ` Faixa de valores: ${formatBRL(stats.value_range_min)} a ${formatBRL(stats.value_range_max)}.`
                : ''}
            </p>

            {/* AC4: Badge "Dados atualizados em {data}" + granular freshness label */}
            {stats && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <p className="inline-flex items-center gap-2 text-sm text-ink-secondary bg-surface-2 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 rounded-full bg-green-500" />
                  Dados atualizados em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
                </p>
                <time
                  dateTime={new Date(stats.last_updated).toISOString()}
                  className="text-xs text-ink-muted"
                >
                  {getFreshnessLabel(stats.last_updated)}
                </time>
              </div>
            )}
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* AC2: Stats grid — count, value range, modalities, trend */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Editais Abertos</p>
              <p className="text-2xl font-bold text-ink">{stats?.total_editais ?? 0}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Valor Médio</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats?.avg_value ?? 0)}</p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Faixa de Valores</p>
              <p className="text-lg font-bold text-ink">
                {stats?.value_range_min ? formatBRL(stats.value_range_min) : 'R$ 0'}
                <span className="text-ink-secondary font-normal text-sm"> a </span>
                {stats?.value_range_max ? formatBRL(stats.value_range_max) : 'R$ 0'}
              </p>
            </div>
            <div className="p-4 rounded-lg border border-[var(--border)] text-center">
              <p className="text-sm text-ink-secondary mb-1">Tendência 90 dias</p>
              {trend && (
                <p className={`text-2xl font-bold ${
                  trend.direction === 'up' ? 'text-green-600' :
                  trend.direction === 'down' ? 'text-red-600' :
                  'text-ink'
                }`}>
                  {trend.direction === 'up' && '↑ '}
                  {trend.direction === 'down' && '↓ '}
                  {trend.text}
                </p>
              )}
            </div>
          </div>

          {/* AC2: Modality percentages */}
          {stats && stats.top_modalidades && stats.top_modalidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Modalidades predominantes
              </h2>
              <div className="space-y-3">
                {stats.top_modalidades.map((mod) => {
                  const pct = totalModCount > 0 ? Math.round((mod.count / totalModCount) * 100) : 0;
                  return (
                    <div key={mod.name} className="flex items-center gap-3">
                      <span className="text-sm text-ink-secondary w-48 shrink-0 truncate">{mod.name}</span>
                      <div className="flex-1 bg-surface-2 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-brand-blue h-full rounded-full transition-all"
                          style={{ width: `${Math.max(pct, 2)}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-ink w-12 text-right">{pct}%</span>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* AC2: Top 5 opportunities of the week */}
          {stats && stats.top_oportunidades.length > 0 && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Top 5 oportunidades da semana
              </h2>
              <div className="space-y-3">
                {stats.top_oportunidades.map((item, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-[var(--border)] hover:bg-surface-1 transition-colors"
                  >
                    <p className="font-medium text-ink mb-1 line-clamp-2">{item.titulo}</p>
                    <div className="flex flex-wrap gap-3 text-sm text-ink-secondary">
                      <span>{item.orgao}</span>
                      {item.valor && <span className="font-medium text-ink">{formatBRL(item.valor)}</span>}
                      {item.data && <span>{item.data}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* AC4: CTA inline */}
          <BlogCTA
            variant="inline"
            setor={sector.name}
            uf={ufName}
            count={stats?.total_editais}
            slug={`${setor}-${uf}`}
          />

          {/* AC2: Regional editorial block (300+ words) */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              {sector.name} em {ufName}: panorama de licitações
            </h2>
            <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed">
              {editorial.map((paragraph, i) => (
                <p key={i}>{paragraph}</p>
              ))}
            </div>
          </section>

          {/* Zero-editais fallback: prefer historical contracts from pncp_supplier_contracts
              (genuine value for SEO visitors) and fall back to honest warning only if
              there is no contract history either. */}
          {hasZeroEditais && (
            contractsFallback && contractsFallback.total_contracts > 0 ? (
              <HistoricalContractsFallback
                scope="sector-uf"
                sectorName={sector.name}
                ufName={ufName}
                data={contractsFallback}
                ctaSlug={`${setor}-${uf}`}
              />
            ) : (
              <div className="mb-10 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800 font-medium mb-2">
                  Nenhuma licitação ativa neste período para {sector.name} em {ufName}.
                </p>
                <p className="text-sm text-yellow-700">
                  Também não identificamos contratos recentes deste setor neste estado. Confira UFs
                  vizinhas ou teste o SmartLic para receber alertas automáticos quando novas
                  oportunidades surgirem.
                </p>
              </div>
            )
          )}

          {/* A1: Modalidade-specific FAQ for unique content */}
          {modalidadeInfo && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                Perguntas sobre {modalidadeInfo.name}
              </h2>
              <div className="space-y-4">
                {[
                  {
                    q: `Como funciona o ${modalidadeInfo.name} para ${sector.name} em ${ufName}?`,
                    a: `${modalidadeInfo.typicalProcess}. Para o setor de ${sector.name} em ${ufName}, o SmartLic monitora automaticamente todos os editais publicados nesta modalidade no PNCP, PCP e ComprasGov.`,
                  },
                  {
                    q: `Quantos editais de ${modalidadeInfo.name} de ${sector.name} abrem por mês em ${ufName}?`,
                    a: `Nos últimos 30 dias, ${stats?.total_editais ?? 0} editais de ${sector.name} foram publicados em ${ufName}. A proporção de ${modalidadeInfo.name} varia conforme o período — consulte os dados ao vivo acima para o número atualizado.`,
                  },
                  {
                    q: `Qual a base legal do ${modalidadeInfo.name}?`,
                    a: `O ${modalidadeInfo.name} é regulamentado por ${modalidadeInfo.legalBasis}. ${modalidadeInfo.description}`,
                  },
                ].map((faq, i) => (
                  <details key={`mod-faq-${i}`} className="group border border-[var(--border)] rounded-lg">
                    <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-ink hover:bg-surface-1 rounded-lg transition-colors">
                      {faq.q}
                      <span className="text-ink-secondary group-open:rotate-180 transition-transform">&#x25BE;</span>
                    </summary>
                    <p className="px-4 pb-4 text-ink-secondary leading-relaxed">{faq.a}</p>
                  </details>
                ))}
              </div>
            </section>
          )}

          {/* AC2: FAQ section */}
          <section className="mb-10">
            <h2 className="text-xl font-semibold text-ink mb-4">
              Perguntas frequentes
            </h2>
            <div className="space-y-4">
              {faqs.map((faq, i) => (
                <details
                  key={i}
                  className="group border border-[var(--border)] rounded-lg"
                >
                  <summary className="flex items-center justify-between p-4 cursor-pointer font-medium text-ink hover:bg-surface-1 rounded-lg transition-colors">
                    {faq.question}
                    <span className="text-ink-secondary group-open:rotate-180 transition-transform">
                      &#x25BE;
                    </span>
                  </summary>
                  <p className="px-4 pb-4 text-ink-secondary leading-relaxed">
                    {faq.answer}
                  </p>
                </details>
              ))}
            </div>
          </section>

          {/* A1: Modalidade-specific educational content for unique indexable content */}
          {modalidadeInfo && (
            <section className="mb-10">
              <h2 className="text-xl font-semibold text-ink mb-4">
                {modalidadeInfo.name} para {sector.name} em {ufName}
              </h2>
              <div className="prose prose-slate max-w-none text-ink-secondary leading-relaxed space-y-4">
                <p>{modalidadeInfo.description}</p>
                <div className="not-prose p-4 rounded-lg bg-surface-1 border border-[var(--border)]">
                  <p className="text-sm font-medium text-ink mb-2">Base Legal</p>
                  <p className="text-sm text-ink-secondary">{modalidadeInfo.legalBasis}</p>
                </div>
                <div className="not-prose p-4 rounded-lg bg-surface-1 border border-[var(--border)]">
                  <p className="text-sm font-medium text-ink mb-2">Processo Típico</p>
                  <p className="text-sm text-ink-secondary">{modalidadeInfo.typicalProcess}</p>
                </div>
                {(() => {
                  const modStats = stats?.top_modalidades?.find(
                    (m) => m.name.toLowerCase().includes(modalidadeInfo.slug.split('-')[0])
                  );
                  const modPct = modStats && totalModCount > 0
                    ? Math.round((modStats.count / totalModCount) * 100)
                    : null;
                  return modPct !== null ? (
                    <p>
                      No setor de {sector.name} em {ufName}, a modalidade {modalidadeInfo.name} representa{' '}
                      <strong>{modPct}%</strong> dos editais publicados nos últimos 30 dias
                      {modStats ? ` (${modStats.count} de ${totalModCount} editais)` : ''}.
                    </p>
                  ) : null;
                })()}
              </div>
            </section>
          )}

          {/* AC4: Final CTA with button */}
          <BlogCTA
            variant="final"
            setor={sector.name}
            uf={ufName}
            count={stats?.total_editais}
            slug={`${setor}-${uf}`}
          />

          {/* AC7: Internal linking */}
          <RelatedPages
            sectorId={sector.id}
            currentUf={ufUpper}
            currentType="sector-uf"
          />

          {/* SEO Frente 4: Cidades relevantes em {UF} */}
          {(() => {
            const cidadesUf = getCitiesByUf(ufUpper);
            if (cidadesUf.length === 0) return null;
            return (
              <section className="mt-10">
                <h2 className="text-xl font-semibold text-ink mb-4">
                  Cidades relevantes em {ufName}
                </h2>
                <div className="flex flex-wrap gap-2">
                  {cidadesUf.map((c) => (
                    <Link
                      key={c.slug}
                      href={`/blog/licitacoes/cidade/${c.slug}/${setor}`}
                      className="inline-flex items-center px-3 py-1.5 rounded-full border border-[var(--border)] text-sm text-ink-secondary hover:bg-surface-1 hover:text-ink transition-colors"
                    >
                      {sector.name} em {c.name}
                    </Link>
                  ))}
                </div>
              </section>
            );
          })()}
        </div>
      </main>

      <Footer />
    </div>
  );
}
