import { Metadata } from 'next';
import Link from 'next/link';
import ContentPageLayout from '../../components/ContentPageLayout';
import CnpjPerfilClient from './CnpjPerfilClient';
import EmptyStateSEO from '@/components/seo/EmptyStateSEO';
import InlineTrialCTA from '../../components/InlineTrialCTA';
import IntelReportCTA from './IntelReportCTA';
import { LeadCapture } from '@/components/LeadCapture';
import { FoundersRibbon } from '@/components/banners/FoundersRibbon';
import WhatsAppCTA from '@/app/components/whatsapp/WhatsAppCTA';
import { fetchWithBudget } from '@/lib/safe-fetch';
import { getBackendUrl } from '@/lib/backend-url';
import {
  buildOperationalTitle,
  buildOperationalDescription,
} from '@/lib/seo';
import { buildOrgSchema } from './_jsonld';
import { isNoindexed } from '@/lib/seo/noindex';
import { OpportunitySignalsPanel } from '@/app/components/OpportunitySignalsPanel';

const BACKEND_URL = getBackendUrl();

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

export const revalidate = 3600; // 24h ISR

export function generateStaticParams() {
  return []; // SSR on-demand
}

async function fetchPerfil(cnpj: string): Promise<PerfilB2G | null> {
  return fetchWithBudget<PerfilB2G>(`${BACKEND_URL}/v1/empresa/${cnpj}/perfil-b2g`, {
    timeout: 15000,
    retries: 1,
    revalidate: 3600,
    throwOn5xx: true, // ISR stale-preservation: 5xx re-throws to keep last-good cache
    label: 'cnpj-perfil',
  });
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

  // CONV-006b: operational promise title/description
  const title = buildOperationalTitle('cnpj', {
    cnpj,
    subject: empresa.razao_social,
    count: total_contratos_24m,
    value: valorFormatado,
  });
  const description = buildOperationalDescription('cnpj', {
    cnpj,
    subject: empresa.razao_social,
    count: total_contratos_24m,
    value: valorFormatado,
  });

  return {
    title,
    description,
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
    // SEO-P0-003 (#989): also gate on uniqueness audit. Pages flagged as
    // duplicate by `scripts/seo/uniqueness_audit.py` ship `index: false`
    // even when they have data, to avoid HCU drag.
    robots: {
      index: total_contratos_24m > 0 && !isNoindexed('cnpj', `/cnpj/${cnpj}`),
      follow: true,
    },
  };
}

export default async function CnpjPerfilPage({
  params,
}: {
  params: Promise<{ cnpj: string }>;
}) {
  const { cnpj } = await params;
  const perfil = await fetchPerfil(cnpj);

  // ADR-SEO-001: data absence → EmptyStateSEO (not notFound) to prevent ISR-cached 404s
  if (!perfil) {
    return (
      <EmptyStateSEO
        title="CNPJ sem contratos registrados ainda"
        description="Este CNPJ não possui contratos públicos registrados nas fontes oficiais no momento. Os dados são indexados diariamente — volte em breve."
        ctaHref="/cnpj"
        ctaLabel="Consultar outro CNPJ"
      />
    );
  }

  const { empresa } = perfil;

  // #996 SEO-P2-009: Organization JSON-LD enriched with SmartLic-exclusive data
  // (contract history, sector classification, areas served) for entity profile SERP.
  const orgSchema = buildOrgSchema(perfil);

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

  // SEO-P1-007 (#993): Visual breadcrumb derived from same trail as JSON-LD.
  // ContentPageLayout's BreadcrumbNav emits the BreadcrumbList JSON-LD when
  // breadcrumbItems is provided (suppressSchema=false), so we no longer need
  // an inline breadcrumbSchema script — single source of truth.
  // CONV-002 (#1311): Build signal data from existing perfil data
  const cnpjSignals: Array<{ icon: string; label: string; value: string; description: string }> = [];
  const valorTotalCnpj = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0 }).format(perfil.valor_total_24m);
  const orgaosUnicos = new Set(perfil.contratos.map((c) => c.orgao)).size;

  if (perfil.total_contratos_24m > 0) {
    cnpjSignals.push({
      icon: '💰',
      label: 'Total Contratado com Governo',
      value: valorTotalCnpj,
      description: `${perfil.total_contratos_24m} contratos nos últimos 24 meses`,
    });
  }
  if (orgaosUnicos > 0) {
    cnpjSignals.push({
      icon: '🏛️',
      label: 'Órgãos Contratantes',
      value: `${orgaosUnicos} órgãos`,
      description: 'Entidades que contrataram esta empresa no período',
    });
  }
  if ((perfil.ufs_atuacao ?? []).length > 0) {
    cnpjSignals.push({
      icon: '📍',
      label: 'Regiões de Atuação',
      value: `${perfil.ufs_atuacao.length} ${perfil.ufs_atuacao.length === 1 ? 'estado' : 'estados'}`,
      description: perfil.ufs_atuacao.join(', '),
    });
  }
  if (perfil.editais_abertos_setor > 0) {
    cnpjSignals.push({
      icon: '🎯',
      label: 'Editais Abertos no Setor',
      value: `${perfil.editais_abertos_setor} ${perfil.editais_abertos_setor === 1 ? 'edital' : 'editais'}`,
      description: `Oportunidades em ${perfil.setor_nome || 'setor detectado'}`,
    });
  }
  if (perfil.contratos.length > 0) {
    cnpjSignals.push({
      icon: '📊',
      label: 'Score B2G',
      value: perfil.score || 'N/I',
      description: 'Indicador de maturidade em contratações públicas',
    });
  }

  const breadcrumbItems = [
    { label: 'Início', href: '/' },
    { label: 'Consulta CNPJ', href: '/cnpj' },
    { label: empresa.razao_social },
  ];

  return (
    <ContentPageLayout
      breadcrumbLabel={empresa.razao_social}
      breadcrumbItems={breadcrumbItems}
      relatedPages={[
        { href: `/fornecedores/${cnpj}`, title: `${empresa.razao_social} — Histórico de Fornecedor` },
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

      <CnpjPerfilClient perfil={perfil} />

      {/* CONV-002 (#1311): OpportunitySignalsPanel — investigação competitiva */}
      {cnpjSignals.length > 0 && (
        <div className="mt-8">
          <OpportunitySignalsPanel
            sourceTemplate="cnpj_page"
            entityId={cnpj}
            setor={perfil.setor_detectado}
            uf={empresa.uf}
            heading={`Inteligência competitiva de ${empresa.razao_social}`}
            subheading="Padrão de contratações públicas e oportunidades do setor"
            signals={cnpjSignals}
            compact
            cta={{
              label: 'Analisar padrão de vitórias',
              href: `/consultoria-b2g?ref=cnpj-${cnpj}&utm_source=pseo&utm_medium=organic&utm_content=cnpj_page`,
              secondaryLabel: 'Mapear possíveis contratantes',
              secondaryHref: `/fornecedores/${cnpj}`,
            }}
          />
        </div>
      )}

      {/* PSEO-TMPL-001 (#882): Link bidirecional para /fornecedores/{cnpj} quando empresa tem contratos */}
      {perfil.total_contratos_24m > 0 && (
        <section className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50 p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="flex-1">
            <p className="text-sm font-semibold text-indigo-900 mb-0.5">
              {empresa.razao_social} como fornecedor público
            </p>
            <p className="text-xs text-indigo-700">
              Veja o perfil completo de fornecedor com histórico de contratos, órgãos compradores e setores de atuação.
            </p>
          </div>
          <Link
            href={`/fornecedores/${cnpj}`}
            className="shrink-0 inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            Ver perfil de fornecedor →
          </Link>
        </section>
      )}

      {/* #632: Intel Report one-time purchase CTA */}
      <section className="mt-8 rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50 to-indigo-50 p-6">
        <h2 className="mb-2 text-xl font-bold text-gray-900">
          Inteligência Competitiva
        </h2>
        <p className="mb-1 font-semibold text-gray-600">
          Raio-X Completo do Concorrente
        </p>
        <p className="mb-4 text-sm text-gray-500">
          8–12 páginas: histórico de contratos, órgãos compradores, evolução temporal, análise IA
        </p>
        <div className="mb-4 text-2xl font-bold text-gray-900">
          R$197{" "}
          <span className="text-sm font-normal text-gray-500">— download imediato</span>
        </div>
        <IntelReportCTA cnpj={cnpj} />
        <p className="mt-3 text-xs text-gray-400">
          ✓ PDF imediato &nbsp; ✓ 30 dias de acesso &nbsp; ✓ Dados oficiais atualizados
        </p>
      </section>

      {/* #652: Inline trial CTA after contratos section */}
      <InlineTrialCTA
        page="cnpj"
        source="cnpj-page"
        extraParam={{ name: 'orgao', value: cnpj }}
      />

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

      {/* REPO-015: Consultoria-b2g CTA with CNPJ pre-fill */}
      <section className="mt-12 rounded-xl border border-blue-200 bg-blue-50 dark:bg-blue-950/30 dark:border-blue-800 p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">
          Quer análise profissional de licitações?
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Diagnóstico gratuito. Sem compromisso.
        </p>
        <Link
          href={`/consultoria-b2g?modalidade=intel&cnpj=${cnpj}`}
          className="inline-block rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
          data-cta-source="pseo-cnpj"
        >
          Mapear meu setor
        </Link>
      </section>

      {/* CONV-013: WhatsApp CTA — falar com founder */}
      <div className="mt-8">
        <WhatsAppCTA
          source="cnpj_page"
          entity={empresa.razao_social}
          entityId={cnpj}
          setor={perfil.setor_detectado}
          uf={empresa.uf}
        />
      </div>

      {/* #788: Founders plan CTA for high-intent organic visitors */}
      <FoundersRibbon
        variant="contextual"
        copy="Acesso vitalício durante a fase inicial do SmartLic — vagas limitadas."
        src="pseo_cnpj"
      />
    </ContentPageLayout>
  );
}
