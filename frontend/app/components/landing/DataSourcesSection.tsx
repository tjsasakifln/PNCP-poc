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
          Cobertura total, precisão absoluta
        </h2>

        <p
          className={`text-lg text-ink-secondary mb-8 transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          100% das licitações federais, direto da fonte oficial do governo.
        </p>

        {/* Fonte Primária: PNCP */}
        <div
          className={`bg-brand-navy text-white p-8 rounded-card mb-6 transition-all duration-500 delay-150 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="flex items-center justify-center gap-3 mb-3">
            <svg
              role="img"
              aria-label="Ícone"
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
            <h3 className="text-xl font-bold">Portal Nacional de Contratações Públicas</h3>
          </div>
          <p className="text-2xl font-bold mb-1">PNCP — 100% das licitações federais</p>
          <p className="text-white/80 text-sm mb-4">Fonte oficial do Governo Federal • 27 estados • Atualização contínua</p>
          <a
            href="https://pncp.gov.br"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-white text-brand-navy px-5 py-2 rounded-button font-semibold hover:bg-surface-1 transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white/50"
            aria-label="Acessar PNCP - abre em nova aba"
          >
            Conhecer o PNCP
            <svg
              role="img"
              aria-label="Ícone"
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
              />
            </svg>
          </a>
        </div>

        {/* Fontes Complementares */}
        <div
          className={`bg-surface-1 p-6 rounded-card border border-[var(--border)] transition-all duration-500 delay-200 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <h4 className="text-sm font-bold text-ink uppercase tracking-wide mb-4">
            Fontes Complementares em Expansão
          </h4>
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-ink-secondary">
            {['BLL', 'Portal Compras Públicas', 'BNC', 'Licitar Digital', 'Portais estaduais'].map((source) => (
              <span
                key={source}
                className="bg-surface-0 border border-[var(--border)] px-3 py-1.5 rounded-full"
              >
                {source}
              </span>
            ))}
          </div>
          <p className="text-xs text-ink-muted mt-4">Integrações em constante expansão para cobertura máxima</p>
        </div>
      </div>
    </section>
  );
}
