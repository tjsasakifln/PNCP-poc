'use client';

import { useInView } from '@/app/hooks/useInView';

interface FinalCTAProps {
  className?: string;
}

/**
 * SAB-006 AC3: Absorbed beta counter content into FinalCTA.
 */
export default function FinalCTA({ className = '' }: FinalCTAProps) {
  const { ref, isInView } = useInView({ threshold: 0.3 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 ${className}`}
    >
      <div
        className={`bg-brand-navy rounded-card p-10 sm:p-14 text-center text-white transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight mb-4">
          Licitações estão abrindo agora. E você?
        </h2>

        <p
          className={`text-lg sm:text-xl mb-6 text-white/80 transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          A cada dia sem filtro estratégico, editais compatíveis com sua empresa passam — e vão para outro.
        </p>

        {/* SAB-006: Absorbed beta counter */}
        <p
          className={`text-sm mb-8 text-white/60 transition-all duration-500 delay-150 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
          data-testid="beta-counter"
        >
          Mais de <span className="text-white font-semibold">10 empresas</span> já testaram — uniformes, TI, engenharia, saúde e facilities
        </p>

        <div
          className={`flex flex-col sm:flex-row items-center justify-center gap-4 transition-all duration-500 delay-200 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <a
            href="/signup?source=landing-cta"
            className="w-full sm:w-auto bg-white text-brand-navy hover:bg-surface-1 font-bold px-8 py-4 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] text-center text-lg focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white/50"
          >
            Analisar oportunidades do meu setor
          </a>
        </div>

        <div
          className={`mt-6 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-white/70 transition-all duration-500 delay-300 ${
            isInView ? 'opacity-100' : 'opacity-0'
          }`}
        >
          <span>Fontes oficiais verificadas</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span>Critérios objetivos</span>
          <span className="hidden sm:inline text-white/30">|</span>
          <span>Cancelamento em 1 clique</span>
        </div>

        <p
          className={`mt-3 text-sm text-white/50 transition-all duration-500 delay-400 ${
            isInView ? 'opacity-100' : 'opacity-0'
          }`}
        >
          Produto completo por 14 dias. Sem cartão. Se não analisar hoje, pode perder.
        </p>
      </div>
    </section>
  );
}
