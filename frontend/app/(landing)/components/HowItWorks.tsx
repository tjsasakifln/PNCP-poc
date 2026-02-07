interface HowItWorksProps {
  className?: string;
}

interface StepCard {
  stepNumber: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const steps: StepCard[] = [
  {
    stepNumber: 1,
    title: 'Configure filtros',
    description:
      'Defina estado, setor, faixa de valor e palavras-chave relevantes para sua empresa.',
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
        />
      </svg>
    ),
  },
  {
    stepNumber: 2,
    title: 'Receba alertas',
    description:
      'Buscas automáticas diárias e relatórios com resumos IA. Alertas em tempo real para oportunidades críticas.',
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
    ),
  },
  {
    stepNumber: 3,
    title: 'Participe e vença',
    description:
      'Atue antes da concorrência com vantagem competitiva. Histórico completo para análise estratégica.',
    icon: (
      <svg
        className="w-8 h-8"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
        />
      </svg>
    ),
  },
];

export default function HowItWorks({ className = '' }: HowItWorksProps) {
  return (
    <section
      id="como-funciona"
      className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 bg-gray-50 dark:bg-gray-900/50 ${className}`}
    >
      <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 dark:text-white mb-4">
        Como funciona
      </h2>
      <p className="text-lg text-center text-gray-600 dark:text-gray-300 mb-12 max-w-2xl mx-auto">
        Processo simples e automatizado para encontrar licitações relevantes
      </p>

      <div className="grid md:grid-cols-3 gap-8 relative">
        {steps.map((step, index) => (
          <div key={index} className="relative">
            {/* Arrow (desktop only) */}
            {index < steps.length - 1 && (
              <div className="hidden md:block absolute top-12 -right-4 z-10">
                <svg
                  className="w-8 h-8 text-blue-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}

            {/* Step Card */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm h-full">
              {/* Step Number Badge */}
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mb-4">
                {step.stepNumber}
              </div>

              {/* Icon */}
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center text-blue-600 dark:text-blue-400 mb-4">
                {step.icon}
              </div>

              {/* Title */}
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                {step.title}
              </h3>

              {/* Description */}
              <p className="text-gray-600 dark:text-gray-300">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
