/**
 * Features Page — Transformation Narratives
 *
 * GTM-009: Complete rewrite from task-based to transformation-based copy.
 * Each feature uses "Sem SmartLic" → "Com SmartLic" structure.
 *
 * Aligned with: GTM-007 (no PNCP), GTM-008 (IA as decision intelligence),
 * GTM-002 (SmartLic Pro), GTM-003 (7-day full product trial)
 *
 * @page
 */

import Footer from '../components/Footer';
import { FeaturesContent } from './FeaturesContent';


// GTM-COPY-006 AC5: Per-page metadata for /features
export const metadata = {
  title: 'O Que Muda no Seu Resultado com Avaliação de Viabilidade',
  description: 'Compare cenários: sem avaliação vs com SmartLic. Critérios objetivos, fontes oficiais e filtragem estratégica para decidir em quais licitações investir.',
  alternates: {
    canonical: 'https://smartlic.tech/features',
  },
};

export default function FeaturesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              O Que Muda no Seu Resultado
            </h1>
            <p className="text-xl text-white/90 mb-8">
              SmartLic não é sobre fazer tarefas mais rápido. É sobre transformar como você encontra, avalia e decide em quais licitações investir tempo. Compare os cenários:
            </p>
            <a
              href="/signup?source=features-hero"
              className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
            >
              <span>Analisar oportunidades do meu setor</span>
              <svg
                role="img"
                aria-label="Seta para direita"
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </a>
          </div>
        </div>
      </section>

      {/* Transformation Features (Client Component for GlassCard animations) */}
      <FeaturesContent />

      {/* AC8: Trust & Transparency Section */}
      <section className="py-16 bg-surface-1">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl sm:text-3xl font-bold text-ink text-center mb-4">
            Transparência nos Critérios de Avaliação
          </h2>
          <p className="text-lg text-ink-secondary text-center max-w-2xl mx-auto mb-10">
            Cada recomendação é baseada em critérios documentados e verificáveis — nunca em palpite ou heurísticas genéricas.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-surface-0 border border-[color:var(--border)] rounded-xl p-5">
              <div className="w-8 h-8 bg-brand-blue/10 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-4 h-4 text-brand-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              </div>
              <h3 className="font-bold text-sm text-ink mb-1">Critérios objetivos</h3>
              <p className="text-xs text-ink-secondary">5 fatores de avaliação documentados: setor, valor, prazo, região e modalidade</p>
            </div>
            <div className="bg-surface-0 border border-[color:var(--border)] rounded-xl p-5">
              <div className="w-8 h-8 bg-brand-blue/10 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-4 h-4 text-brand-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <h3 className="font-bold text-sm text-ink mb-1">Fontes oficiais</h3>
              <p className="text-xs text-ink-secondary">Dados de fontes oficiais de contratações públicas — 27 UFs cobertas</p>
            </div>
            <div className="bg-surface-0 border border-[color:var(--border)] rounded-xl p-5">
              <div className="w-8 h-8 bg-brand-blue/10 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-4 h-4 text-brand-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              </div>
              <h3 className="font-bold text-sm text-ink mb-1">Justificativa visível</h3>
              <p className="text-xs text-ink-secondary">Cada oportunidade mostra por que foi selecionada e qual o nível de aderência</p>
            </div>
            <div className="bg-surface-0 border border-[color:var(--border)] rounded-xl p-5">
              <div className="w-8 h-8 bg-brand-blue/10 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-4 h-4 text-brand-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              </div>
              <h3 className="font-bold text-sm text-ink mb-1">Sem dados fabricados</h3>
              <p className="text-xs text-ink-secondary">Métricas reais do sistema. Sem estatísticas inventadas ou resultados inflados.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Comece a filtrar o que realmente vale a pena
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Produto completo por 30 dias. Se uma única licitação ganha pagar o investimento do ano inteiro, por que esperar?
          </p>
          <a
            href="/signup?source=features-bottom-cta"
            className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
          >
            <span>Analisar oportunidades do meu setor</span>
            <svg
              role="img"
              aria-label="Seta para direita"
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </a>
        </div>
      </section>

      <Footer />
    </>
  );
}
