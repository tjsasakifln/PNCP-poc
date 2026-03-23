import { X, CheckCircle2, AlertCircle, Check } from 'lucide-react';
import AnimateOnScroll from '@/components/ui/AnimateOnScroll';

interface BeforeAfterProps {
  className?: string;
}

/**
 * DEBT-2: Converted to RSC with AnimateOnScroll client islands.
 */
export default function BeforeAfter({ className = '' }: BeforeAfterProps) {
  return (
    <section
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 ${className}`}
    >
      <AnimateOnScroll threshold={0.2}>
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-12">
          O que acontece sem filtro estratégico — e com ele
        </h2>
      </AnimateOnScroll>

      {/* Layout Assimétrico 40/60 */}
      <div className="grid md:grid-cols-5 gap-6">
        {/* Sem SmartLic — 40% (2 cols) */}
        <AnimateOnScroll
          delay={100}
          className="md:col-span-2 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border border-red-200/50 dark:border-red-700/50 rounded-2xl p-6 sm:p-8 shadow-md hover:-translate-y-1 hover:shadow-lg"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-red-500/10 rounded-full flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600" aria-label="Sem Curadoria" />
            </div>
            <h3 className="text-lg font-bold text-red-900 dark:text-red-100 uppercase tracking-wide">Sem Filtro Estratégico</h3>
          </div>

          <ul className="space-y-3 text-red-800 dark:text-red-200 text-sm">
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Gasta horas analisando editais que não se encaixam no seu perfil</span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Perde licitações porque não sabia que existiam</span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Descobre oportunidades quando o prazo já está curto</span>
            </li>
            <li className="flex items-start gap-2">
              <X className="text-red-500 flex-shrink-0 mt-1" size={18} />
              <span>Decide com base em intuição — opera no escuro, sem critérios objetivos</span>
            </li>
          </ul>
        </AnimateOnScroll>

        {/* Com SmartLic — 60% (3 cols) — Destaque */}
        <AnimateOnScroll
          delay={200}
          className="md:col-span-3 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-2 border-blue-200/50 dark:border-blue-700/50 rounded-2xl p-6 sm:p-8 shadow-md hover:-translate-y-1 hover:shadow-lg"
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
              <span>Editais incompatíveis descartados antes de chegar até você — sobra só o relevante</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Cobertura nacional automática — todas as UFs de fontes oficiais</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Acesso assim que publicados — você se posiciona antes</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="text-green-500 flex-shrink-0 mt-1 font-bold" size={18} />
              <span>Cada decisão baseada em critérios objetivos documentados: setor, valor, prazo, região, modalidade</span>
            </li>
          </ul>
        </AnimateOnScroll>
      </div>
    </section>
  );
}
