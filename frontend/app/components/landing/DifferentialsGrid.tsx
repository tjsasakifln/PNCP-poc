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
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    title: 'TEMPO',
    bullets: ['500k oportunidades/mês processadas', 'Resumos automáticos', 'Resultado em minutos'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
    title: 'PRECISÃO',
    bullets: ['Filtros por setor, estado, valor', 'Palavras-chave customizáveis', 'Zero ruído'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: 'CONFIANÇA',
    bullets: ['Fonte: PNCP', '+ fontes complementares', 'Atualização diária'],
  },
  {
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
      </svg>
    ),
    title: 'PRATICIDADE',
    bullets: ['Excel 1-clique', 'Zero config', 'Histórico completo'],
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
        Diferenciais que importam
      </h2>
      <p
        className={`text-lg text-center text-ink-secondary mb-12 max-w-2xl mx-auto transition-all duration-500 delay-100 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Desenvolvido por servidores públicos
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
