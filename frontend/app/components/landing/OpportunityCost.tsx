'use client';

import { useInView } from '@/app/hooks/useInView';
import { TrendingDown, Clock, Users } from 'lucide-react';

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
        className={`relative overflow-hidden bg-gradient-to-br from-amber-50 via-orange-50 to-amber-50 dark:from-amber-950/20 dark:via-orange-950/20 dark:to-amber-950/20 border border-amber-200/50 dark:border-amber-800/30 rounded-2xl shadow-sm transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        {/* Decorative gradient accent */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-500" />

        <div className="relative p-8 sm:p-10 lg:p-12">
          {/* Header com icon mais profissional */}
          <div className="flex items-start gap-4 mb-8">
            <div className="flex-shrink-0 w-14 h-14 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg">
              <TrendingDown className="w-7 h-7 text-white" strokeWidth={2.5} />
            </div>

            <div className="flex-1">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 tracking-tight leading-tight">
                Licitações não encontradas são contratos perdidos.
              </h2>
              <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">
                O mercado de licitações brasileiro em números
              </p>
            </div>
          </div>

          {/* Stats grid - moderno com icons */}
          <div className="grid sm:grid-cols-3 gap-6">
            {/* Stat 1: Volume */}
            <div className="group relative bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-amber-100/50 dark:border-amber-900/30 hover:border-amber-300 dark:hover:border-amber-700 transition-all duration-300 hover:shadow-md">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <TrendingDown className="w-5 h-5 text-amber-600 dark:text-amber-400" strokeWidth={2.5} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-white tabular-nums">
                    500 mil
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    oportunidades/mês no Brasil
                  </div>
                </div>
              </div>
            </div>

            {/* Stat 2: Invisibilidade */}
            <div className="group relative bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-amber-100/50 dark:border-amber-900/30 hover:border-amber-300 dark:hover:border-amber-700 transition-all duration-300 hover:shadow-md">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <Clock className="w-5 h-5 text-red-600 dark:text-red-400" strokeWidth={2.5} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-white">
                    97%
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    descobertos tarde demais
                  </div>
                </div>
              </div>
            </div>

            {/* Stat 3: Competição */}
            <div className="group relative bg-white/80 dark:bg-gray-900/40 backdrop-blur-sm rounded-xl p-6 border border-amber-100/50 dark:border-amber-900/30 hover:border-amber-300 dark:hover:border-amber-700 transition-all duration-300 hover:shadow-md">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <Users className="w-5 h-5 text-orange-600 dark:text-orange-400" strokeWidth={2.5} />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white leading-tight">
                    Agora
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    seu concorrente está buscando
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* CTA sutil */}
          <div className="mt-8 pt-6 border-t border-amber-200/50 dark:border-amber-800/30">
            <p className="text-center text-sm text-gray-600 dark:text-gray-400">
              <span className="font-medium text-gray-900 dark:text-white">SmartLic monitora 27 estados + DF</span> para você não perder nenhuma oportunidade.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
