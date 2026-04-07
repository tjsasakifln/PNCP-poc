import { Metadata } from 'next';
import { buildCanonical, SITE_URL } from '@/lib/seo';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import Footer from '@/app/components/Footer';
import DemoClient from './DemoClient';

export const revalidate = 86400; // 24h ISR

export const metadata: Metadata = {
  title: 'Demo Interativo — Veja o SmartLic em Ação | SmartLic',
  description:
    'Experimente o SmartLic sem criar conta. Demo guiado de 2 minutos: busca multi-fonte, classificação por setor, e análise de viabilidade com 4 fatores. Dados reais do PNCP.',
  alternates: { canonical: buildCanonical('/demo') },
  openGraph: {
    title: 'Demo Interativo — Veja o SmartLic em Ação',
    description:
      'Demo guiado de 2 minutos: busca, classificação e análise de viabilidade com dados reais do PNCP.',
    type: 'website',
    url: buildCanonical('/demo'),
    locale: 'pt_BR',
  },
  robots: { index: true, follow: true },
};

export default function DemoPage() {
  const canonicalUrl = buildCanonical('/demo');

  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'HowTo',
        name: 'Como usar o SmartLic para encontrar licitações públicas',
        description:
          'Aprenda a usar o SmartLic em 4 passos: selecione seu setor, inicie a busca multi-fonte, analise os resultados com score de viabilidade e explore a análise detalhada com 4 fatores.',
        url: canonicalUrl,
        totalTime: 'PT2M',
        step: [
          {
            '@type': 'HowToStep',
            position: 1,
            name: 'Selecionar setor',
            text: 'Escolha o setor de atuação da sua empresa entre 15 opções pré-configuradas com keywords e critérios específicos.',
            url: `${canonicalUrl}#setor`,
          },
          {
            '@type': 'HowToStep',
            position: 2,
            name: 'Buscar editais',
            text: 'Clique em buscar para acionar a pesquisa simultânea no PNCP, Portal de Compras Públicas e ComprasGov.',
            url: `${canonicalUrl}#busca`,
          },
          {
            '@type': 'HowToStep',
            position: 3,
            name: 'Analisar resultados',
            text: 'Veja os editais classificados por score de viabilidade (0–100) calculado com 4 fatores: modalidade, prazo, valor e geografia.',
            url: `${canonicalUrl}#resultados`,
          },
          {
            '@type': 'HowToStep',
            position: 4,
            name: 'Ver viabilidade detalhada',
            text: 'Expanda qualquer edital para ver a análise fator a fator com justificativa em linguagem natural e porcentagem de peso.',
            url: `${canonicalUrl}#analise`,
          },
        ],
      },
      {
        '@type': 'WebApplication',
        name: 'SmartLic',
        url: SITE_URL,
        applicationCategory: 'BusinessApplication',
        operatingSystem: 'Web',
        description:
          'Plataforma de inteligência em licitações públicas com IA para classificação setorial e análise de viabilidade de editais do PNCP e fontes governamentais.',
        offers: {
          '@type': 'Offer',
          price: '0',
          priceCurrency: 'BRL',
          description: 'Teste grátis por 14 dias, sem cartão de crédito',
        },
        provider: {
          '@type': 'Organization',
          name: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
          url: SITE_URL,
        },
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          {
            '@type': 'ListItem',
            position: 1,
            name: 'Início',
            item: SITE_URL,
          },
          {
            '@type': 'ListItem',
            position: 2,
            name: 'Ferramentas',
            item: `${SITE_URL}/features`,
          },
          {
            '@type': 'ListItem',
            position: 3,
            name: 'Demo Interativo',
            item: canonicalUrl,
          },
        ],
      },
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="min-h-screen bg-[var(--canvas)]">
        <LandingNavbar />

        {/* Hero section */}
        <section className="bg-gradient-to-br from-brand-navy to-brand-blue text-white py-14 px-4">
          <div className="max-w-4xl mx-auto text-center">
            {/* Breadcrumb */}
            <nav className="text-sm text-white/60 mb-6" aria-label="Breadcrumb">
              <a href="/" className="hover:text-white/80">Início</a>
              <span className="mx-2">›</span>
              <a href="/features" className="hover:text-white/80">Ferramentas</a>
              <span className="mx-2">›</span>
              <span className="text-white/80">Demo Interativo</span>
            </nav>

            <div className="inline-flex items-center gap-2 bg-white/10 text-white/90 text-sm px-4 py-1.5 rounded-full mb-5 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
              Demo ao vivo — sem cadastro necessário
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 leading-tight">
              Veja o SmartLic em Ação<br className="hidden sm:block" />
              <span className="text-blue-200"> — Sem Criar Conta</span>
            </h1>

            <p className="text-lg sm:text-xl text-white/80 max-w-2xl mx-auto mb-6">
              Tour guiado de 2 minutos: busca multi-fonte, classificação por setor com IA
              e análise de viabilidade com 4 fatores. Dados simulados do setor de Engenharia em SP.
            </p>

            <div className="flex flex-wrap justify-center gap-4 text-sm text-white/70">
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Busca PNCP + Portal de Compras + ComprasGov
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Score de viabilidade com IA
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Análise 4 fatores detalhada
              </span>
            </div>
          </div>
        </section>

        {/* Demo content */}
        <main className="py-10 px-4">
          <DemoClient />
        </main>

        <Footer />
      </div>
    </>
  );
}
