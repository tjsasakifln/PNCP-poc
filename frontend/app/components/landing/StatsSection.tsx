'use client';

import { useState, useEffect, useRef } from 'react';
import { useInView } from '@/app/hooks/useInView';

interface StatsSectionProps {
  className?: string;
}

/**
 * SAB-006 AC2/AC6: Consolidated stats section with counter animation.
 * All key metrics (87%, 15, 27, 1000+) live here — removed from other sections.
 * Starts with opacity: 0 → fade-in + counting animation (fixes FOUC from P3-01).
 */
export default function StatsSection({ className = '' }: StatsSectionProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });
  const [counts, setCounts] = useState({ sectors: 0, rules: 0, states: 0, filtered: 0 });
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!isInView || hasAnimated.current) return;
    hasAnimated.current = true;

    const targets = { sectors: 15, rules: 1000, states: 27, filtered: 87 };
    const duration = 1200;
    const steps = 40;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      setCounts({
        sectors: Math.min(Math.round(targets.sectors * progress), targets.sectors),
        rules: Math.min(Math.round(targets.rules * progress), targets.rules),
        states: Math.min(Math.round(targets.states * progress), targets.states),
        filtered: Math.min(Math.round(targets.filtered * progress), targets.filtered),
      });
      if (step >= steps) clearInterval(timer);
    }, duration / steps);

    return () => clearInterval(timer);
  }, [isInView]);

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 bg-brand-blue-subtle/50 ${className}`}
    >
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-10 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Impacto real no mercado de licitações
      </h2>

      {/* Layout Hero Number + 3 menores (Assimétrico) */}
      <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
        {/* Hero Number — 15 setores */}
        <div
          role="text"
          aria-label="15 setores especializados"
          className={`flex-shrink-0 text-center p-8 lg:p-12 bg-surface-0 rounded-card border border-[var(--border)] shadow-sm transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-4 scale-95'
          }`}
        >
          <div aria-hidden="true" className="text-5xl sm:text-6xl lg:text-7xl font-display tracking-tighter text-brand-navy tabular-nums">
            {counts.sectors}
          </div>
          <div aria-hidden="true" className="text-lg text-ink-secondary mt-2 font-medium">setores especializados</div>
          <div className="w-16 h-1 bg-brand-blue mx-auto mt-4 rounded-full" />
        </div>

        {/* 3 Stats menores */}
        <div className="flex-1 grid sm:grid-cols-3 gap-6 w-full">
          <div
            role="text"
            aria-label="87% de editais descartados"
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-200 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div aria-hidden="true" className="text-3xl sm:text-4xl font-bold text-brand-blue tabular-nums">{counts.filtered}%</div>
            <div aria-hidden="true" className="text-sm text-ink-secondary mt-1">de editais descartados</div>
          </div>

          <div
            role="text"
            aria-label="1000+ regras de filtragem"
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-250 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div aria-hidden="true" className="text-3xl sm:text-4xl font-bold text-brand-blue tabular-nums">{counts.rules}+</div>
            <div aria-hidden="true" className="text-sm text-ink-secondary mt-1">regras de filtragem</div>
          </div>

          <div
            role="text"
            aria-label="27 estados cobertos"
            className={`text-center p-6 bg-surface-0 rounded-card border border-[var(--border)] transition-all duration-500 delay-300 hover:-translate-y-0.5 hover:shadow-md ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
          >
            <div aria-hidden="true" className="text-3xl sm:text-4xl font-bold text-brand-blue tabular-nums">{counts.states}</div>
            <div aria-hidden="true" className="text-sm text-ink-secondary mt-1">estados cobertos</div>
          </div>
        </div>
      </div>
    </section>
  );
}
