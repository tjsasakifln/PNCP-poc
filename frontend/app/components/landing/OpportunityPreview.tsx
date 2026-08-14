'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useScrollAnimation, fadeInUp, staggerContainer } from '@/lib/animations';
import AnimateOnScroll from '@/components/ui/AnimateOnScroll';

/**
 * COPY-COP-005 Phase 4: OpportunityPreview — Static placeholder showing
 * hardcoded opportunities. Demonstrates the value of SmartLic filtering.
 *
 * Shows real-looking but static bid cards with viability scoring.
 * Replaced with live data when user signs up.
 */
const MOCK_OPPORTUNITIES = [
  {
    id: '1',
    title: 'Pregão Eletrônico — Uniformes Escolares',
    orgao: 'Secretaria Municipal de Educação',
    uf: 'SP',
    valor: 'R$ 1.2 milhão',
    prazo: '22 dias',
    modalidade: 'Pregão',
    compatibilidade: 92,
    status: 'open',
  },
  {
    id: '2',
    title: 'Concorrência — Obras de Pavimentação',
    orgao: 'Prefeitura Municipal',
    uf: 'MG',
    valor: 'R$ 4.8 milhões',
    prazo: '45 dias',
    modalidade: 'Concorrência',
    compatibilidade: 78,
    status: 'open',
  },
  {
    id: '3',
    title: 'Tomada de Preços — Serviços de Limpeza Urbana',
    orgao: 'Secretaria de Infraestrutura',
    uf: 'BA',
    valor: 'R$ 890 mil',
    prazo: '15 dias',
    modalidade: 'Tomada de Preços',
    compatibilidade: 85,
    status: 'open',
  },
];

function ViabilityBadge({ score }: { score: number }) {
  const color = score >= 85 ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
    : score >= 70 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
    : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400';

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${score >= 85 ? 'bg-emerald-500' : score >= 70 ? 'bg-amber-500' : 'bg-slate-400'}`} />
      {score}% viável
    </span>
  );
}

export default function OpportunityPreview() {
  const { ref, isVisible } = useScrollAnimation(0.1);

  return (
    <section
      ref={ref}
      className="max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16"
      data-testid="opportunity-preview"
    >
      <AnimateOnScroll>
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-ink mb-3">
            Oportunidades reais que você está perdendo agora
          </h2>
          <p className="text-ink-secondary max-w-2xl mx-auto">
            Enquanto você lê este texto, editais compatíveis com seu perfil estão sendo publicados.
            Veja exemplos reais do que o SmartLic encontra para você.
          </p>
        </div>
      </AnimateOnScroll>

      <motion.div
        className="grid gap-4 md:grid-cols-3"
        variants={staggerContainer}
        initial="hidden"
        animate={isVisible ? 'visible' : 'hidden'}
      >
        {MOCK_OPPORTUNITIES.map((opp) => (
          <motion.div
            key={opp.id}
            variants={fadeInUp}
            className="group relative bg-surface-0 border border-border rounded-xl p-5 hover:shadow-lg hover:border-border-strong transition-all"
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-2 mb-3">
              <h3 className="text-sm font-semibold text-ink leading-snug line-clamp-2">
                {opp.title}
              </h3>
              <ViabilityBadge score={opp.compatibilidade} />
            </div>

            {/* Org */}
            <p className="text-xs text-ink-muted mb-3 line-clamp-1">
              {opp.orgao} • {opp.uf}
            </p>

            {/* Details grid */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              <div>
                <span className="text-ink-muted block">Valor estimado</span>
                <span className="text-ink font-semibold">{opp.valor}</span>
              </div>
              <div>
                <span className="text-ink-muted block">Prazo</span>
                <span className="text-ink font-semibold">{opp.prazo}</span>
              </div>
              <div>
                <span className="text-ink-muted block">Modalidade</span>
                <span className="text-ink">{opp.modalidade}</span>
              </div>
              <div>
                <span className="text-ink-muted block">Status</span>
                <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Aberta
                </span>
              </div>
            </div>

            {/* CTA */}
            <a
              href="/consultoria-b2g?source=opportunity-preview"
              className="block w-full text-center text-sm font-semibold text-brand-blue hover:text-brand-blue-hover py-2 rounded-lg border border-brand-blue/30 hover:border-brand-blue/50 hover:bg-brand-blue-subtle transition-all"
              data-testid={`opportunity-cta-${opp.id}`}
            >
              Ver análise completa →
            </a>
          </motion.div>
        ))}
      </motion.div>

      <AnimateOnScroll delay={200}>
        <div className="text-center mt-10">
          <a
            href="/consultoria-b2g?source=opportunity-preview-bottom"
            className="inline-flex items-center gap-2 text-sm font-semibold text-brand-blue hover:text-brand-blue-hover transition-colors"
            data-testid="opportunity-preview-cta"
          >
            Ver oportunidades reais para meu setor →
          </a>
        </div>
      </AnimateOnScroll>
    </section>
  );
}
