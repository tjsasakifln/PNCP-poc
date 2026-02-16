'use client';

import { X, CheckCircle2, AlertCircle, Check } from 'lucide-react';
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
        Da busca manual à decisão estratégica
      </h2>

      {/* Layout Assimétrico 40/60 */}
      <div className="grid md:grid-cols-5 gap-6">
        {/* Sem SmartLic — 40% (2 cols) */}
        <div
          className={`
            md:col-span-2
            bg-gradient-to-br from-red-50 to-red-100
            dark:from-red-900/20 dark:to-red-800/20
            border border-red-200/50 dark:border-red-700/50
            rounded-2xl p-6 sm:p-8 shadow-md
            transition-all duration-500 delay-100
            hover:-translate-y-1 hover:shadow-lg
            ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
          `}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-red-500/10 rounded-full flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600" aria-label="Sem Curadoria" />
            </div>
            <h3 className="text-lg font-bold text-red-900 dark:text-red-100 uppercase tracking-wide">Sem Inteligência de Mercado</h3>
          </div>

          <ul className="space-y-3 text-red-800 dark:text-red-200 text-sm">
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Perde contratos por <strong className="text-red-900 dark:text-red-100">falta de visibilidade</strong></span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Oportunidades certas passam despercebidas</span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Concorrentes se posicionam antes de você</span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Decisões baseadas em intuição, não em dados</span>
            </li>
          </ul>
        </div>

        {/* Com SmartLic — 60% (3 cols) — Destaque */}
        <div
          className={`
            md:col-span-3
            bg-gradient-to-br from-blue-50 to-blue-100
            dark:from-blue-900/20 dark:to-blue-800/20
            border-2 border-blue-200/50 dark:border-blue-700/50
            rounded-2xl p-6 sm:p-8 shadow-md
            transition-all duration-500 delay-200
            hover:-translate-y-1 hover:shadow-lg
            ${isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}
          `}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-blue-600" aria-label="Com SmartLic" />
            </div>
            <h3 className="text-lg font-bold text-blue-900 dark:text-blue-100 uppercase tracking-wide">Com SmartLic</h3>
          </div>

          <ul className="space-y-3 text-blue-800 dark:text-blue-200">
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Visão completa do mercado <strong className="text-blue-900 dark:text-blue-100">em tempo real</strong></span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Avaliação objetiva: vale a pena ou não, e por quê</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Posicione-se antes da concorrência</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Decisões com confiança baseadas em inteligência</span>
            </li>
          </ul>
        </div>
      </div>
    </section>
  );
}
