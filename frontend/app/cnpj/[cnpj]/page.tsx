import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ContentPageLayout from '../../components/ContentPageLayout';
import CnpjPerfilClient from './CnpjPerfilClient';
import { LeadCapture } from '@/components/LeadCapture';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

interface EditaisAmostra {
  orgao: string;
  descricao: string;
  valor_estimado: number | null;
  data_encerramento: string | null;
  uf: string | null;
  modalidade: string | null;
}

interface PerfilB2G {
  empresa: {
    razao_social: string;
    cnpj: string;
    cnae_principal: string;
    porte: string;
    uf: string;
    situacao: string;
  };
  contratos: Array<{
    orgao: string;
    orgao_cnpj?: string | null;
    valor: number | null;
    data_inicio: string | null;
    descricao: string;
    esfera?: string | null;
    uf?: string | null;
  }>;
  score: string;
  setor_detectado: string;
  setor_nome: string;
  editais_abertos_setor: number;
  editais_amostra: EditaisAmostra[];
  total_contratos_24m: number;
  valor_total_24m: number;
  ufs_atuacao: string[];
  aviso_legal: string;
}

export const revalidate = 86400; // 24h ISR

export function generateStaticParams() {
  return []; // SSR on-demand
}

async function fetchPerfil(cnpj: string): Promise<PerfilB2G | null> {
  try {
    const resp = await fetch(`${BACKEND_URL}/v1/empresa/${cnpj}/perfil-b2g`, {
      next: { revalidate: 86400 },
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
  params: Promise<{ cnpj: string }>;
}): Promise<Metadata> {
  const { cnpj } = await params;
  const perfil = await fetchPerfil(cnpj);

  if (!perfil) {
    return {
      title: 'CNPJ não encontrado',
      description: 'O CNPJ informado não foi encontrado na base de dados.',
    };
  }

  const { empresa, total_contratos_24m, valor_total_24m, score } = perfil;
  const valorFormatado = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0,
  }).format(valor_total_24m);

  return {
    title: `${empresa.razao_social} — Histórico de Contratos Públicos`,
    description: `${empresa.razao_social} tem ${total_contratos_24m} contratos com o governo nos últimos 24 meses. Total: ${valorFormatado}. Score B2G: ${score}.`,
    alternates: {
      canonical: `https://smartlic.tech/cnpj/${cnpj}`,
    },
    openGraph: {
      title: `${empresa.razao_social} — Contratos Públicos`,
      description: `${total_contratos_24m} contratos | ${valorFormatado} | Score: ${score}`,
      url: `https://smartlic.tech/cnpj/${cnpj}`,
      type: 'website',
      images: [
        {
          url: `/api/og?title=${encodeURIComponent(empresa.razao_social + ' — B2G Score: ' + score)}`,
          width: 1200,
          height: 630,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${empresa.razao_social} — Score B2G: ${score}`,
      description: `${total_contratos_24m} contratos | ${valorFormatado}`,
    },
    robots: { index: total_contratos_24m > 0, follow: true },
  };
}

export default async function CnpjPerfilPage({
  params,
}: {
  params: Promise<{ cnpj: string }>;
}) {
  const { cnpj } = await params;
  const perfil = await fetchPerfil(cnpj);

  if (!perfil) {
    notFound();
  }

  const { empresa } = perfil;

  const orgSchema = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: empresa.razao_social,
    taxID: empresa.cnpj,
    address: {
      '@type': 'PostalAddress',
      addressRegion: empresa.uf,
      addressCountry: 'BR',
    },
  };

  const datasetSchema = {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: `Contratos Públicos — ${empresa.razao_social}`,
    description: `Histórico de contratos governamentais de ${empresa.razao_social} (CNPJ ${empresa.cnpj})`,
    creator: { '@type': 'Organization', name: 'SmartLic', url: 'https://smartlic.tech' },
    license: 'https://dados.gov.br/dados/conteudo/sobre-dados-abertos',
    distribution: {
      '@type': 'DataDownload',
      contentUrl: `https://smartlic.tech/cnpj/${cnpj}`,
      encodingFormat: 'text/html',
    },
  };

  const breadcrumbSchema = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Início', item: 'https://smartlic.tech' },
      { '@type': 'ListItem', position: 2, name: 'Consulta CNPJ', item: 'https://smartlic.tech/cnpj' },
      { '@type': 'ListItem', position: 3, name: empresa.razao_social, item: `https://smartlic.tech/cnpj/${cnpj}` },
    ],
  };

  return (
    <ContentPageLayout
      breadcrumbLabel={empresa.razao_social}
      relatedPages={[
        { href: '/cnpj', title: 'Nova consulta CNPJ' },
        { href: '/orgaos', title: 'Órgãos Compradores' },
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

      <CnpjPerfilClient perfil={perfil} />

      {/* A2: Contextual lead capture with detected sector + UF */}
      <div className="mt-10">
        <LeadCapture
          source="cnpj-perfil"
          setor={perfil.setor_detectado}
          uf={perfil.empresa.uf}
          heading="Receba alertas semanais do seu setor por email"
          description={`Novos editais de ${perfil.setor_nome} em ${perfil.empresa.uf}, toda semana no seu email.`}
        />
      </div>
    </ContentPageLayout>
  );
}
