'use client';

import { useInView } from '@/app/hooks/useInView';

interface DataSourcesSectionProps {
  className?: string;
}

export default function DataSourcesSection({ className = '' }: DataSourcesSectionProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div className="text-center max-w-3xl mx-auto">
        <h2
          className={`text-3xl sm:text-4xl font-bold text-ink tracking-tight mb-6 transition-all duration-500 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          Cobertura nacional, precisão absoluta
        </h2>

        <p
          className={`text-lg text-ink-secondary mb-8 transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          Conectados ao PNCP e ao Portal de Compras Públicas — as duas maiores bases de licitações do Brasil.
        </p>

        {/* Fonte Primária: Inteligência de Fontes */}
        <div
          className={`bg-brand-navy text-white p-8 rounded-card mb-6 transition-all duration-500 delay-150 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="flex items-center justify-center gap-3 mb-3">
            <svg
              role="img"
              aria-label="Cobertura"
              className="w-7 h-7"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <h3 className="text-xl font-bold">Inteligência de Fontes Oficiais</h3>
          </div>
          <p className="text-2xl font-bold mb-1">Duas das maiores bases de licitações públicas do Brasil</p>
          <p className="text-white/80 text-sm mb-4">Portal Nacional de Contratações Públicas (PNCP) + Portal de Compras Públicas</p>
        </div>

        {/* Fontes Complementares */}
        <div
          className={`bg-surface-1 p-6 rounded-card border border-[var(--border)] transition-all duration-500 delay-200 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <h4 className="text-sm font-bold text-ink uppercase tracking-wide mb-4">
            Cobertura em Constante Expansão
          </h4>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-ink-secondary">
            {['PNCP (Federal)', 'Portal de Compras Públicas', 'Novas fontes em breve'].map((source) => (
              <span
                key={source}
                className="bg-surface-0 border border-[var(--border)] px-3 py-1.5 rounded-full"
              >
                {source}
              </span>
            ))}
          </div>
          <p className="text-xs text-ink-muted mt-4">Novas integrações sendo adicionadas regularmente</p>
        </div>
      </div>
    </section>
  );
}
