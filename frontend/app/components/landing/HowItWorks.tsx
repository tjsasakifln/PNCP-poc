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
    title: 'Diga o que você vende',
    description: 'Selecione seu setor de atuação e a região onde compete.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
  {
    stepNumber: 2,
    title: 'Receba curadoria inteligente',
    description: 'IA filtra, analisa e resume os editais certos para você.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    stepNumber: 3,
    title: 'Decida com confiança',
    description: 'Relatório executivo pronto. Oportunidades ranqueadas por relevância.',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
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
        Da definição do seu perfil à decisão de participar — em minutos.
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
