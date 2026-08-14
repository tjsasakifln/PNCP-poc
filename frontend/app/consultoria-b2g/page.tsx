/**
 * REPO-009 #761 — /consultoria-b2g landing page
 *
 * Server Component. Handles metadata + JSON-LD FAQPage schema.
 * DiagnosticForm is wrapped in a thin 'use client' island so that
 * searchParams pre-fill works without making the whole page a client component.
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import Footer from '@/app/components/Footer';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import ConsultoriaForm from './ConsultoriaForm';

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: 'Consultoria B2G — Inteligência em Licitações | SmartLic',
  description:
    'A CONFENGE interpreta o dado público do SmartLic: go/no-go de licitação, carteira de empresa, risco de contrato e recorte local. Sem trial e sem plano de software.',
  alternates: {
    canonical: '/consultoria-b2g',
  },
};

// ---------------------------------------------------------------------------
// Structured data
// ---------------------------------------------------------------------------

const faqItems = [
  {
    question: 'Isso é SaaS ou serviço?',
    answer:
      'Consultoria especializada com infraestrutura proprietária de IA. Você contrata como parceiro estratégico, não como licença de software.',
  },
  {
    question: 'Qual é o prazo mínimo?',
    answer:
      'Sem compromisso de longo prazo na fase de validação. Trabalhamos mês a mês.',
  },
  {
    question: 'Vocês atendem qual setor?',
    answer:
      'Todos os setores com presença em licitações públicas. Nosso sistema cobre 27 UFs e 20+ setores.',
  },
  {
    question: 'Como funciona o onboarding?',
    answer:
      'Diagnóstico inicial gratuito, depois configuração em 48h.',
  },
  {
    question: 'Posso cancelar a qualquer momento?',
    answer: 'Sim. Sem multa e sem burocracia.',
  },
  {
    question: 'O que diferencia o SmartLic da CONFENGE?',
    answer:
      'O SmartLic publica o fato público. A CONFENGE interpreta, diagnostica e opera a decisão comercial.',
  },
];

const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: faqItems.map((item) => ({
    '@type': 'Question',
    name: item.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: item.answer,
    },
  })),
};

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const dores = [
  {
    icon: '⏱',
    text: 'Horas lendo PDF de edital sem saber se vale a pena',
  },
  {
    icon: '🎲',
    text: 'Decisão go/no-go sem dados de concorrência',
  },
  {
    icon: '👥',
    text: 'Cobertura insuficiente para time pequeno',
  },
  {
    icon: '⚡',
    text: 'Reatividade: descobrir oportunidades tarde demais',
  },
];

const pacotes = [
  {
    id: 'radar',
    nome: 'Radar Operacional',
    subtitulo: 'Alertas + Briefing',
    descricao:
      'Monitoramento diário das 27 UFs com briefing semanal. Cada edital relevante chega com triagem e pré-análise de viabilidade.',
    bullets: [
      'Alertas diários filtrados por setor e UF',
      'Briefing semanal com top-5 oportunidades',
      'Pré-análise de viabilidade em 4 fatores',
      'Dashboard de contratos dos concorrentes',
    ],
    cta: 'Quero o Radar',
    ctaHref: '#diagnostico',
    destaque: false,
  },
  {
    id: 'report',
    nome: 'Inteligência Estratégica',
    subtitulo: 'Relatórios + Análise',
    descricao:
      'Dossiê de concorrência, análise de histórico de preços e benchmarks por modalidade. Para decisões go/no-go baseadas em evidência.',
    bullets: [
      'Dossiê completo de concorrência (CNPJ)',
      'Histórico de preços e contratos por setor',
      'Análise de modalidade e timeline',
      'Parecer de viabilidade por edital',
    ],
    cta: 'Quero o relatório',
    ctaHref: '#diagnostico',
    destaque: true,
  },
  {
    id: 'intel',
    nome: 'Operação Premium',
    subtitulo: 'Consultoria',
    descricao:
      'Operamos o ciclo completo: radar + dossiê + suporte em impugnação + acompanhamento pós-abertura. Para empresas que tratam licitação como negócio.',
    bullets: [
      'Tudo do Inteligência Estratégica',
      'Suporte em impugnação e esclarecimentos',
      'Acompanhamento pós-abertura',
      'Reunião mensal de estratégia',
    ],
    cta: 'Falar com consultor',
    ctaHref: '#diagnostico',
    destaque: false,
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default async function ConsultoriaB2GPage({
  searchParams,
}: {
  searchParams: Promise<{ modalidade?: string }>;
}) {
  const params = await searchParams;
  const modalidadeParam = params?.modalidade as
    | 'radar'
    | 'report'
    | 'intel'
    | 'nao_sei'
    | undefined;

  // Validate that it's one of the accepted values
  const validModalidades = ['radar', 'report', 'intel', 'nao_sei'] as const;
  const defaultModalidade = validModalidades.includes(
    modalidadeParam as (typeof validModalidades)[number]
  )
    ? (modalidadeParam as (typeof validModalidades)[number])
    : undefined;

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />

      <LandingNavbar />

      <main className="bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        {/* ------------------------------------------------------------------ */}
        {/* Hero */}
        {/* ------------------------------------------------------------------ */}
        <section className="relative bg-gradient-to-br from-slate-900 to-blue-950 text-white py-20 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-blue-300 text-sm font-semibold uppercase tracking-widest mb-4">
              Consultoria B2G · SmartLic
            </p>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight mb-6">
              Um núcleo externo de inteligência B2G operando dentro da sua
              empresa.
            </h1>
            <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-10">
              Estratégia setorial, dossiê de concorrência, parecer de
              viabilidade e suporte em impugnação. Para empresas que tratam
              licitação como negócio, não como aposta.
            </p>
            <a
              href="#pacotes"
              className="inline-block bg-blue-500 hover:bg-blue-400 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
            >
              Ver pacotes →
            </a>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Problemas que resolvemos */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">
              Problemas que resolvemos
            </h2>
            <div className="grid sm:grid-cols-2 gap-6">
              {dores.map((dor, i) => (
                <div
                  key={i}
                  className="flex items-start gap-4 bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700"
                >
                  <span className="text-2xl flex-shrink-0" aria-hidden="true">
                    {dor.icon}
                  </span>
                  <p className="text-slate-700 dark:text-slate-300 font-medium">
                    {dor.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Pacotes */}
        {/* ------------------------------------------------------------------ */}
        <section id="pacotes" className="py-16 px-4">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
              Três formas de trabalharmos juntos
            </h2>
            <p className="text-slate-500 dark:text-slate-400 text-center mb-12">
              Sem mensalidade mínima na fase de validação. Comece pelo que faz
              sentido para o seu momento.
            </p>
            <div className="grid md:grid-cols-3 gap-6">
              {pacotes.map((p) => (
                <div
                  key={p.id}
                  className={`rounded-xl border p-6 flex flex-col ${
                    p.destaque
                      ? 'border-blue-500 ring-2 ring-blue-500 bg-blue-50 dark:bg-blue-950/30'
                      : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'
                  }`}
                >
                  {p.destaque && (
                    <span className="self-start mb-3 text-xs font-bold uppercase tracking-wider bg-blue-500 text-white px-2 py-1 rounded">
                      Mais popular
                    </span>
                  )}
                  <h3 className="text-xl font-bold mb-1">{p.nome}</h3>
                  <p className="text-blue-600 dark:text-blue-400 text-sm font-semibold mb-3">
                    {p.subtitulo}
                  </p>
                  <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
                    {p.descricao}
                  </p>
                  <ul className="space-y-2 mb-6 flex-1">
                    {p.bullets.map((b, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300"
                      >
                        <span
                          className="text-green-500 flex-shrink-0 mt-0.5"
                          aria-hidden="true"
                        >
                          ✓
                        </span>
                        {b}
                      </li>
                    ))}
                  </ul>
                  <a
                    href={p.ctaHref}
                    className={`block text-center font-semibold py-3 px-4 rounded-lg transition-colors ${
                      p.destaque
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-900 dark:text-slate-100'
                    }`}
                  >
                    {p.cta}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Tecnologia */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              Plataforma de busca + análise proprietária
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Toda inteligência que entregamos é produzida por um sistema
              próprio que agrega PNCP, ComprasGov e Portal de Compras Públicas
              em tempo real — com classificação por IA e análise de viabilidade
              em 4 fatores. O mesmo sistema está disponível para você operar
              diretamente via SaaS.
            </p>
            <Link
              href="/buscar"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              Explorar a plataforma →
            </Link>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* FAQ */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">
              Perguntas frequentes
            </h2>
            <dl className="space-y-6">
              {faqItems.map((item, i) => (
                <div
                  key={i}
                  className="border-b border-slate-200 dark:border-slate-700 pb-6 last:border-0"
                >
                  <dt className="font-semibold text-lg mb-2">
                    {item.question}
                  </dt>
                  <dd className="text-slate-600 dark:text-slate-400">
                    {item.answer}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Diagnóstico — DiagnosticForm */}
        {/* ------------------------------------------------------------------ */}
        <section id="diagnostico" className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-3">
              Diagnóstico gratuito
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-center mb-8">
              Preencha o formulário e retornaremos em até 48 horas com uma
              análise inicial do seu potencial B2G.
            </p>
            <ConsultoriaForm defaultModalidade={defaultModalidade} />
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
