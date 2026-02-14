'use client';

import { useInView } from '@/app/hooks/useInView';

interface DifferentialsGridProps {
  className?: string;
}

interface DifferentialCard {
  icon: React.ReactNode;
  title: string;
  bullets: string[];
  featured?: boolean;
}

const differentials: DifferentialCard[] = [
  {
    featured: true,
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
      </svg>
    ),
    title: 'FILTRO SETORIAL INTELIGENTE',
    bullets: ['9 setores especializados', 'Palavras-chave por nicho', 'Só oportunidades do seu mercado'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'SÓ OPORTUNIDADES ABERTAS',
    bullets: ['Editais com prazo vigente', 'Sem resultados vencidos', 'Ação imediata garantida'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    title: 'RESUMO EXECUTIVO POR IA',
    bullets: ['Análise automática de cada edital', 'Destaques e valores-chave', 'Decisão em segundos, não horas'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
    title: 'ZERO RUÍDO',
    bullets: ['Sem editais irrelevantes', 'Sem duplicatas', 'Curadoria, não listagem'],
  },
];

export default function DifferentialsGrid({ className = '' }: DifferentialsGridProps) {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-4 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Inteligência que gera resultado
      </h2>
      <p
        className={`text-lg text-center text-ink-secondary mb-12 max-w-2xl mx-auto transition-all duration-500 delay-100 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Cada diferencial foi pensado para você ganhar licitações, não apenas encontrá-las
      </p>

      {/* Layout 1+3 Assimétrico */}
      <div className="grid lg:grid-cols-4 gap-6">
        {/* Card Featured (TEMPO) — Full width on mobile, first col on desktop */}
        <div
          className={`lg:col-span-4 bg-brand-navy text-white p-8 rounded-card transition-all duration-500 delay-150 hover:-translate-y-0.5 hover:shadow-xl ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-white/10 rounded-card flex items-center justify-center">
                {differentials[0].icon}
              </div>
              <h3 className="text-2xl font-bold tracking-wide">{differentials[0].title}</h3>
            </div>
            <ul className="flex flex-wrap gap-x-8 gap-y-2 text-white/90">
              {differentials[0].bullets.map((bullet, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-success">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* 3 Cards menores */}
        {differentials.slice(1).map((differential, index) => (
          <div
            key={index}
            className={`lg:col-span-1 bg-surface-1 p-6 rounded-card border border-[var(--border)] transition-all duration-500 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: `${200 + index * 50}ms` }}
          >
            <div className="w-12 h-12 bg-brand-blue-subtle rounded-card flex items-center justify-center text-brand-blue mb-4">
              {differential.icon}
            </div>
            <h3 className="text-sm font-bold text-ink uppercase tracking-wide mb-3">
              {differential.title}
            </h3>
            <ul className="space-y-1.5 text-sm text-ink-secondary">
              {differential.bullets.map((bullet, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-brand-blue">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
