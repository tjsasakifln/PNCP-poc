import { Shield, Target, DollarSign, Clock, MapPin, Scale, TrendingDown, Eye, CheckCircle2 } from 'lucide-react';
import AnimateOnScroll from '@/components/ui/AnimateOnScroll';

interface TrustCriteriaProps {
  className?: string;
}

const evaluationCriteria = [
  {
    icon: Target,
    title: 'Compatibilidade setorial',
    description: 'Cruza o objeto do edital com mais de 1.000 regras específicas do seu setor + inteligência artificial para editais ambíguos',
  },
  {
    icon: DollarSign,
    title: 'Faixa de valor adequada',
    description: 'Verifica se o valor estimado da licitação é compatível com o porte e capacidade da sua empresa',
  },
  {
    icon: Clock,
    title: 'Prazo viável para preparação',
    description: 'Avalia se há tempo hábil para preparar e submeter uma proposta competitiva',
  },
  {
    icon: MapPin,
    title: 'Região de atuação',
    description: 'Filtra por estados onde sua empresa opera ou tem capacidade de atender',
  },
  {
    icon: Scale,
    title: 'Modalidade favorável',
    description: 'Identifica modalidades onde sua empresa tem mais chance de competir com vantagem',
  },
];

const adherenceLevels = [
  {
    level: 'Alta',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-700 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-900/20',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    description: '3 ou mais critérios atendem seu perfil — oportunidade prioritária',
  },
  {
    level: 'Média',
    color: 'bg-yellow-500',
    textColor: 'text-yellow-700 dark:text-yellow-400',
    bgColor: 'bg-yellow-50 dark:bg-yellow-900/20',
    borderColor: 'border-yellow-200 dark:border-yellow-800',
    description: '2 critérios atendem — vale avaliar com atenção',
  },
  {
    level: 'Baixa',
    color: 'bg-gray-400',
    textColor: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-50 dark:bg-gray-900/20',
    borderColor: 'border-gray-200 dark:border-gray-700',
    description: '1 critério ou menos — considere apenas se estratégico',
  },
];

/**
 * DEBT-2: Converted to RSC with AnimateOnScroll client islands.
 */
export default function TrustCriteria({ className = '' }: TrustCriteriaProps) {
  return (
    <section
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      {/* AC1 — Header */}
      <AnimateOnScroll threshold={0.1}>
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-blue-subtle text-brand-blue text-sm font-medium mb-4">
            <Shield className="w-4 h-4" />
            Transparência de critérios
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-ink tracking-tight mb-4">
            Cada recomendação tem uma justificativa
          </h2>
          <p className="text-lg text-ink-secondary max-w-2xl mx-auto">
            Você sabe exatamente por que cada oportunidade foi selecionada — e por que as outras foram descartadas. Sem caixa preta, sem palpite.
          </p>
        </div>
      </AnimateOnScroll>

      {/* AC2 — 5 Evaluation Criteria */}
      <AnimateOnScroll threshold={0.1} delay={100}>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-16">
          {evaluationCriteria.map((criterion, index) => {
            const Icon = criterion.icon;
            return (
              <div
                key={index}
                className="bg-surface-1 border border-[var(--border)] rounded-2xl p-5 transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md"
                style={{ transitionDelay: `${150 + index * 50}ms` }}
              >
                <div className="w-10 h-10 bg-brand-blue-subtle rounded-xl flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5 text-brand-blue" strokeWidth={2} />
                </div>
                <h3 className="text-sm font-bold text-ink mb-1.5">{criterion.title}</h3>
                <p className="text-xs text-ink-secondary leading-relaxed">{criterion.description}</p>
              </div>
            );
          })}
        </div>
      </AnimateOnScroll>

      {/* AC3 — Adherence Level Explanation */}
      <AnimateOnScroll threshold={0.1} delay={200}>
        <div className="bg-surface-1 border border-[var(--border)] rounded-2xl p-8 mb-16">
          <h3 className="text-xl font-bold text-ink mb-2">Nível de aderência: como funciona</h3>
          <p className="text-sm text-ink-secondary mb-6">
            Cada oportunidade recebe um nível de aderência baseado em quantos critérios de avaliação ela atende para o seu perfil.
          </p>
          <div className="grid sm:grid-cols-3 gap-4">
            {adherenceLevels.map((level) => (
              <div
                key={level.level}
                className={`${level.bgColor} border ${level.borderColor} rounded-xl p-4`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-3 h-3 rounded-full ${level.color}`} />
                  <span className={`font-bold ${level.textColor}`}>{level.level}</span>
                </div>
                <p className="text-sm text-ink-secondary">{level.description}</p>
              </div>
            ))}
          </div>
        </div>
      </AnimateOnScroll>

      {/* AC4 + AC5 — False Positive and Negative Reduction */}
      <AnimateOnScroll threshold={0.1} delay={300}>
        <div className="grid md:grid-cols-2 gap-6">
          {/* AC4 — False Positive Reduction */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200/50 dark:border-blue-700/50 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-500/10 rounded-full flex items-center justify-center">
                <TrendingDown className="w-5 h-5 text-blue-600" />
              </div>
              <h3 className="text-lg font-bold text-ink">Menos ruído, mais precisão</h3>
            </div>
            <p className="text-ink-secondary mb-4">
              Em média, <strong className="text-ink">70-90% dos editais publicados são irrelevantes</strong> para qualquer setor específico. O SmartLic descarta automaticamente o que não se encaixa.
            </p>
            <div className="flex items-start gap-2 text-sm text-blue-800 dark:text-blue-200 bg-blue-100/50 dark:bg-blue-900/30 rounded-lg p-3">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-blue-600" />
              <span>Você recebe 20 recomendações qualificadas, não 2.000 resultados genéricos</span>
            </div>
          </div>

          {/* AC5 — False Negative Reduction */}
          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border border-emerald-200/50 dark:border-emerald-700/50 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center">
                <Eye className="w-5 h-5 text-emerald-600" />
              </div>
              <h3 className="text-lg font-bold text-ink">Nenhuma oportunidade perdida</h3>
            </div>
            <p className="text-ink-secondary mb-4">
              Cobertura de <strong className="text-ink">27 UFs</strong> com múltiplas fontes oficiais. Inteligência artificial avalia até editais com descrições ambíguas para não perder nada relevante.
            </p>
            <div className="flex items-start gap-2 text-sm text-emerald-800 dark:text-emerald-200 bg-emerald-100/50 dark:bg-emerald-900/30 rounded-lg p-3">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-600" />
              <span>Se existe algo compatível em qualquer lugar do Brasil, você sabe</span>
            </div>
          </div>
        </div>
      </AnimateOnScroll>
    </section>
  );
}
