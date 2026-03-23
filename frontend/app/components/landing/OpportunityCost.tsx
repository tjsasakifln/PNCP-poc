import { AlertTriangle } from 'lucide-react';
import AnimateOnScroll from '@/components/ui/AnimateOnScroll';

interface OpportunityCostProps {
  className?: string;
}

/**
 * DEBT-2: Converted to RSC with AnimateOnScroll client island.
 */
export default function OpportunityCost({ className = '' }: OpportunityCostProps) {
  return (
    <section
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 ${className}`}
    >
      <AnimateOnScroll
        threshold={0.2}
        className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border border-yellow-200/50 dark:border-yellow-700/50 rounded-2xl p-8 shadow-md hover:shadow-lg hover:-translate-y-0.5"
      >
        {/* Headline Provocativa */}
        <div className="flex items-start gap-4">
          <AlertTriangle
            className="w-8 h-8 text-yellow-600 flex-shrink-0 mt-1"
            aria-label="Alerta"
          />

          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">
              Continuar sem filtro estratégico é operar no escuro.
            </h2>

            {/* Bullet Points */}
            <ul className="mt-6 space-y-3 text-lg text-ink-secondary">
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>
                  Uma única licitação perdida por investir proposta no edital errado pode custar <strong className="text-ink tabular-nums">R$ 50.000, R$ 200.000 ou mais</strong>
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>Sem filtro estratégico, você decide com base em intuição — sem saber se aquele edital realmente se encaixa</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-warning font-bold">•</span>
                <span>O risco não é perder tempo. É perder dinheiro investindo proposta em licitações erradas.</span>
              </li>
            </ul>

            <p className="mt-6 text-base text-ink font-medium border-t border-yellow-200/50 dark:border-yellow-700/50 pt-4">
              Com SmartLic, cada decisão é baseada em critérios objetivos documentados — setor, valor, prazo, região e modalidade.
            </p>
          </div>
        </div>
      </AnimateOnScroll>
    </section>
  );
}
