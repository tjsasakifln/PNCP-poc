/**
 * Pricing Page with ROI Calculator
 *
 * GTM-002: Single plan model — SmartLic Pro R$1.999/mês
 * ROI calculator justifies SmartLic cost vs. manual search time cost
 *
 * @page
 */

'use client';

import { useState, useEffect } from 'react';
import { pricing } from '@/lib/copy/valueProps';
import {
  calculateROI,
  DEFAULT_VALUES,
  formatCurrency,
  getROIMessage,
  type ROIInputs,
} from '@/lib/copy/roi';
import Footer from '../components/Footer';

const SMARTLIC_PRO_PRICE = 1999;

export default function PricingPage() {
  const [hoursPerWeek, setHoursPerWeek] = useState(DEFAULT_VALUES.hoursPerWeek);
  const [costPerHour, setCostPerHour] = useState(DEFAULT_VALUES.costPerHour);

  const [roiResult, setRoiResult] = useState(
    calculateROI({
      hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
      costPerHour: DEFAULT_VALUES.costPerHour,
      planPrice: SMARTLIC_PRO_PRICE,
    })
  );

  useEffect(() => {
    const inputs: ROIInputs = {
      hoursPerWeek,
      costPerHour,
      planPrice: SMARTLIC_PRO_PRICE,
    };
    setRoiResult(calculateROI(inputs));
  }, [hoursPerWeek, costPerHour]);

  const roiMessage = getROIMessage({
    hoursPerWeek,
    costPerHour,
    planPrice: SMARTLIC_PRO_PRICE,
  });

  return (
    <>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-brand-blue to-brand-blue/80 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl sm:text-5xl font-bold mb-6">
              {pricing.headline}
            </h1>
            <p className="text-xl text-white/90">
              {pricing.subheadline}
            </p>
          </div>
        </div>
      </section>

      {/* ROI Calculator Section */}
      <section className="py-20 bg-surface-0">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-card p-8">
            <h2 className="text-3xl font-bold text-[var(--ink)] mb-2 text-center">
              {pricing.roi.headline}
            </h2>
            <p className="text-center text-[var(--ink-secondary)] mb-8">
              Calcule quanto você economiza com o SmartLic Pro
            </p>

            {/* Calculator Inputs */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div>
                <label
                  htmlFor="hours-per-week"
                  className="block text-sm font-medium text-[var(--ink)] mb-2"
                >
                  Horas gastas por semana em processos manuais
                </label>
                <input
                  id="hours-per-week"
                  type="number"
                  min="1"
                  max="168"
                  value={hoursPerWeek}
                  onChange={(e) => setHoursPerWeek(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[var(--surface-0)] border border-[var(--border)] rounded-button text-[var(--ink)] focus:outline-none focus:ring-2 focus:ring-brand-blue"
                />
              </div>

              <div>
                <label
                  htmlFor="cost-per-hour"
                  className="block text-sm font-medium text-[var(--ink)] mb-2"
                >
                  Custo/hora do seu tempo (R$)
                </label>
                <input
                  id="cost-per-hour"
                  type="number"
                  min="1"
                  max="10000"
                  value={costPerHour}
                  onChange={(e) => setCostPerHour(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-[var(--surface-0)] border border-[var(--border)] rounded-button text-[var(--ink)] focus:outline-none focus:ring-2 focus:ring-brand-blue"
                />
              </div>
            </div>

            {/* SmartLic Pro Price Reference */}
            <div className="text-center mb-8 p-4 bg-brand-navy/5 border border-brand-navy/20 rounded-card">
              <p className="text-sm text-[var(--ink-secondary)] mb-1">SmartLic Pro</p>
              <p className="text-2xl font-bold text-brand-navy">
                {formatCurrency(SMARTLIC_PRO_PRICE)}<span className="text-sm font-normal text-[var(--ink-muted)]">/mês</span>
              </p>
              <p className="text-xs text-[var(--ink-muted)] mt-1">
                A partir de {formatCurrency(1599)}/mês no compromisso anual
              </p>
            </div>

            {/* Divider */}
            <div className="border-t border-border my-8"></div>

            {/* ROI Results */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-[var(--error)]/10 border border-[var(--error)]/30 rounded-card p-6">
                <p className="text-sm text-[var(--ink-secondary)] mb-1">
                  Custo Mensal do Processo Manual
                </p>
                <p className="text-3xl font-bold text-error">
                  {roiResult.formatted.manualSearchCostPerMonth}
                </p>
                <p className="text-xs text-[var(--ink-muted)] mt-2">
                  {hoursPerWeek}h/semana x {formatCurrency(costPerHour)}/h x 4 semanas
                </p>
              </div>

              <div className="bg-[var(--success)]/10 border border-[var(--success)]/30 rounded-card p-6">
                <p className="text-sm text-[var(--ink-secondary)] mb-1">
                  SmartLic Pro
                </p>
                <p className="text-3xl font-bold text-success">
                  {roiResult.formatted.smartlicPlanCost}
                </p>
                <p className="text-xs text-[var(--ink-muted)] mt-2">
                  Fixo mensal, sem taxas ocultas
                </p>
              </div>
            </div>

            <div className="bg-[var(--brand-blue)]/10 border border-[var(--brand-blue)]/30 rounded-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-[var(--ink-secondary)] mb-1">
                    Economia Mensal
                  </p>
                  <p className="text-4xl font-bold text-brand-blue">
                    {roiResult.formatted.monthlySavings}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-[var(--ink-secondary)] mb-1">ROI</p>
                  <p className="text-4xl font-bold text-brand-blue">
                    {roiResult.formatted.roi}
                  </p>
                </div>
              </div>
              <div className="border-t border-brand-blue/20 pt-4">
                <p className="font-semibold text-[var(--ink)] mb-2">{roiMessage.headline}</p>
                <p className="text-sm text-[var(--ink-secondary)]">{roiMessage.explanation}</p>
              </div>
            </div>

            <p className="text-center text-lg font-semibold text-success mt-6">
              {pricing.roi.tagline}
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Comparison Table */}
      <section className="py-20 bg-surface-1">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-[var(--ink)] mb-8 text-center">
            SmartLic vs Plataformas Tradicionais
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full bg-surface-0 rounded-lg overflow-hidden shadow-lg">
              <thead className="bg-surface-2">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-[var(--ink)]">
                    Aspecto
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-[var(--ink)]">
                    Plataformas Tradicionais
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-brand-blue">
                    SmartLic
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className="px-6 py-4 font-medium text-[var(--ink)]">Modelo de Valor</td>
                  <td className="px-6 py-4 text-sm text-[var(--ink-secondary)]">
                    {pricing.comparison.pricingModel.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.pricingModel.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-[var(--ink)]">Taxas Ocultas</td>
                  <td className="px-6 py-4 text-sm text-error">
                    {pricing.comparison.hiddenFees.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.hiddenFees.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-[var(--ink)]">Cancelamento</td>
                  <td className="px-6 py-4 text-sm text-error">
                    {pricing.comparison.cancellation.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.cancellation.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-[var(--ink)]">Garantia</td>
                  <td className="px-6 py-4 text-sm text-[var(--ink-secondary)]">
                    {pricing.comparison.guarantee.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.guarantee.smartlic}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Guarantee Section */}
      <section className="py-20 bg-surface-0">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="bg-[var(--success)]/10 border border-[var(--success)]/30 rounded-card p-8">
            <h2 className="text-3xl font-bold text-[var(--ink)] mb-4">
              {pricing.guarantee.headline}
            </h2>
            <p className="text-lg text-[var(--ink-secondary)] mb-6">
              {pricing.guarantee.description}
            </p>
            <a
              href="/planos?source=pricing-guarantee"
              className="inline-flex items-center gap-2 bg-success text-white px-8 py-4 rounded-lg font-semibold hover:bg-success/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
            >
              <span>Ativar SmartLic Pro</span>
              <svg
                role="img"
                aria-label="Seta"
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

      {/* Transparency Statement */}
      <section className="py-20 bg-surface-1">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-lg text-[var(--ink-secondary)]">
            {pricing.transparency}
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
