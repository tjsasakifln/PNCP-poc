import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { buildCanonical, getFreshnessLabel } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';

// Sprint 3 Parte 13: paginas de perfil de fornecedor por CNPJ
// ISR 24h — dados do PNCP atualizados diariamente
export const revalidate = 86400;

// Limite de CNPJs pre-renderizados no build (resto e on-demand ISR)
const _MAX_STATIC_CNPJS = 1000;

type Props = { params: Promise<{ cnpj: string }> };

interface RecentContract {
  objeto: string;
  orgao: string;
  valor: number | null;
  data_assinatura: string;
  uf: string;
}

interface TopComprador {
  nome: string;
  cnpj: string;
  total_contratos: number;
  valor_total: number;
}

interface FaqItem {
  question: string;
  answer: string;
}

interface FornecedorProfile {
  cnpj: string;
  razao_social: string;
  cnae_descricao: string;
  municipio: string;
  uf_sede: string;
  simples_nacional: boolean;
  mei: boolean;
  total_contratos: number;
  valor_total: number;
  ufs_atuantes: string[];
  anos_atividade: number[];
  top_compradores: TopComprador[];
  contratos_recentes: RecentContract[];
  faq_items: FaqItem[];
  last_updated: string;
  aviso_legal: string;
}

async function fetchProfile(cnpj: string): Promise<FornecedorProfile | null> {
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/v1/fornecedores/${cnpj}/profile`, {
      next: { revalidate: 86400 },
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
    const res = await fetch(`${backendUrl}/v1/sitemap/fornecedores-cnpj`, {
      cache: 'no-store',
    });
    if (!res.ok) return [];
    const data = await res.json();
    const cnpjs: string[] = (data.cnpjs || []).slice(0, _MAX_STATIC_CNPJS);
    return cnpjs.map((cnpj) => ({ cnpj }));
  } catch {
    return [];
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { cnpj } = await params;
  const profile = await fetchProfile(cnpj);

  if (!profile) {
    return {
      title: `Fornecedor ${cnpj} — SmartLic`,
      robots: { index: false, follow: false },
    };
  }

  const valorFmt = profile.valor_total >= 1_000_000
    ? `R$ ${(profile.valor_total / 1_000_000).toFixed(1)} mi`
    : `R$ ${(profile.valor_total / 1_000).toFixed(0)} mil`;

  return {
    title: `${profile.razao_social} — Historico B2G | ${profile.total_contratos} contratos`,
    description: `Perfil completo de ${profile.razao_social} (CNPJ ${cnpj}): ${profile.total_contratos} contratos publicos, ${valorFmt} em contratos, atuando em ${profile.ufs_atuantes.length} estado(s). Dados PNCP.`,
    alternates: { canonical: buildCanonical(`/fornecedores/${cnpj}`) },
    openGraph: {
      title: `${profile.razao_social} — Contratos com o Governo`,
      description: `${profile.total_contratos} contratos | ${valorFmt} | PNCP`,
      type: 'website',
      locale: 'pt_BR',
    },
    robots: { index: true, follow: true },
  };
}

export default async function FornecedorCnpjPage({ params }: Props) {
  const { cnpj } = await params;

  // Validacao basica de formato antes de chamar o backend
  if (!/^\d{14}$/.test(cnpj)) notFound();

  const profile = await fetchProfile(cnpj);
  if (!profile) notFound();

  const breadcrumbs = [
    { name: 'SmartLic', url: '/' },
    { name: 'Fornecedores do Governo', url: '/fornecedores' },
    { name: profile.razao_social, url: `/fornecedores/${cnpj}` },
  ];

  const localizacao = [profile.municipio, profile.uf_sede].filter(Boolean).join(' — ') || 'Nao informado';

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      name: profile.razao_social,
      legalName: profile.razao_social,
      identifier: { '@type': 'PropertyValue', name: 'CNPJ', value: cnpj },
      ...(profile.municipio && profile.uf_sede
        ? {
            address: {
              '@type': 'PostalAddress',
              addressLocality: profile.municipio,
              addressRegion: profile.uf_sede,
              addressCountry: 'BR',
            },
          }
        : {}),
      url: `https://smartlic.tech/fornecedores/${cnpj}`,
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
            {profile.razao_social}
          </h1>
          <p className="text-sm text-gray-500 mb-1">
            CNPJ {cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')}
            {profile.cnae_descricao && <> &middot; {profile.cnae_descricao}</>}
          </p>
          <p className="text-sm text-gray-400 mb-6">
            {profile.last_updated ? getFreshnessLabel(profile.last_updated) : 'Dados do PNCP'}
            {' · Fonte: Portal Nacional de Contratacoes Publicas'}
          </p>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Total de Contratos</p>
              <p className="text-2xl font-bold text-gray-900">
                {profile.total_contratos.toLocaleString('pt-BR')}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Valor Total</p>
              <p className="text-2xl font-bold text-green-700">
                {formatBRL(profile.valor_total)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Estados Atuantes</p>
              <p className="text-2xl font-bold text-gray-900">
                {profile.ufs_atuantes.length}
              </p>
              <p className="text-xs text-gray-400 mt-1">
                {profile.ufs_atuantes.slice(0, 5).join(', ')}
                {profile.ufs_atuantes.length > 5 && '...'}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <p className="text-xs text-gray-500 mb-1">Sede</p>
              <p className="text-sm font-semibold text-gray-900">{localizacao}</p>
              <div className="flex gap-1 mt-1 flex-wrap">
                {profile.simples_nacional && (
                  <span className="text-xs bg-green-100 text-green-700 rounded px-1">Simples</span>
                )}
                {profile.mei && (
                  <span className="text-xs bg-blue-100 text-blue-700 rounded px-1">MEI</span>
                )}
              </div>
            </div>
          </div>

          {/* Contratos Recentes */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-3">
              Contratos Recentes
            </h2>
            <div className="bg-white rounded-lg shadow-sm border overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="text-left px-4 py-3">Objeto</th>
                    <th className="text-left px-4 py-3">Orgao Comprador</th>
                    <th className="text-right px-4 py-3">Valor</th>
                    <th className="text-right px-4 py-3">Data</th>
                    <th className="text-center px-4 py-3">UF</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {profile.contratos_recentes.map((c, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-2 max-w-xs">
                        <span className="line-clamp-2">{c.objeto}</span>
                      </td>
                      <td className="px-4 py-2 text-gray-600">{c.orgao}</td>
                      <td className="text-right px-4 py-2 text-green-700 whitespace-nowrap">
                        {c.valor != null ? formatBRL(c.valor) : '—'}
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

          {/* Top Compradores */}
          {profile.top_compradores.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">
                Principais Orgaos Compradores
              </h2>
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
                    {profile.top_compradores.map((o) => (
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

          {/* FAQ */}
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

          {/* Paginas Relacionadas */}
          <section className="border-t border-gray-200 pt-8 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Paginas Relacionadas</h2>
            <div className="flex flex-wrap gap-3 text-sm">
              <Link href={`/cnpj/${cnpj}`} className="text-blue-600 hover:underline">
                Licitacoes deste CNPJ
              </Link>
              <Link href="/fornecedores" className="text-blue-600 hover:underline">
                Todos os Fornecedores
              </Link>
              {profile.ufs_atuantes.slice(0, 3).map((uf) => (
                <Link
                  key={uf}
                  href={`/contratos/${uf.toLowerCase()}`}
                  className="text-blue-600 hover:underline"
                >
                  Contratos em {uf}
                </Link>
              ))}
            </div>
          </section>

          {/* Lead Capture */}
          <section className="mt-4 bg-blue-50 rounded-lg p-6 text-center">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Monitore editais do setor de {profile.razao_social}
            </h2>
            <p className="text-gray-600 mb-4">
              O SmartLic rastreia licitacoes abertas do PNCP e avisa quando surgem
              oportunidades relevantes para sua empresa.
            </p>
            <Link
              href="/signup"
              className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              Teste gratis por 14 dias
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
