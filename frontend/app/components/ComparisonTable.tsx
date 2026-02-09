/**
 * ComparisonTable Component
 *
 * Visual comparison: SmartLic vs. Traditional Platforms
 * Based on validated market pain points (STORY-173)
 *
 * @component
 */

import { comparisonTable } from '@/lib/copy/comparisons';

export default function ComparisonTable() {
  return (
    <section className="py-20 bg-surface-1" id="comparison">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            SmartLic vs Plataformas Tradicionais
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            Baseado em reclamações reais de usuários do mercado
          </p>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto">
          <table className="w-full bg-surface-0 rounded-lg overflow-hidden shadow-lg">
            {/* Table Header */}
            <thead className="bg-surface-2">
              <tr>
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

            {/* Table Body */}
            <tbody className="divide-y divide-border">
              {comparisonTable.map((row, index) => (
                <tr
                  key={index}
                  className="hover:bg-surface-1 transition-colors"
                >
                  {/* Feature Column */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {row.icon && (
                        <span className="text-2xl">{row.icon}</span>
                      )}
                      <span className="font-medium text-ink">
                        {row.feature}
                      </span>
                    </div>
                  </td>

                  {/* Traditional Platforms Column */}
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-2">
                      <span className="text-error mt-0.5">❌</span>
                      <span className="text-sm text-ink-secondary">
                        {row.traditional}
                      </span>
                    </div>
                  </td>

                  {/* SmartLic Column */}
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-2">
                      <span className="text-success mt-0.5">✅</span>
                      <div>
                        <p className="text-sm text-ink font-medium">
                          {row.smartlic}
                        </p>
                        {row.advantage && (
                          <p className="text-xs text-brand-blue mt-1">
                            {row.advantage}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-ink-muted text-center mt-6 italic">
          *Dados baseados em pesquisa de mercado (Reclame AQUI, estudos acadêmicos, análise de plataformas tradicionais, 2025-2026)
        </p>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <a
            href="/signup?source=comparison-table"
            className="inline-flex items-center gap-2 bg-success text-white px-8 py-4 rounded-lg font-semibold hover:bg-success/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            <span>Começar Teste Grátis de 7 Dias</span>
            <svg
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
  );
}
