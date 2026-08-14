import { Metadata } from 'next';
import Link from 'next/link';
import EmptyStateSEO from '@/components/seo/EmptyStateSEO';
import { buildCanonical } from '@/lib/seo';
import { ssgLimitedFetch } from '@/lib/concurrency';
import { LeadCapture } from '@/components/LeadCapture';
import TrackingLink from '@/components/TrackingLink';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import { isNoindexed } from '@/lib/seo/noindex';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

interface FornecedorRank {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

interface MonthlyTrend {
  month: string;
  count: number;
  value: number;
}

interface SampleContract {
  objeto: string;
  orgao: string;
  fornecedor: string;
  valor: number | null;
  data_assinatura: string;
}

interface OrgaoContratosStats {
  orgao_nome: string;
  orgao_cnpj: string;
  total_contracts: number;
  total_value: number;
  avg_value: number;
  top_fornecedores: FornecedorRank[];
  monthly_trend: MonthlyTrend[];
  sample_contracts: SampleContract[];
  last_updated: string;
  aviso_legal: string;
}

export const revalidate = 14400; // 4h ISR (reduzido de 24h para melhorar freshness)

export function generateStaticParams() {
  return []; // SSR on-demand
}

async function fetchOrgaoContratosStats(cnpj: string): Promise<OrgaoContratosStats | null> {
  try {
    const resp = await ssgLimitedFetch(`${BACKEND_URL}/v1/contratos/orgao/${cnpj}/stats`, {
      next: { revalidate: 14400 }, // ISR-aligned com revalidate da page (4h) — mantém SSG/ISR estático e evita static→dynamic shift
      signal: AbortSignal.timeout(10000),
    });
    if (resp.status >= 500) {
      // Transient backend error — throw so ISR preserves last-good cache.
      throw new Error(`contratos_orgao_stats_backend_5xx:${resp.status}`);
    }
    // 4xx (incl. 404) → genuine "no data" — render EmptyStateSEO.
    if (!resp.ok) return null;
    return await resp.json();
  } catch (err) {
    if (err instanceof Error && err.message.startsWith('contratos_orgao_stats_backend_5xx')) throw err;
    return null;
  }
}

function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(value);
}

type Props = { params: Promise<{ cnpj: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { cnpj } = await params;
  const stats = await fetchOrgaoContratosStats(cnpj);

  if (!stats) {
    return { title: 'Orgao nao encontrado', robots: { index: false }, alternates: { canonical: buildCanonical(`/contratos/orgao/${cnpj}`) } };
  }

  const totalFormatado = formatBRL(stats.total_value);
  const year = new Date().getFullYear();

  return {
    title: `Contratos de ${stats.orgao_nome} ${year} — Fornecedores e Valores`,
    description: `${stats.orgao_nome} firmou ${stats.total_contracts} contratos totalizando ${totalFormatado}. Veja os principais fornecedores, valores e tendencias. Dados das fontes oficiais.`,
    alternates: { canonical: buildCanonical(`/contratos/orgao/${cnpj}`) },
    openGraph: {
      title: `Contratos de ${stats.orgao_nome}`,
      description: `${stats.total_contracts} contratos | ${totalFormatado} em valor total`,
      url: buildCanonical(`/contratos/orgao/${cnpj}`),
      type: 'website',
      locale: 'pt_BR',
      images: [{
        url: `/api/og?title=${encodeURIComponent(stats.orgao_nome + ' — Contratos Públicos')}`,
        width: 1200,
        height: 630,
      }],
    },
    twitter: {
      card: 'summary_large_image',
      title: `Contratos de ${stats.orgao_nome}`,
      description: `${stats.total_contracts} contratos | ${totalFormatado}`,
    },
    // SEO-P0-003 (#989): gate on uniqueness audit (see lib/seo/noindex.ts).
    robots: {
      index: !isNoindexed('contratos-orgao', `/contratos/orgao/${cnpj}`),
      follow: true,
    },
  };
}

export default async function OrgaoContratosPage({ params }: Props) {
  const { cnpj } = await params;
  const stats = await fetchOrgaoContratosStats(cnpj);

  // ADR-SEO-001: data absence → EmptyStateSEO (not notFound) to prevent ISR-cached 404s
  if (!stats) {
    return (
      <EmptyStateSEO
        title="Órgão sem contratos registrados ainda"
        description="Este órgão não possui contratos públicos registrados nas fontes oficiais no momento. Os dados são indexados diariamente — volte em breve."
        ctaHref="/contratos"
        ctaLabel="Ver contratos por setor"
      />
    );
  }

  const orgSchema = {
    '@context': 'https://schema.org',
    '@type': 'GovernmentOrganization',
    name: stats.orgao_nome,
    taxID: stats.orgao_cnpj,
    address: { '@type': 'PostalAddress', addressCountry: 'BR' },
  };

  const datasetSchema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `Contratos Públicos — ${stats.orgao_nome}`,
    description: `Historico de contratos firmados por ${stats.orgao_nome} (CNPJ ${stats.orgao_cnpj})`,
    creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
    license: 'https://dados.gov.br/dados/conteudo/sobre-dados-abertos',
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Inicio', item: 'https://smartlic.tech' },
      { '@type': 'ListItem', position: 2, name: 'Contratos', item: 'https://smartlic.tech/contratos' },
      { '@type': 'ListItem', position: 3, name: stats.orgao_nome, item: buildCanonical(`/contratos/orgao/${cnpj}`) },
    ],
  };

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <LandingNavbar />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(orgSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-surface-1 border-b border-[var(--border)]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
            <nav className="flex items-center gap-2 text-sm text-ink-secondary mb-6 flex-wrap">
              <Link href="/" className="hover:text-brand-blue transition-colors">Home</Link>
              <span>/</span>
              <Link href="/contratos" className="hover:text-brand-blue transition-colors">Contratos</Link>
              <span>/</span>
              <span className="text-ink truncate max-w-[300px]">{stats.orgao_nome}</span>
            </nav>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-ink tracking-tight mb-3">
              Contratos de {stats.orgao_nome}
            </h1>
            <p className="text-sm text-ink-secondary">
              CNPJ: {stats.orgao_cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')}
              {' · '}Atualizado em {new Date(stats.last_updated).toLocaleDateString('pt-BR')}
            </p>

            <section aria-labelledby="hero-cta-heading" className="mt-6 bg-blue-50 rounded-lg p-6 text-center">
              <h2 id="hero-cta-heading" className="text-lg font-bold text-gray-900 mb-1">
                Quer monitorar {stats.orgao_nome} e descobrir oportunidades antes da concorrência?
              </h2>
              <p className="text-sm text-gray-600 mb-4">O SmartLic rastreia novos editais e contratos automaticamente.</p>
              <TrackingLink
                href={`/consultoria-b2g?utm_source=programmatic&utm_medium=cta&utm_campaign=conv-cta-001&utm_content=contratos-orgao&page_cnpj=${cnpj}`}
                eventName="cta_clicked"
                eventProps={{ cta_name: 'contratos_orgao_hero', destination: '/consultoria-b2g', page_type: 'contratos_orgao', page_cnpj: cnpj, orgao_nome: stats.orgao_nome }}
                data-testid="pseo-cta-primary"
                className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors min-h-[44px]"
              >
                Pedir um diagnóstico à CONFENGE
              </TrackingLink>
              <p className="mt-2 text-xs text-gray-500">Sem login · dado público verificável</p>
            </section>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5 text-center">
              <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Total de Contratos</p>
              <p className="text-3xl font-bold text-ink">{stats.total_contracts.toLocaleString('pt-BR')}</p>
            </div>
            <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5 text-center">
              <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Valor Total</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats.total_value)}</p>
            </div>
            <div className="bg-surface-1 border border-[var(--border)] rounded-xl p-5 text-center">
              <p className="text-xs text-ink-secondary uppercase tracking-wider mb-1">Valor Medio</p>
              <p className="text-2xl font-bold text-ink">{formatBRL(stats.avg_value)}</p>
            </div>
          </div>

          {/* Top Fornecedores */}
          {stats.top_fornecedores.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-ink mb-4">Principais Fornecedores</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-ink-secondary">
                      <th className="text-left py-2 pr-4 font-medium">#</th>
                      <th className="text-left py-2 pr-4 font-medium">Fornecedor</th>
                      <th className="text-right py-2 px-4 font-medium">Contratos</th>
                      <th className="text-right py-2 pl-4 font-medium">Valor Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.top_fornecedores.map((f, i) => (
                      <tr key={f.cnpj} className="border-b border-[var(--border)] hover:bg-surface-1 transition-colors">
                        <td className="py-3 pr-4 text-ink-secondary">{i + 1}</td>
                        <td className="py-3 pr-4">
                          <Link href={`/fornecedores/${f.cnpj}`} className="text-brand-blue hover:underline font-medium">
                            {f.nome}
                          </Link>
                          <Link href={`/cnpj/${f.cnpj}`} className="block text-xs text-ink-secondary hover:underline mt-0.5">
                            Consulta CNPJ →
                          </Link>
                        </td>
                        <td className="py-3 px-4 text-right font-mono">{f.total_contratos}</td>
                        <td className="py-3 pl-4 text-right font-mono">{formatBRL(f.valor_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Monthly Trend */}
          {stats.monthly_trend.some(t => t.count > 0) && (
            <section>
              <h2 className="text-lg font-semibold text-ink mb-4">Tendencia Mensal (12 meses)</h2>
              <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3">
                {stats.monthly_trend.filter(t => t.count > 0).map((t) => (
                  <div key={t.month} className="p-3 rounded-lg border border-[var(--border)] text-center">
                    <p className="text-xs text-ink-secondary">{t.month}</p>
                    <p className="text-lg font-semibold text-ink">{t.count}</p>
                    <p className="text-xs text-ink-secondary">{formatBRL(t.value)}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Sample Contracts */}
          {stats.sample_contracts.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-ink mb-4">Contratos Recentes</h2>
              <div className="space-y-3">
                {stats.sample_contracts.map((c, i) => (
                  <div key={i} className="p-4 rounded-lg border border-[var(--border)]">
                    <p className="text-sm font-medium text-ink mb-1">{c.objeto}</p>
                    <div className="flex flex-wrap gap-3 text-xs text-ink-secondary">
                      <span>
                        Fornecedor:{' '}
                        {c.fornecedor && c.fornecedor !== 'Nao informado' ? (
                          <span className="text-ink">{c.fornecedor}</span>
                        ) : (
                          c.fornecedor
                        )}
                      </span>
                      {c.valor && <span>Valor: {formatBRL(c.valor)}</span>}
                      <span>Data: {c.data_assinatura}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Oportunidades Semelhantes — CTA para buscar editais do mesmo órgão */}
          <section className="rounded-xl border border-green-200 bg-green-50 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Encontrar Oportunidades Semelhantes
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              O SmartLic monitora automaticamente novos editais publicados por{' '}
              <strong>{stats.orgao_nome}</strong> e por órgãos com perfil de compra semelhante.
              Receba alertas antes da concorrência.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <TrackingLink
                href={`/consultoria-b2g?utm_source=programmatic&utm_medium=cta&utm_campaign=conv-cta-001&utm_content=contratos-orgao-similar&page_cnpj=${cnpj}`}
                eventName="cta_clicked"
                eventProps={{ cta_name: 'contratos_orgao_similar', destination: '/consultoria-b2g', page_type: 'contratos_orgao', page_cnpj: cnpj, orgao_nome: stats.orgao_nome }}
                className="inline-block px-5 py-2.5 bg-green-600 text-white text-sm font-semibold rounded-lg hover:bg-green-700 transition-colors text-center"
              >
                Monitorar editais deste órgão →
              </TrackingLink>
              <Link
                href={`/orgaos/${cnpj}`}
                className="inline-block px-5 py-2.5 bg-white border border-green-300 text-green-700 text-sm font-semibold rounded-lg hover:bg-green-50 transition-colors text-center"
              >
                Ver perfil completo do órgão
              </Link>
            </div>
          </section>

          {/* Internal Links */}
          <section>
            <h2 className="text-lg font-semibold text-ink mb-4">Veja tambem</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Link href="/contratos" className="p-3 rounded-lg border border-[var(--border)] text-sm text-brand-blue hover:bg-surface-1 transition-colors text-center">
                Contratos por Setor
              </Link>
              <Link href={`/orgaos/${cnpj}`} className="p-3 rounded-lg border border-[var(--border)] text-sm text-brand-blue hover:bg-surface-1 transition-colors text-center">
                Perfil do Orgao
              </Link>
              <Link href="/fornecedores" className="p-3 rounded-lg border border-[var(--border)] text-sm text-brand-blue hover:bg-surface-1 transition-colors text-center">
                Fornecedores
              </Link>
              <Link href="/dados" className="p-3 rounded-lg border border-[var(--border)] text-sm text-brand-blue hover:bg-surface-1 transition-colors text-center">
                Dados Públicos
              </Link>
            </div>
          </section>

          {/* Aviso Legal */}
          <p className="text-xs text-ink-secondary italic">{stats.aviso_legal}</p>

          {/* Footer CTA */}
          <section aria-labelledby="footer-cta-heading" className="bg-blue-50 rounded-lg p-6 text-center">
            <h2 id="footer-cta-heading" className="text-xl font-bold text-gray-900 mb-2">
              Monitore editais e contratos de {stats.orgao_nome}
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia licitações abertas nas fontes oficiais e avisa quando surgem oportunidades relevantes.
            </p>
            <TrackingLink
              href={`/consultoria-b2g?utm_source=programmatic&utm_medium=cta&utm_campaign=conv-cta-001&utm_content=contratos-orgao-footer&page_cnpj=${cnpj}`}
              eventName="cta_clicked"
              eventProps={{ cta_name: 'contratos_orgao_footer', destination: '/consultoria-b2g', page_type: 'contratos_orgao', page_cnpj: cnpj, orgao_nome: stats.orgao_nome }}
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Pedir um diagnóstico à CONFENGE
            </TrackingLink>
            <p className="mt-2 text-xs text-gray-500">Sem login · dado público verificável</p>
          </section>

          <LeadCapture
            source="contratos-orgao"
            heading="Monitore contratos deste orgao"
            description={`Receba alertas quando ${stats.orgao_nome} firmar novos contratos.`}
          />
        </div>
      </main>

      <Footer />
    </div>
  );
}
