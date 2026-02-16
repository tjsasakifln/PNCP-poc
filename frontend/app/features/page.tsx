/**
 * Features Page
 *
 * Detailed features with defensive positioning ("Outras plataformas... SmartLic...")
 * STORY-173 AC2: Features page copy rewrite
 *
 * @page
 */

import Link from 'next/link';
import { features } from '@/lib/copy/valueProps';
import Footer from '../components/Footer';

export const metadata = {
  title: 'Funcionalidades | SmartLic',
  description: 'Descubra como o SmartLic entrega inteligência de decisão para oportunidades de licitação com avaliação objetiva por IA.',
};

export default function FeaturesPage() {
  const featuresList = [
    features.sectorSearch,
    features.intelligentFiltering,
    features.multiSourceConsolidation,
    features.decisionIntelligence,
    features.competitiveAdvantage,
  ];

  return (
    <>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              Funcionalidades que Geram Vantagem Competitiva
            </h1>
            <p className="text-xl text-white/90 mb-8">
              Enquanto outras plataformas exigem trabalho manual, o SmartLic entrega inteligência automatizada.
            </p>
            <a
              href="/signup?source=features-hero"
              className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
            >
              <span>Começar Teste Grátis</span>
              <svg
              role="img"
              aria-label="Ícone"
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </a>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-surface-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-20">
            {featuresList.map((feature, index) => (
              <div
                key={index}
                className={`flex flex-col ${
                  index % 2 === 0 ? 'lg:flex-row' : 'lg:flex-row-reverse'
                } gap-12 items-center`}
              >
                {/* Feature Content */}
                <div className="flex-1">
                  <h2 className="text-3xl font-bold text-ink mb-4">
                    {feature.title}
                  </h2>

                  {/* Pain Point (Red) */}
                  <div className="bg-error/10 border-l-4 border-error p-4 mb-4 rounded">
                    <p className="text-sm font-semibold text-error mb-2">
                      ❌ Outras Plataformas:
                    </p>
                    <p className="text-sm text-ink-secondary">
                      {feature.painPoint}
                    </p>
                  </div>

                  {/* Solution (Green) */}
                  <div className="bg-success/10 border-l-4 border-success p-4 mb-6 rounded">
                    <p className="text-sm font-semibold text-success mb-2">
                      ✅ SmartLic:
                    </p>
                    <p className="text-sm text-ink-secondary">
                      {feature.solution}
                    </p>
                  </div>

                  {/* Details */}
                  <p className="text-base text-ink-secondary mb-6">
                    {feature.details}
                  </p>

                  {/* Benefits List */}
                  <div className="space-y-3">
                    <p className="font-semibold text-ink">Benefícios:</p>
                    <ul className="space-y-2">
                      {feature.benefits.map((benefit: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2">
                          <svg
              role="img"
              aria-label="Ícone"
                            className="w-5 h-5 text-success flex-shrink-0 mt-0.5"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="text-sm text-ink-secondary">
                            {benefit}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Feature Visual (Placeholder for screenshot/demo) */}
                <div className="flex-1 w-full">
                  <div className="bg-surface-1 border border-border rounded-lg p-8 min-h-[300px] flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-6xl mb-4">
                        {index === 0 && '🔍'}
                        {index === 1 && '🎯'}
                        {index === 2 && '🌍'}
                        {index === 3 && '⚡'}
                        {index === 4 && '🤖'}
                      </div>
                      <p className="text-sm text-ink-muted">
                        Demo visual / Screenshot
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison CTA */}
      <section className="py-20 bg-surface-1">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-ink mb-4">
            Veja a Comparação Completa
          </h2>
          <p className="text-lg text-ink-secondary mb-8">
            Compare SmartLic com plataformas tradicionais lado a lado
          </p>
          <Link
            href="/#comparison"
            className="inline-flex items-center gap-2 bg-brand-blue text-white px-8 py-4 rounded-lg font-semibold hover:bg-brand-blue/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            <span>Ver Tabela Comparativa</span>
            <svg
              role="img"
              aria-label="Ícone"
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </Link>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Pronto para Ganhar Mais Licitações?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Consultas gratuitas. Sem cartão de crédito. Cancele quando quiser.
          </p>
          <a
            href="/signup?source=features-bottom-cta"
            className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
          >
            <span>Começar Agora</span>
            <svg
              role="img"
              aria-label="Ícone"
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </a>
        </div>
      </section>

      <Footer />
    </>
  );
}
