import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 5 Parte 13: due diligence B2G por CNPJ (CEIS + CNEP)
// On-demand ISR — sem generateStaticParams, gerado na primeira visita, cacheado 24h
export const revalidate = 86400;

type Props = { params: Promise<{ cnpj: string }> };

interface SancaoEntry {
  tipo: 'CEIS' | 'CNEP';
  orgao_sancionador: string;
  data_inicio: string;
  data_fim: string;
  motivo: string;
  valor_multa: number | null;
}

interface ComplianceProfile {
  cnpj: string;
  razao_social: string;
  situacao_geral: 'Sem registros' | 'Sancoes ativas' | 'Sancoes encerradas';
  total_sancoes_ceis: number;
  total_sancoes_cnep: number;
  sancoes: SancaoEntry[];
  fonte_dados: string;
  last_updated: string;
  aviso_legal: string;
}

async function fetchProfile(cnpj: string): Promise<ComplianceProfile | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/compliance/${cnpj}/profile`, {
      next: { revalidate: 86400 },
    });
    if (res.status === 404 || res.status === 400) return null;
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { cnpj } = await params;

  if (!/^\d{14}$/.test(cnpj)) {
    return {
      title: `Due Diligence CNPJ ${cnpj} — SmartLic`,
      robots: { index: false, follow: false },
    };
  }

  const profile = await fetchProfile(cnpj);

  if (!profile) {
    return {
      title: `Due Diligence B2G: CNPJ ${cnpj} | SmartLic`,
      robots: { index: false, follow: false },
    };
  }

  const cnpjFmt = cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');
  const situacaoDesc =
    profile.situacao_geral === 'Sem registros'
      ? 'sem sanções no CEIS ou CNEP'
      : profile.situacao_geral === 'Sancoes ativas'
      ? `com sanções ativas (CEIS: ${profile.total_sancoes_ceis}, CNEP: ${profile.total_sancoes_cnep})`
      : `com sanções encerradas (CEIS: ${profile.total_sancoes_ceis}, CNEP: ${profile.total_sancoes_cnep})`;

  return {
    title: `Due Diligence B2G: ${profile.razao_social} | CEIS, CNEP, TCU | SmartLic`,
    description:
      `Consulta de sanções e impedimentos de ${profile.razao_social} (CNPJ ${cnpjFmt}): ` +
      `${situacaoDesc}. Dados do Portal da Transparência (CEIS e CNEP).`,
    alternates: { canonical: buildCanonical(`/compliance/${cnpj}`) },
    openGraph: {
      title: `Due Diligence B2G: ${profile.razao_social}`,
      description: `CEIS e CNEP — ${profile.situacao_geral}`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: true, follow: true },
  };
}

export default async function ComplianceCnpjPage({ params }: Props) {
  const { cnpj } = await params;

  if (!/^\d{14}$/.test(cnpj)) notFound();

  const profile = await fetchProfile(cnpj);
  if (!profile) notFound();

  const cnpjFmt = cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5');

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Due Diligence B2G', url: '/compliance' },
    { name: profile.razao_social, url: `/compliance/${cnpj}` },
  ];

  const situacaoLabel = {
    'Sem registros': 'Sem sanções ativas',
    'Sancoes ativas': 'Sanções ativas',
    'Sancoes encerradas': 'Sanções encerradas',
  }[profile.situacao_geral] ?? profile.situacao_geral;

  const situacaoColor = {
    'Sem registros': 'bg-green-100 text-green-800',
    'Sancoes ativas': 'bg-red-100 text-red-800',
    'Sancoes encerradas': 'bg-yellow-100 text-yellow-800',
  }[profile.situacao_geral] ?? 'bg-gray-100 text-gray-800';

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Report',
      name: `Due Diligence B2G: ${profile.razao_social}`,
      author: {
        '@type': 'Organization',
        name: 'SmartLic',
        url: 'https://smartlic.tech',
      },
      about: {
        '@type': 'Organization',
        name: profile.razao_social,
        legalName: profile.razao_social,
        identifier: { '@type': 'PropertyValue', name: 'CNPJ', value: cnpj },
      },
      datePublished: profile.last_updated,
      url: `https://smartlic.tech/compliance/${cnpj}`,
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
                <span className="text-gray-900 font-medium truncate max-w-xs inline-block align-bottom">
                  {b.name}
                </span>
              )}
            </span>
          ))}
        </nav>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Cabeçalho */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-1">
                Due Diligence B2G
              </h1>
              <p className="text-lg text-gray-700 font-medium">{profile.razao_social}</p>
              <p className="text-sm text-gray-500">CNPJ {cnpjFmt}</p>
              <p className="text-xs text-gray-400 mt-1">
                {profile.last_updated ? getFreshnessLabel(profile.last_updated) : 'Dados do Portal da Transparência'}
                {' · '}CEIS e CNEP
              </p>
            </div>
            <span className={`self-start inline-block px-4 py-2 rounded-full text-sm font-semibold ${situacaoColor}`}>
              {situacaoLabel}
            </span>
          </div>

          {/* Resumo de KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Registros CEIS</p>
              <p className={`text-2xl font-bold ${profile.total_sancoes_ceis > 0 ? 'text-red-700' : 'text-green-700'}`}>
                {profile.total_sancoes_ceis}
              </p>
              <p className="text-xs text-gray-400 mt-1">Cadastro de Empresas Inidôneas</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Registros CNEP</p>
              <p className={`text-2xl font-bold ${profile.total_sancoes_cnep > 0 ? 'text-red-700' : 'text-green-700'}`}>
                {profile.total_sancoes_cnep}
              </p>
              <p className="text-xs text-gray-400 mt-1">Cadastro Nacional de Penalidades</p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4 col-span-2 sm:col-span-1">
              <p className="text-xs text-gray-500 mb-1">Situação Geral</p>
              <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${situacaoColor}`}>
                {situacaoLabel}
              </span>
              <p className="text-xs text-gray-400 mt-2">Baseado em CEIS + CNEP</p>
            </div>
          </div>

          {/* Detalhamento de sanções */}
          {profile.sancoes.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                Registros de Sanções e Penalidades
              </h2>
              <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600">
                    <tr>
                      <th className="text-left px-4 py-3">Base</th>
                      <th className="text-left px-4 py-3">Órgão Sancionador</th>
                      <th className="text-left px-4 py-3">Início</th>
                      <th className="text-left px-4 py-3">Fim</th>
                      <th className="text-left px-4 py-3">Fundamento</th>
                      <th className="text-right px-4 py-3">Multa</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {profile.sancoes.map((s, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                            s.tipo === 'CEIS' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {s.tipo}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-gray-700 max-w-xs">
                          <span className="line-clamp-2">{s.orgao_sancionador}</span>
                        </td>
                        <td className="px-4 py-2 text-gray-600 whitespace-nowrap">
                          {formatDate(s.data_inicio)}
                        </td>
                        <td className="px-4 py-2 text-gray-600 whitespace-nowrap">
                          {s.data_fim ? formatDate(s.data_fim) : 'Vigente'}
                        </td>
                        <td className="px-4 py-2 text-gray-600 max-w-xs">
                          <span className="line-clamp-2">{s.motivo}</span>
                        </td>
                        <td className="text-right px-4 py-2 text-red-700 whitespace-nowrap">
                          {s.valor_multa != null ? formatBRL(s.valor_multa) : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {profile.sancoes.length === 0 && (
            <section className="mb-8">
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                <p className="text-green-800 font-semibold text-lg">
                  Nenhum registro encontrado no CEIS ou CNEP
                </p>
                <p className="text-green-700 text-sm mt-1">
                  {profile.razao_social} não apresenta sanções ou penalidades registradas nos
                  cadastros consultados do Portal da Transparência.
                </p>
              </div>
            </section>
          )}

          {/* Links relacionados */}
          <section className="border-t border-gray-200 pt-8 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Páginas Relacionadas</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              <Link href={`/fornecedores/${cnpj}`} className="text-blue-600 hover:underline">
                Perfil de Fornecedor — {profile.razao_social}
              </Link>
              <Link href="/compliance" className="text-blue-600 hover:underline">
                Due Diligence B2G
              </Link>
              <Link href="/fornecedores" className="text-blue-600 hover:underline">
                Diretório de Fornecedores
              </Link>
            </div>
          </section>

          {/* CTA */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore licitações com fornecedores qualificados
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic verifica a situação de fornecedores nos principais cadastros
              governamentais e filtra as oportunidades mais seguras para sua empresa.
            </p>
            <Link
              href="/signup"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teste grátis por 14 dias
            </Link>
          </section>

          {/* Aviso legal */}
          <div className="mt-8 bg-gray-100 rounded-lg p-4">
            <p className="text-xs text-gray-500 leading-relaxed">{profile.aviso_legal}</p>
          </div>
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

function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  const parts = dateStr.slice(0, 10).split('-');
  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`;
  return dateStr;
}
