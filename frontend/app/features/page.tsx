/**
 * Features Page — Transformation Narratives
 *
 * GTM-009: Complete rewrite from task-based to transformation-based copy.
 * Each feature uses "Sem SmartLic" → "Com SmartLic" structure.
 *
 * Aligned with: GTM-007 (no PNCP), GTM-008 (IA as decision intelligence),
 * GTM-002 (SmartLic Pro), GTM-003 (7-day full product trial)
 *
 * @page
 */

import Footer from '../components/Footer';
import { FeaturesContent } from './FeaturesContent';


export const metadata = {
  title: 'O Que Muda no Seu Resultado | SmartLic',
  description: 'Compare os cenários: sem SmartLic vs com SmartLic. Descubra como transformar sua forma de encontrar, avaliar e decidir em quais licitações investir.',
};

export default function FeaturesPage() {
  return (
    <>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              O Que Muda no Seu Resultado
            </h1>
            <p className="text-xl text-white/90 mb-8">
              SmartLic não é sobre fazer tarefas mais rápido. É sobre transformar como você encontra, avalia e decide em quais licitações investir tempo. Compare os cenários:
            </p>
            <a
              href="/signup?source=features-hero"
              className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
            >
              <span>Experimentar SmartLic Pro</span>
              <svg
                role="img"
                aria-label="Seta para direita"
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

      {/* Transformation Features (Client Component for GlassCard animations) */}
      <FeaturesContent />

      {/* Final CTA */}
      <section className="py-20 bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Começar a Ganhar Mais Licitações
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Experimente o SmartLic completo por 7 dias. Sem versão limitada. Se uma única licitação ganha pagar o sistema por um ano inteiro, por que esperar?
          </p>
          <a
            href="/signup?source=features-bottom-cta"
            className="inline-flex items-center gap-2 bg-white text-brand-blue px-8 py-4 rounded-lg font-semibold hover:bg-white/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-brand-blue"
          >
            <span>Experimentar SmartLic Pro</span>
            <svg
              role="img"
              aria-label="Seta para direita"
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
