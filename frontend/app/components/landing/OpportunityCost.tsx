'use client';

import { AlertTriangle } from 'lucide-react';
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
        className={`
          bg-gradient-to-br from-yellow-50 to-yellow-100
          dark:from-yellow-900/20 dark:to-yellow-800/20
          border border-yellow-200/50 dark:border-yellow-700/50
          rounded-2xl p-8 shadow-md
          transition-all duration-500
          hover:shadow-lg hover:-translate-y-0.5
          ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
        `}
      >
        {/* Headline Provocativa — Tom institucional direto */}
        <div className="flex items-start gap-4">
          <AlertTriangle
            className="w-8 h-8 text-yellow-600 flex-shrink-0 mt-1"
            aria-label="Alerta"
          />

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">
              Cada edital que passa é um contrato que vai para o concorrente.
            </h2>

            {/* Bullet Points — Curtos e diretos */}
            <ul className="mt-6 space-y-3 text-lg text-ink-secondary">
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>
                  <strong className="text-ink tabular-nums">R$ 2,3 bilhões</strong> em oportunidades mapeadas mensalmente
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>Editais relevantes vencem enquanto você ainda procura</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>Quem encontra primeiro, licita primeiro</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
