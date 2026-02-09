'use client';

import { useInView } from '@/app/hooks/useInView';

interface OpportunityCostProps {
  className?: string;
}

export default function OpportunityCost({ className = '' }: OpportunityCostProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      <div
        className={`bg-warning-subtle border-l-4 border-warning p-8 rounded-card transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        {/* Headline Provocativa — Tom institucional direto */}
        <div className="flex items-start gap-4">
          <svg
            className="w-8 h-8 text-warning flex-shrink-0 mt-1"
            fill="currentColor"
            viewBox="0 0 20 20"
            role="img"
            aria-label="Alerta"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">
              Licitações não encontradas são contratos perdidos.
            </h2>

            {/* Bullet Points — Curtos e diretos */}
            <ul className="mt-6 space-y-3 text-lg text-ink-secondary">
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>
                  <strong className="text-ink tabular-nums">500 mil</strong> oportunidades/mês no Brasil
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>A maioria passa despercebida</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>Seu concorrente pode estar encontrando agora</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
