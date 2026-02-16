'use client';

import { motion } from 'framer-motion';
import { useScrollAnimation, fadeInUp, staggerContainer, scaleIn } from '@/lib/animations';
import { comparisonTable } from '@/lib/copy/comparisons';
import { GradientButton } from './ui/GradientButton';

/**
 * STORY-174 AC3: Comparison Table - Premium Styling
 *
 * Features:
 * - Sticky header on scroll (CSS position: sticky)
 * - Gradient borders on header row
 * - Animated checkmarks/X marks (Framer Motion scale-in)
 * - Hover: entire row highlights (background transition)
 * - Mobile: Responsive card-based layout
 * - Staggered row entrance animations
 */
export default function ComparisonTable() {
  const { ref, isVisible } = useScrollAnimation(0.1);

  return (
    <section ref={ref} className="py-20 bg-surface-1" id="comparison">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-12"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            SmartLic vs Plataformas Tradicionais
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            Baseado em reclamações reais de usuários do mercado
          </p>
        </motion.div>

        {/* Desktop: Premium Table */}
        <div className="hidden md:block overflow-x-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate={isVisible ? 'visible' : 'hidden'}
          >
            <table className="w-full bg-surface-0 rounded-lg overflow-hidden shadow-xl">
              {/* Sticky Header with Gradient Border */}
              <thead className="bg-surface-2 sticky top-0 z-10">
                <tr className="border-b-2 border-brand-blue">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-ink">
                    Funcionalidade
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-ink">
                    Plataformas Tradicionais
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-brand-blue">
                    SmartLic
                  </th>
                </tr>
              </thead>

              {/* Table Body with Row Animations */}
              <tbody className="divide-y divide-border">
                {comparisonTable.map((row, index) => (
                  <motion.tr
                    key={index}
                    className="
                      hover:bg-surface-1
                      transition-colors
                      duration-200
                    "
                    variants={fadeInUp}
                    custom={index}
                  >
                    {/* Feature Column */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {row.icon && (
                          <row.icon
                            className="w-5 h-5 text-brand-blue flex-shrink-0"
                            strokeWidth={2}
                            aria-label={row.feature}
                            role="img"
                          />
                        )}
                        <span className="font-medium text-ink">
                          {row.feature}
                        </span>
                      </div>
                    </td>

                    {/* Traditional Platforms Column */}
                    <td className="px-6 py-4">
                      <div className="flex items-start gap-2">
                        <motion.span
                          className="text-error mt-0.5 text-xl"
                          variants={scaleIn}
                          transition={{ delay: index * 0.1 }}
                        >
                          ❌
                        </motion.span>
                        <span className="text-sm text-ink-secondary">
                          {row.traditional}
                        </span>
                      </div>
                    </td>

                    {/* SmartLic Column */}
                    <td className="px-6 py-4">
                      <div className="flex items-start gap-2">
                        <motion.span
                          className="text-success mt-0.5 text-xl"
                          variants={scaleIn}
                          transition={{ delay: index * 0.1 + 0.05 }}
                        >
                          ✅
                        </motion.span>
                        <div>
                          <p className="text-sm text-ink font-medium">
                            {row.smartlic}
                          </p>
                          {row.advantage && (
                            <p className="text-xs text-brand-blue mt-1 font-semibold">
                              {row.advantage}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        </div>

        {/* Mobile: Card-based Layout */}
        <div className="md:hidden space-y-4">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate={isVisible ? 'visible' : 'hidden'}
          >
            {comparisonTable.map((row, index) => (
              <motion.div
                key={index}
                className="bg-surface-0 rounded-lg p-6 shadow-md border border-border"
                variants={fadeInUp}
              >
                {/* Feature */}
                <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                  {row.icon && (
                    <row.icon
                      className="w-6 h-6 text-brand-blue flex-shrink-0"
                      strokeWidth={2}
                      aria-label={row.feature}
                      role="img"
                    />
                  )}
                  <h3 className="font-semibold text-ink">{row.feature}</h3>
                </div>

                {/* Traditional */}
                <div className="mb-4">
                  <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">
                    Plataformas Tradicionais
                  </p>
                  <div className="flex items-start gap-2">
                    <span className="text-error">❌</span>
                    <span className="text-sm text-ink-secondary">
                      {row.traditional}
                    </span>
                  </div>
                </div>

                {/* SmartLic */}
                <div>
                  <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">
                    SmartLic
                  </p>
                  <div className="flex items-start gap-2">
                    <span className="text-success">✅</span>
                    <div>
                      <p className="text-sm text-ink font-medium">
                        {row.smartlic}
                      </p>
                      {row.advantage && (
                        <p className="text-xs text-brand-blue mt-1 font-semibold">
                          {row.advantage}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Disclaimer */}
        <motion.p
          className="text-xs text-ink-muted text-center mt-6 italic"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          *Dados baseados em pesquisa de mercado (Reclame AQUI, estudos acadêmicos, análise de plataformas tradicionais, 2025-2026)
        </motion.p>

        {/* Bottom CTA */}
        <motion.div
          className="text-center mt-12"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <GradientButton
            variant="primary"
            size="lg"
            glow={true}
            onClick={() => window.location.href = '/signup?source=comparison-table'}
          >
            Experimentar o Produto Completo
            <svg
              role="img"
              aria-label="Ícone"
              className="w-5 h-5 ml-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7l5 5m0 0l-5 5m5-5H6"
              />
            </svg>
          </GradientButton>
        </motion.div>
      </div>
    </section>
  );
}
