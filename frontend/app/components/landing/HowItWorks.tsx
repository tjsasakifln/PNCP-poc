'use client';

import { useInView } from '@/app/hooks/useInView';

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
    description: 'Estado, setor, faixa de valor e palavras-chave.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
      </svg>
    ),
  },
  {
    stepNumber: 2,
    title: 'Receba resultados',
    description: 'Buscas automáticas com resumos IA.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
  },
  {
    stepNumber: 3,
    title: 'Baixe e atue',
    description: 'Excel pronto. Histórico completo.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
  },
];

export default function HowItWorks({ className = '' }: HowItWorksProps) {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section
      id="como-funciona"
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 bg-surface-1 ${className}`}
    >
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-4 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Como funciona
      </h2>
      <p
        className={`text-lg text-center text-ink-secondary mb-12 max-w-2xl mx-auto transition-all duration-500 delay-100 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Três passos. Resultado em minutos.
      </p>

      <div className="grid md:grid-cols-3 gap-8 relative">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`relative transition-all duration-500 ${
              isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{ transitionDelay: `${150 + index * 100}ms` }}
          >
            {/* Connector line (desktop only) */}
            {index < steps.length - 1 && (
              <div className="hidden md:block absolute top-8 left-[calc(50%+24px)] w-[calc(100%-48px)] h-0.5 bg-[var(--border)]" />
            )}

            {/* Step Card */}
            <div className="bg-surface-0 p-6 rounded-card border border-[var(--border)] hover:-translate-y-0.5 hover:shadow-md transition-all h-full">
              {/* Step Number Badge */}
              <div className="w-12 h-12 bg-brand-navy text-white rounded-full flex items-center justify-center text-lg font-bold mb-4 relative z-10">
                {step.stepNumber}
              </div>

              {/* Icon */}
              <div className="w-10 h-10 bg-brand-blue-subtle rounded-button flex items-center justify-center text-brand-blue mb-4">
                {step.icon}
              </div>

              {/* Title */}
              <h3 className="text-lg font-bold text-ink mb-2">{step.title}</h3>

              {/* Description */}
              <p className="text-sm text-ink-secondary">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
