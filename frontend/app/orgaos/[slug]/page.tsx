import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ContentPageLayout from '../../components/ContentPageLayout';
import OrgaoPerfilClient from './OrgaoPerfilClient';
import { LeadCapture } from '@/components/LeadCapture';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

interface LicitacaoRecente {
  objeto_compra: string;
  modalidade_nome: string;
  valor_total_estimado: number | null;
  data_publicacao: string;
  uf: string;
}

interface ModalidadeCount {
  nome: string;
  count: number;
}

interface OrgaoStats {
  nome: string;
  cnpj: string;
  esfera: string;
  uf: string;
  municipio: string;
  total_licitacoes: number;
  licitacoes_30d: number;
  licitacoes_90d: number;
  licitacoes_365d: number;
  valor_medio_estimado: number;
  valor_total_estimado: number;
  top_modalidades: ModalidadeCount[];
  top_setores: string[];
  ultimas_licitacoes: LicitacaoRecente[];
  total_contratos_24m?: number;
  valor_total_contratos_24m?: number;
  aviso_legal: string;
}

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return []; // SSR on-demand
}

async function fetchOrgaoStats(slug: string): Promise<OrgaoStats | null> {
  try {
    const resp = await fetch(`${BACKEND_URL}/v1/orgao/${slug}/stats`, {
      next: { revalidate: 86400 },
      signal: AbortSignal.timeout(10000),
    });
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const stats = await fetchOrgaoStats(slug);

  if (!stats) {
    return {
      title: 'Órgão não encontrado',
      description: 'O órgão informado não foi encontrado na base de dados.',
      robots: { index: false, follow: false },
    };
  }

  // STORY-439 AC1: noindex órgãos com volume insuficiente de licitações (thin content gate)
  const minBids = parseInt(process.env.MIN_ACTIVE_BIDS_FOR_INDEX ?? '5', 10);
  if (stats.total_licitacoes < minBids) {
    return {
      title: `${stats.nome} — Licitações Públicas`,
      robots: { index: false, follow: true },
    };
  }

  const valorMedioFormatado = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(stats.valor_medio_estimado);

  const contratosDesc = stats.total_contratos_24m
    ? ` ${stats.total_contratos_24m} contratos firmados (24 meses).`
    : '';

  return {
    title: `${stats.nome} — Licitações, Editais e Contratos`,
    description: `${stats.nome} publicou ${stats.total_licitacoes} licitações. ${stats.licitacoes_30d} nos últimos 30 dias. Valor médio: ${valorMedioFormatado}.${contratosDesc}`,
    alternates: {
      canonical: `https://smartlic.tech/orgaos/${slug}`,
    },
    openGraph: {
      title: `${stats.nome} — Licitações e Editais`,
      description: `${stats.total_licitacoes} licitações publicadas | ${stats.licitacoes_30d} nos últimos 30 dias`,
      url: `https://smartlic.tech/orgaos/${slug}`,
      type: 'website',
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(stats.nome + ' — Licitações Públicas')}`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${stats.nome} — Licitações Públicas`,
      description: `${stats.total_licitacoes} licitações | ${stats.licitacoes_30d} nos últimos 30 dias`,
    },
  };
}

export default async function OrgaoPerfilPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const stats = await fetchOrgaoStats(slug);

  if (!stats) {
    notFound();
  }

  const orgSchema = {
    '@context': 'https://schema.org',
    '@type': 'GovernmentOrganization',
    name: stats.nome,
    taxID: stats.cnpj,
    address: {
      '@type': 'PostalAddress',
      addressRegion: stats.uf,
      addressLocality: stats.municipio,
      addressCountry: 'BR',
    },
  };

  const datasetSchema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `Licitações Públicas — ${stats.nome}`,
    description: `Histórico de licitações e editais publicados por ${stats.nome} (CNPJ ${stats.cnpj})`,
    creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
    license: 'https://dados.gov.br/dados/conteudo/sobre-dados-abertos',
    distribution: {
      '@type': 'DataDownload',
      contentUrl: `https://smartlic.tech/orgaos/${slug}`,
      encodingFormat: 'text/html',
    },
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Início', item: 'https://smartlic.tech' },
      { '@type': 'ListItem', position: 2, name: 'Órgãos Compradores', item: 'https://smartlic.tech/orgaos' },
      { '@type': 'ListItem', position: 3, name: stats.nome, item: `https://smartlic.tech/orgaos/${slug}` },
    ],
  };

  return (
    <ContentPageLayout
      breadcrumbLabel={stats.nome}
      relatedPages={[
        { href: '/orgaos', title: 'Órgãos Compradores' },
        { href: '/cnpj', title: 'Consulta CNPJ' },
        { href: '/calculadora', title: 'Calculadora de Oportunidades' },
        { href: '/licitacoes', title: 'Licitações por Setor' },
      ]}
    >
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(orgSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(datasetSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }}
      />

      <OrgaoPerfilClient stats={stats} />

      <div className="mt-10">
        <LeadCapture
          source="orgao-perfil"
          uf={stats.uf}
          heading="Receba alertas de editais deste órgão"
          description={`Novos editais de ${stats.nome}, toda semana no seu email.`}
        />
      </div>
    </ContentPageLayout>
  );
}
