'use client';

import { useInView } from '@/app/hooks/useInView';

interface StatsSectionProps {
  className?: string;
}

export default function StatsSection({ className = '' }: StatsSectionProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 bg-brand-blue-subtle/50 ${className}`}
    >
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-12 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Números que falam por si
      </h2>

      {/* Layout Hero Number + 3 menores (Assimétrico) */}
      <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
        {/* Hero Number — 6M+ */}
        <div
          className={`flex-shrink-0 text-center p-8 lg:p-12 bg-surface-0 rounded-card border border-[var(--border)] shadow-sm transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'
          }`}
        >
          <div className="text-6xl sm:text-7xl lg:text-8xl font-display tracking-tighter text-brand-navy tabular-nums">
            6M+
          </div>
          <div className="text-lg text-ink-secondary mt-2 font-medium">licitações/ano</div>
          <div className="w-16 h-1 bg-brand-blue mx-auto mt-4 rounded-full" />
        </div>

        {/* 3 Stats menores */}
        <div className="flex-1 grid sm:grid-cols-3 gap-6 w-full">
          <div
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-200 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div className="text-3xl sm:text-4xl font-bold text-brand-blue tabular-nums">500k</div>
            <div className="text-sm text-ink-secondary mt-1">/mês processadas</div>
          </div>

          <div
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-250 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div className="text-3xl sm:text-4xl font-bold text-brand-blue tabular-nums">12</div>
            <div className="text-sm text-ink-secondary mt-1">setores atendidos</div>
          </div>

          <div
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-300 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div className="text-2xl sm:text-3xl font-bold text-brand-blue">Servidores</div>
            <div className="text-sm text-ink-secondary mt-1">públicos criadores</div>
          </div>
        </div>
      </div>
    </section>
  );
}
