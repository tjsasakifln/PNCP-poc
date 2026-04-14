import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { buildCanonical } from '@/lib/seo';
import { LeadCapture } from '@/components/LeadCapture';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

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
    const resp = await fetch(`${BACKEND_URL}/v1/contratos/orgao/${cnpj}/stats`, {
      cache: 'no-store', // bypass Next.js Data Cache — sempre fresh no ISR regen
      signal: AbortSignal.timeout(10000),
    });
    if (!resp.ok) return null;
    return resp.json();
  } catch {
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
    return { title: 'Orgao nao encontrado', robots: { index: false } };
  }

  const totalFormatado = formatBRL(stats.total_value);
  const year = new Date().getFullYear();

  return {
    title: `Contratos de ${stats.orgao_nome} ${year} — Fornecedores e Valores`,
    description: `${stats.orgao_nome} firmou ${stats.total_contracts} contratos totalizando ${totalFormatado}. Veja os principais fornecedores, valores e tendencias. Dados PNCP.`,
    alternates: { canonical: buildCanonical(`/contratos/orgao/${cnpj}`) },
    openGraph: {
      title: `Contratos de ${stats.orgao_nome}`,
      description: `${stats.total_contracts} contratos | ${totalFormatado} em valor total`,
      url: buildCanonical(`/contratos/orgao/${cnpj}`),
      type: 'website',
      locale: 'pt_BR',
      images: [{
        url: `/api/og?title=${encodeURIComponent(stats.orgao_nome + ' — Contratos Publicos')}`,
        width: 1200,
        height: 630,
      }],
    },
    twitter: {
      card: 'summary_large_image',
      title: `Contratos de ${stats.orgao_nome}`,
      description: `${stats.total_contracts} contratos | ${totalFormatado}`,
    },
  };
}

export default async function OrgaoContratosPage({ params }: Props) {
  const { cnpj } = await params;
  const stats = await fetchOrgaoContratosStats(cnpj);

  if (!stats) {
    notFound();
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
    name: `Contratos Publicos — ${stats.orgao_nome}`,
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
                          <Link href={`/cnpj/${f.cnpj}`} className="text-brand-blue hover:underline font-medium">
                            {f.nome}
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
                      <span>Fornecedor: {c.fornecedor}</span>
                      {c.valor && <span>Valor: {formatBRL(c.valor)}</span>}
                      <span>Data: {c.data_assinatura}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

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
                Dados Publicos
              </Link>
            </div>
          </section>

          {/* Aviso Legal */}
          <p className="text-xs text-ink-secondary italic">{stats.aviso_legal}</p>

          {/* Lead Capture */}
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
