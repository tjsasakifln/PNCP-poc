'use client';

import { useInView } from '@/app/hooks/useInView';

interface BeforeAfterProps {
  className?: string;
}

export default function BeforeAfter({ className = '' }: BeforeAfterProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-12 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Transforme sua busca por licitações
      </h2>

      {/* Layout Assimétrico 40/60 */}
      <div className="grid md:grid-cols-5 gap-6">
        {/* Sem SmartLic — 40% (2 cols) */}
        <div
          className={`md:col-span-2 bg-error-subtle p-6 sm:p-8 rounded-card border border-[var(--border)] transition-all duration-500 delay-100 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-error/10 rounded-full flex items-center justify-center">
              <svg
              role="img"
              aria-label="Ícone"
                className="w-5 h-5 text-error"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-ink uppercase tracking-wide">Busca Manual</h3>
          </div>

          <ul className="space-y-3 text-ink-secondary text-sm">
            <li className="flex items-start gap-2">
              <span className="text-error flex-shrink-0">✕</span>
              <span><strong className="text-ink">8h/dia</strong> em portais</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-error flex-shrink-0">✕</span>
              <span>Editais perdidos</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-error flex-shrink-0">✕</span>
              <span>27 fontes fragmentadas</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-error flex-shrink-0">✕</span>
              <span>Sem histórico</span>
            </li>
          </ul>
        </div>

        {/* Com SmartLic — 60% (3 cols) — Destaque */}
        <div
          className={`md:col-span-3 bg-gradient-to-br from-brand-blue-subtle to-surface-1 p-6 sm:p-8 rounded-card border-2 border-brand-blue/30 transition-all duration-500 delay-200 hover:-translate-y-0.5 hover:shadow-lg ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-brand-blue/10 rounded-full flex items-center justify-center">
              <svg
              role="img"
              aria-label="Ícone"
                className="w-5 h-5 text-brand-blue"
                fill="currentColor"
                viewBox="0 0 20 20"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-ink uppercase tracking-wide">Com SmartLic</h3>
          </div>

          <ul className="space-y-3 text-ink-secondary">
            <li className="flex items-start gap-2">
              <span className="text-success flex-shrink-0 font-bold">✓</span>
              <span><strong className="text-ink">15min/dia</strong> automatizado</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success flex-shrink-0 font-bold">✓</span>
              <span>Alertas em tempo real</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success flex-shrink-0 font-bold">✓</span>
              <span>Busca unificada</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success flex-shrink-0 font-bold">✓</span>
              <span>Histórico completo</span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
