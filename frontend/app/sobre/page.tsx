/**
 * GTM-COPY-005: Credibilidade & Autoridade Explícita
 * STORY-273 AC4: Enhanced /sobre page with team, mission, contact
 *
 * AC1: Página Sobre/Metodologia acessível via header
 * AC2: Seção Quem Somos (CONFENGE)
 * AC3: Seção Metodologia (critérios de avaliação)
 * AC4: Seção Fontes de Dados (fontes oficiais)
 * AC4-273: Team, Mission/Vision, Contact
 *
 * Static page — no auth required, SEO optimized.
 */

import Link from 'next/link';
import Footer from '../components/Footer';
import LandingNavbar from '../components/landing/LandingNavbar';

// GTM-COPY-006 pattern: Per-page metadata for SEO
export const metadata = {
  title: 'Metodologia e Critérios de Avaliação',
  description: 'Conheça a metodologia SmartLic: critérios objetivos, fontes oficiais do PNCP e IA aplicada à avaliação de licitações públicas.',
  alternates: {
    canonical: 'https://smartlic.tech/sobre',
  },
};

// Organization structured data for E-E-A-T
const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'CONFENGE Avaliações e Inteligência Artificial LTDA',
  url: 'https://smartlic.tech',
  description: 'Plataforma de inteligência em licitações públicas que transforma decisões de intuitivas para objetivas.',
  foundingDate: '2024',
  contactPoint: {
    '@type': 'ContactPoint',
    url: 'https://smartlic.tech/ajuda#contato',
    contactType: 'customer service',
    availableLanguage: 'Portuguese',
  },
  sameAs: ['https://smartlic.tech'],
};

const criterios = [
  {
    title: 'Compatibilidade setorial',
    what: 'Cruza o objeto do edital com regras específicas do setor selecionado, incluindo palavras-chave, exclusões e classificação por inteligência artificial.',
    why: 'Garante que você veja apenas licitações onde sua empresa realmente pode competir.',
    how: 'Oportunidades com alta compatibilidade aparecem primeiro. Editais incompatíveis são descartados automaticamente.',
  },
  {
    title: 'Faixa de valor adequada',
    what: 'Verifica se o valor estimado da licitação é compatível com o porte e capacidade típica do seu setor.',
    why: 'Evita que você perca tempo com licitações fora do seu alcance financeiro ou operacional.',
    how: 'Cada setor tem uma faixa de valor configurada. Licitações fora da faixa recebem avaliação de viabilidade menor.',
  },
  {
    title: 'Prazo para preparação',
    what: 'Avalia quanto tempo resta entre a publicação e a data de abertura do edital.',
    why: 'Preparar uma proposta competitiva exige tempo. Prazos muito curtos aumentam o risco de propostas incompletas.',
    how: 'Licitações com prazo adequado para preparação recebem avaliação mais alta.',
  },
  {
    title: 'Região de atuação',
    what: 'Filtra oportunidades pelos estados (UFs) onde sua empresa opera ou tem capacidade de atender.',
    why: 'Logística e presença local impactam diretamente a competitividade e o custo de execução.',
    how: 'Você seleciona os estados de interesse e o sistema retorna apenas oportunidades dessas regiões.',
  },
  {
    title: 'Modalidade favorável',
    what: 'Identifica a modalidade licitatória (pregão, concorrência, etc.) e avalia a competitividade para o seu perfil.',
    why: 'Diferentes modalidades têm regras distintas que favorecem diferentes portes de empresa.',
    how: 'Modalidades mais acessíveis ao seu perfil recebem pontuação de viabilidade mais alta.',
  },
];

export default function SobrePage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
      />

      <LandingNavbar />

      <main id="main-content" className="min-h-screen bg-[var(--canvas)]">
        {/* Hero */}
        <section className="bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white py-16 sm:py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold font-display mb-4">
              Sobre o SmartLic
            </h1>
            <p className="text-lg sm:text-xl text-white/90 max-w-2xl">
              Inteligência aplicada a licitações. Critérios objetivos, fontes oficiais, decisões melhores.
            </p>
          </div>
        </section>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 space-y-16">

          {/* AC2 — Quem Somos */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-brand-blue-subtle rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Quem somos
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 space-y-4">
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                O SmartLic é desenvolvido pela <strong className="text-[var(--ink)]">CONFENGE Avaliações e Inteligência Artificial LTDA</strong>, empresa com experiência em avaliações técnicas e aplicação de inteligência artificial ao mercado B2G (Business-to-Government).
              </p>
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                Nosso propósito é <strong className="text-[var(--ink)]">transformar decisões em licitações de intuitivas para objetivas</strong>. Acreditamos que empresas que competem em licitações merecem ferramentas que substituam a análise manual e o palpite por análise estruturada e dados verificados.
              </p>
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                O SmartLic nasceu da observação direta do desperdício no mercado de licitações: empresas gastam horas analisando editais manualmente, analisam oportunidades irrelevantes e perdem as que realmente importam. Nossa plataforma resolve isso com tecnologia.
              </p>
            </div>
          </section>

          {/* STORY-273 AC4: Team Section */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-brand-blue-subtle rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Nosso time
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 space-y-4">
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                O SmartLic foi fundado por profissionais com experiência em <strong className="text-[var(--ink)]">engenharia de avaliações, inteligência artificial e mercado de licitações públicas</strong>. A equipe combina conhecimento técnico em TI com vivência prática no ecossistema B2G brasileiro.
              </p>
              <div className="grid sm:grid-cols-2 gap-4 pt-2">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-brand-blue-subtle rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Engenharia e IA</p>
                    <p className="text-xs text-[var(--ink-muted)]">Desenvolvimento de algoritmos de classificação e pipeline de dados em escala nacional</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-brand-blue-subtle rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Mercado B2G</p>
                    <p className="text-xs text-[var(--ink-muted)]">Vivência prática em contratações públicas e licitações em múltiplos setores</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* STORY-273 AC4: Mission/Vision */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Nossa missão
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 space-y-4">
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                <strong className="text-[var(--ink)]">Democratizar o acesso inteligente a licitações públicas.</strong> Acreditamos que toda empresa que compete no mercado B2G merece ferramentas que transformem decisões de intuitivas para objetivas — independentemente do porte.
              </p>
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                Nossa visão é ser a plataforma de referência em inteligência de licitações no Brasil, eliminando o desperdício de tempo com análises manuais e avaliações subjetivas.
              </p>
            </div>
          </section>

          {/* O Problema que Resolvemos */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-red-100 dark:bg-red-900/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                O problema que resolvemos
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8">
              <div className="grid sm:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 dark:text-red-400 mb-2">70-90%</div>
                  <p className="text-sm text-[var(--ink-secondary)]">
                    dos editais publicados são irrelevantes para qualquer setor específico
                  </p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600 dark:text-red-400 mb-2">40h/mês</div>
                  <p className="text-sm text-[var(--ink-secondary)]">
                    gastas analisando editais irrelevantes por empresas B2G
                  </p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mb-2">27 UFs</div>
                  <p className="text-sm text-[var(--ink-secondary)]">
                    cobertas simultaneamente em cada análise
                  </p>
                </div>
              </div>
              <p className="mt-6 text-[var(--ink-secondary)] leading-relaxed">
                A consequência é previsível: oportunidades reais são perdidas enquanto tempo é desperdiçado com editais incompatíveis. O SmartLic inverte essa equação — você recebe apenas o que importa, com justificativa clara de por quê.
              </p>
            </div>
          </section>

          {/* AC3 — Metodologia */}
          <section id="metodologia" className="scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-brand-blue-subtle rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Como avaliamos cada oportunidade
              </h2>
            </div>

            <p className="text-[var(--ink-secondary)] mb-8 leading-relaxed">
              Cada licitação passa por uma avaliação estruturada baseada em 5 critérios objetivos. O resultado é um nível de aderência (Alta, Média ou Baixa) que indica o quanto aquela oportunidade se encaixa no seu perfil. Critérios objetivos, não opinião.
            </p>

            <div className="space-y-4">
              {criterios.map((criterio, index) => (
                <div
                  key={index}
                  className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-brand-blue-subtle rounded-lg flex items-center justify-center text-brand-blue font-bold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-[var(--ink)] mb-3">
                        {criterio.title}
                      </h3>
                      <div className="space-y-2 text-sm">
                        <p className="text-[var(--ink-secondary)]">
                          <strong className="text-[var(--ink)]">O que é avaliado:</strong> {criterio.what}
                        </p>
                        <p className="text-[var(--ink-secondary)]">
                          <strong className="text-[var(--ink)]">Por que importa:</strong> {criterio.why}
                        </p>
                        <p className="text-[var(--ink-secondary)]">
                          <strong className="text-[var(--ink)]">Como impacta a recomendação:</strong> {criterio.how}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* AC4 — Fontes de Dados */}
          <section>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Fontes de dados
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8 space-y-4">
              <p className="text-[var(--ink-secondary)] leading-relaxed">
                Todos os dados utilizados pelo SmartLic vêm de <strong className="text-[var(--ink)]">portais oficiais de contratações públicas do Brasil</strong> — que abrangem licitações federais, estaduais e municipais, incluindo autarquias, fundações e empresas públicas. São dados públicos, abertos e acessíveis a qualquer cidadão.
              </p>

              <div className="grid sm:grid-cols-2 gap-4 pt-2">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Cobertura nacional</p>
                    <p className="text-xs text-[var(--ink-muted)]">27 UFs monitoradas simultaneamente</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Atualização contínua</p>
                    <p className="text-xs text-[var(--ink-muted)]">Consulta em tempo real a cada análise</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Consolidação automática</p>
                    <p className="text-xs text-[var(--ink-muted)]">Múltiplas fontes oficiais unificadas</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <div>
                    <p className="font-medium text-[var(--ink)] text-sm">Dados verificados</p>
                    <p className="text-xs text-[var(--ink-muted)]">Dados oficiais, não estimativas</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-4 bg-[var(--surface-1)] rounded-xl border border-[var(--border)]">
                <p className="text-sm text-[var(--ink-secondary)]">
                  O SmartLic não é afiliado ao governo. Somos uma plataforma independente de inteligência de decisão que agrega e analisa dados públicos para facilitar o acesso a oportunidades de contratações públicas.
                </p>
              </div>
            </div>
          </section>

          {/* STORY-273 AC4: Contact Information */}
          <section id="contato">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-brand-blue-subtle rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-[var(--ink)]">
                Contato
              </h2>
            </div>

            <div className="bg-[var(--surface-0)] border border-[var(--border)] rounded-2xl p-6 sm:p-8">
              <div className="grid sm:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold text-[var(--ink)] mb-3">CONFENGE Avaliações e Inteligência Artificial LTDA</h3>
                  <div className="space-y-2 text-sm text-[var(--ink-secondary)]">
                    <p>Av. Pref. Osmar Cunha, 416 - Centro</p>
                    <p>Florianópolis - SC, 88015-100</p>
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-[var(--ink)] mb-3">Canais de atendimento</h3>
                  <div className="space-y-2 text-sm text-[var(--ink-secondary)]">
                    <p>
                      <Link href="/ajuda#contato" className="text-brand-blue hover:underline">Central de Ajuda</Link>
                      {' '}— Dúvidas e suporte
                    </p>
                    <p>
                      <Link href="/ajuda" className="text-brand-blue hover:underline">Perguntas Frequentes</Link>
                      {' '}— Respostas rápidas
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* CTA */}
          <section className="text-center py-8">
            <h2 className="text-2xl font-bold text-[var(--ink)] mb-3">
              Experimente com seus próprios dados
            </h2>
            <p className="text-[var(--ink-secondary)] mb-6 max-w-lg mx-auto">
              Produto completo por 14 dias. Veja as oportunidades reais do seu setor analisadas com os critérios acima.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/signup?source=sobre-cta"
                className="inline-flex items-center gap-2 bg-[var(--brand-navy)] hover:bg-[var(--brand-blue-hover)] text-white px-8 py-3 rounded-button font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
              >
                Analisar oportunidades do meu setor
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </Link>
              <Link
                href="/ajuda"
                className="inline-flex items-center gap-2 border border-[var(--border)] text-[var(--ink)] px-6 py-3 rounded-button font-semibold hover:bg-[var(--surface-1)] transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
              >
                Ver perguntas frequentes
              </Link>
            </div>
          </section>

          {/* Back Link */}
          <div className="text-center pb-4">
            <Link href="/" className="text-sm text-[var(--ink-muted)] hover:underline">
              Voltar para a página inicial
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
}
