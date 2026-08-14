/**
 * COPY-CONS-012 (#1010) — /consultorias landing page
 *
 * Server Component. Angle: white-label / B2B2G para consultorias e
 * assessorias de licitação. Frame: SmartLic = backbone tech; consultor =
 * relacionamento + expertise. Não dilui a landing principal `/`.
 *
 * Cross-link discreto para `/fundadores` no footer (audiências distintas;
 * não compartilha countdown/oferta Founders).
 */

import type { Metadata } from 'next';
import Link from 'next/link';
import Footer from '@/app/components/Footer';
import LandingNavbar from '@/app/components/landing/LandingNavbar';
import { CONSULTORIA_PRICING } from '@/lib/plan-pricing';

// ---------------------------------------------------------------------------
// Metadata (per-page canonical override; root canonical default em #1019)
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title:
    'SmartLic Consultoria — Inteligência B2G white-label para sua consultoria',
  description:
    'Atenda seus clientes B2G com inteligência sob seu logo. Plataforma white-label para assessorias e consultorias de licitação: 5 usuários, 5.000 análises/mês e relatórios com sua marca.',
  alternates: {
    canonical: '/consultorias',
  },
  openGraph: {
    type: 'website',
    url: 'https://smartlic.tech/consultorias',
    title: 'SmartLic Consultoria — White-label B2G para assessorias',
    description:
      'Backbone tech para consultorias de licitação. Você mantém o relacionamento; nós entregamos a inteligência. R$ 997/mês com até 5 usuários.',
    siteName: 'SmartLic',
    locale: 'pt_BR',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SmartLic Consultoria — White-label B2G',
    description:
      'Backbone tech para consultorias de licitação. Relatórios com seu logo, dashboard consolidado, até 5 usuários.',
  },
};

// ---------------------------------------------------------------------------
// Structured data — Schema.org Service (B2B2G white-label SaaS)
// ---------------------------------------------------------------------------

const serviceSchema = {
  '@context': 'https://schema.org',
  '@type': 'Service',
  serviceType: 'White-label B2G intelligence platform for consultancies',
  provider: {
    '@type': 'Organization',
    name: 'SmartLic',
    url: 'https://smartlic.tech',
  },
  name: 'SmartLic Consultoria',
  description:
    'Plataforma white-label de inteligência em licitações públicas para consultorias e assessorias B2G. Inclui até 5 usuários, 5.000 análises/mês, dashboard consolidado e relatórios com logo da consultoria.',
  areaServed: { '@type': 'Country', name: 'Brasil' },
  audience: {
    '@type': 'BusinessAudience',
    audienceType: 'Consultorias e assessorias de licitação pública',
  },
  offers: {
    '@type': 'Offer',
    price: CONSULTORIA_PRICING.monthly.monthly,
    priceCurrency: 'BRL',
    availability: 'https://schema.org/InStock',
    url: 'https://smartlic.tech/consultorias',
    eligibleQuantity: {
      '@type': 'QuantitativeValue',
      maxValue: 5,
      unitText: 'usuários',
    },
  },
};

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const valueProps = [
  {
    icon: '🏷️',
    title: 'Sua marca, nossa engine',
    text: 'Relatórios em Excel e PDF saem com o logo da sua consultoria. Cliente final vê seu trabalho — não o nosso.',
  },
  {
    icon: '👥',
    title: 'Até 5 usuários',
    text: 'Sócios, analistas e estagiários compartilham o mesmo workspace, com permissões por papel.',
  },
  {
    icon: '📊',
    title: 'Dashboard consolidado',
    text: 'Visão única de todos os clientes que você atende. Pipelines, alertas e métricas em um só lugar.',
  },
  {
    icon: '⚡',
    title: '5.000 análises/mês',
    text: 'Margem larga para atender vários clientes B2G simultaneamente, sem se preocupar com cota.',
  },
  {
    icon: '🎯',
    title: 'Inteligência setorial 20+ setores',
    text: 'GPT-4.1-nano classifica relevância. Você foca no parecer; nós cuidamos da triagem.',
  },
  {
    icon: '🛟',
    title: 'Suporte prioritário',
    text: 'Atendimento dedicado em horário comercial. Onboarding guiado para sócios e equipe.',
  },
];

const casosUso = [
  {
    titulo: 'Assessor solo',
    descricao:
      'Você atende 8-15 clientes recorrentes. SmartLic monitora todos os 27 estados em paralelo e devolve briefing semanal por cliente — você entrega o parecer estratégico.',
  },
  {
    titulo: 'Escritório de advocacia em licitações',
    descricao:
      'Equipe de 3-5 advogados, mandatos de impugnação e habilitação. Dashboard consolidado mostra editais críticos por cliente; relatórios saem com o timbre do escritório.',
  },
  {
    titulo: 'Consultoria de M&A B2G',
    descricao:
      'Due diligence em alvos com receita pública. Histórico de contratos e concorrência por CNPJ alimenta seu modelo de valuation; relatórios de market share white-label.',
  },
];

const features = [
  'Logo da consultoria nos relatórios (Excel + PDF)',
  'Até 5 usuários no mesmo workspace',
  'Dashboard consolidado multi-cliente',
  '5.000 análises de licitação por mês',
  'Pipeline kanban por cliente',
  'Alertas configuráveis por setor e UF',
  'Histórico completo de buscas e sessões',
  'Suporte prioritário em horário comercial',
];

const faq = [
  {
    pergunta: 'Posso usar para vários clientes ao mesmo tempo?',
    resposta:
      'Sim — esse é o ponto. Você opera o SmartLic Consultoria como agência: organiza pipelines por cliente, configura alertas por mandato e entrega relatórios com seu logo para cada um deles.',
  },
  {
    pergunta: 'O cliente final vê que estou usando o SmartLic?',
    resposta:
      'Não nos relatórios exportados. Excel e PDF saem com o logo da sua consultoria. Você é o ponto de contato; nós somos a infraestrutura nos bastidores.',
  },
  {
    pergunta: 'Tem desconto anual?',
    resposta:
      'Sim. Mensal: R$ 997. Semestral: R$ 897/mês (-10%). Anual: R$ 797/mês (-20%). Cobrança em uma única fatura no início do ciclo.',
  },
  {
    pergunta: 'Como agendo uma conversa antes de assinar?',
    resposta:
      'Use o CTA "Agendar conversa". Vamos entender o seu mix de clientes e mostrar como o dashboard consolidado se encaixa no seu fluxo. Sem pressão de fechamento.',
  },
  {
    pergunta: 'E se eu precisar de mais de 5 usuários?',
    resposta:
      'Fale com a gente. Para times maiores, fazemos plano sob medida — escritórios com 8-15 analistas já operam dessa forma.',
  },
];

const monthlyPrice = CONSULTORIA_PRICING.monthly.monthly;
const annualMonthly = CONSULTORIA_PRICING.annual.monthly;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function ConsultoriasPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(serviceSchema) }}
      />

      <LandingNavbar />

      <main className="bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100">
        {/* ------------------------------------------------------------------ */}
        {/* Hero */}
        {/* ------------------------------------------------------------------ */}
        <section className="relative bg-gradient-to-br from-slate-900 to-indigo-950 text-white py-20 px-4">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-indigo-300 text-sm font-semibold uppercase tracking-widest mb-4">
              SmartLic Consultoria · White-label B2G
            </p>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight mb-6">
              Atenda seus clientes B2G com inteligência sob seu logo.
            </h1>
            <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-4">
              SmartLic é o backbone tech. Você é o relacionamento e a
              expertise. Sua consultoria entrega o parecer; nossa engine
              entrega a triagem, a viabilidade e o dossiê — com a sua marca.
            </p>
            <p className="text-base text-slate-400 max-w-2xl mx-auto mb-10">
              Até 5 usuários · 5.000 análises/mês · relatórios com o logo da
              sua consultoria.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="https://web.whatsapp.com/send?phone=5548988344559&text=Quero%20conversar%20sobre%20o%20SmartLic%20Consultoria"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-indigo-500 hover:bg-indigo-400 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
              >
                Agendar conversa →
              </a>
              <Link
                href="/consultoria-b2g?plan=consultoria"
                className="inline-block bg-white hover:bg-slate-100 text-slate-900 font-semibold px-8 py-4 rounded-lg transition-colors"
              >
                Testar 14 dias grátis →
              </Link>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Frame: backbone tech vs relacionamento */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
              Quem entrega o quê
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-center mb-12 max-w-2xl mx-auto">
              Sua consultoria não compete com SaaS — usa SaaS para escalar.
              SmartLic é a engine; você é a interface humana com o cliente.
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-slate-800 rounded-xl p-8 border border-slate-200 dark:border-slate-700">
                <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 mb-3">
                  SmartLic entrega
                </p>
                <h3 className="text-xl font-bold mb-4">Backbone tecnológico</h3>
                <ul className="space-y-2 text-slate-700 dark:text-slate-300">
                  <li>• Busca multi-fonte (PNCP + ComprasGov + PCP)</li>
                  <li>• Classificação de relevância por IA (GPT-4.1-nano)</li>
                  <li>• Análise de viabilidade em 4 fatores</li>
                  <li>• Pipeline kanban por cliente</li>
                  <li>• Histórico e dashboard consolidado</li>
                </ul>
              </div>
              <div className="bg-white dark:bg-slate-800 rounded-xl p-8 border border-slate-200 dark:border-slate-700">
                <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-3">
                  Sua consultoria entrega
                </p>
                <h3 className="text-xl font-bold mb-4">
                  Relacionamento + expertise
                </h3>
                <ul className="space-y-2 text-slate-700 dark:text-slate-300">
                  <li>• Parecer go/no-go com leitura de contexto</li>
                  <li>• Estratégia de impugnação e habilitação</li>
                  <li>• Negociação e relacionamento com cliente final</li>
                  <li>• Conhecimento setorial e jurisprudencial</li>
                  <li>• Relatórios com a sua marca</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Value props grid */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">
              O que vem com o SmartLic Consultoria
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {valueProps.map((vp, i) => (
                <div
                  key={i}
                  className="bg-white dark:bg-slate-800 rounded-xl p-6 border border-slate-200 dark:border-slate-700"
                >
                  <span
                    className="text-3xl block mb-3"
                    aria-hidden="true"
                  >
                    {vp.icon}
                  </span>
                  <h3 className="font-bold text-lg mb-2">{vp.title}</h3>
                  <p className="text-slate-600 dark:text-slate-400 text-sm">
                    {vp.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Casos de uso */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
              Para quem é
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-center mb-12 max-w-2xl mx-auto">
              Três perfis que já operam SmartLic Consultoria como
              infraestrutura padrão.
            </p>
            <div className="space-y-4">
              {casosUso.map((caso, i) => (
                <div
                  key={i}
                  className="bg-white dark:bg-slate-800 rounded-xl p-6 border-l-4 border-indigo-500"
                >
                  <h3 className="font-bold text-lg mb-2">{caso.titulo}</h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    {caso.descricao}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Pricing */}
        {/* ------------------------------------------------------------------ */}
        <section id="pricing" className="py-16 px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">
              SmartLic Consultoria
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-center mb-10">
              Pricing transparente. Sem letra miúda. Cancela quando quiser.
            </p>
            <div className="bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/30 dark:to-slate-800 rounded-2xl p-8 border-2 border-indigo-500 shadow-lg">
              <div className="text-center mb-6">
                <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 mb-2">
                  Plano único — cap 5 usuários
                </p>
                <p className="text-5xl font-bold mb-1">
                  R$ {monthlyPrice}
                  <span className="text-lg font-normal text-slate-500 dark:text-slate-400">
                    /mês
                  </span>
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  ou R$ {annualMonthly}/mês no anual (-20%)
                </p>
              </div>
              <ul className="space-y-3 mb-8">
                {features.map((f, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-3 text-slate-700 dark:text-slate-300"
                  >
                    <span
                      className="text-emerald-500 flex-shrink-0 mt-0.5 font-bold"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="flex flex-col sm:flex-row gap-3">
                <a
                  href="https://web.whatsapp.com/send?phone=5548988344559&text=Quero%20conversar%20sobre%20o%20SmartLic%20Consultoria"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-center bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors"
                >
                  Agendar conversa
                </a>
                <Link
                  href="/consultoria-b2g?plan=consultoria"
                  className="flex-1 text-center bg-white hover:bg-slate-100 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-900 dark:text-slate-100 font-semibold py-4 px-6 rounded-lg border border-slate-300 dark:border-slate-600 transition-colors"
                >
                  Testar 14 dias grátis
                </Link>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 text-center mt-4">
                Trial sem cartão · cancela com 1 clique · suporte humano em
                horário comercial
              </p>
            </div>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* FAQ */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4 bg-slate-50 dark:bg-slate-900">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl sm:text-3xl font-bold text-center mb-12">
              Perguntas frequentes
            </h2>
            <dl className="space-y-6">
              {faq.map((item, i) => (
                <div
                  key={i}
                  className="border-b border-slate-200 dark:border-slate-700 pb-6 last:border-0"
                >
                  <dt className="font-semibold text-lg mb-2">
                    {item.pergunta}
                  </dt>
                  <dd className="text-slate-600 dark:text-slate-400">
                    {item.resposta}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* ------------------------------------------------------------------ */}
        {/* Final CTA + cross-link discreto p/ /fundadores */}
        {/* ------------------------------------------------------------------ */}
        <section className="py-16 px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl font-bold mb-4">
              Pronto para escalar sua consultoria?
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-xl mx-auto">
              Em uma conversa de 30 minutos mostramos como o dashboard
              consolidado se encaixa no seu mix atual de clientes.
            </p>
            <a
              href="https://web.whatsapp.com/send?phone=5548988344559&text=Quero%20conversar%20sobre%20o%20SmartLic%20Consultoria"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
            >
              Agendar conversa →
            </a>
            <p className="mt-10 text-sm text-slate-500 dark:text-slate-400">
              É empresa B2G e não consultoria? Veja o{' '}
              <Link
                href="/fundadores"
                className="underline hover:text-indigo-600 dark:hover:text-indigo-400"
              >
                programa Fundadores
              </Link>
              .
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
