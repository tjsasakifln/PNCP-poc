/**
 * Pricing Page with ROI Calculator
 *
 * STORY-173 AC4: Pricing page with ROI calculator and comparison table
 * Justifies SmartLic cost vs. manual search time cost
 *
 * @page
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { pricing } from '@/lib/copy/valueProps';
import {
  calculateROI,
  DEFAULT_VALUES,
  formatCurrency,
  getROIMessage,
  type ROIInputs,
} from '@/lib/copy/roi';
import Footer from '../components/Footer';

export default function PricingPage() {
  // ROI Calculator State
  const [hoursPerWeek, setHoursPerWeek] = useState(DEFAULT_VALUES.hoursPerWeek);
  const [costPerHour, setCostPerHour] = useState(DEFAULT_VALUES.costPerHour);
  const [selectedPlan, setSelectedPlan] = useState<'starter' | 'professional' | 'enterprise'>('starter');

  // Calculate ROI on input change
  const [roiResult, setRoiResult] = useState(
    calculateROI({
      hoursPerWeek: DEFAULT_VALUES.hoursPerWeek,
      costPerHour: DEFAULT_VALUES.costPerHour,
      smartlicPlan: 'starter',
    })
  );

  useEffect(() => {
    const inputs: ROIInputs = {
      hoursPerWeek,
      costPerHour,
      smartlicPlan: selectedPlan,
    };
    setRoiResult(calculateROI(inputs));
  }, [hoursPerWeek, costPerHour, selectedPlan]);

  const roiMessage = getROIMessage({
    hoursPerWeek,
    costPerHour,
    smartlicPlan: selectedPlan,
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
          <div className="bg-surface-1 border border-border rounded-lg p-8">
            <h2 className="text-3xl font-bold text-ink mb-2 text-center">
              {pricing.roi.headline}
            </h2>
            <p className="text-center text-ink-secondary mb-8">
              Calcule quanto você economiza com o SmartLic vs. busca manual
            </p>

            {/* Calculator Inputs */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Hours per Week Input */}
              <div>
                <label
                  htmlFor="hours-per-week"
                  className="block text-sm font-medium text-ink mb-2"
                >
                  Horas gastas por semana em buscas manuais
                </label>
                <input
                  id="hours-per-week"
                  type="number"
                  min="1"
                  max="168"
                  value={hoursPerWeek}
                  onChange={(e) => setHoursPerWeek(Number(e.target.value))}
                  className="w-full px-4 py-3 bg-surface-0 border border-border rounded-lg text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue"
                />
              </div>

              {/* Cost per Hour Input */}
              <div>
                <label
                  htmlFor="cost-per-hour"
                  className="block text-sm font-medium text-ink mb-2"
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
                  className="w-full px-4 py-3 bg-surface-0 border border-border rounded-lg text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue"
                />
              </div>
            </div>

            {/* Plan Selector */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-ink mb-3">
                Selecione o plano SmartLic
              </label>
              <div className="grid md:grid-cols-3 gap-4">
                {(['starter', 'professional', 'enterprise'] as const).map((plan) => (
                  <button
                    key={plan}
                    onClick={() => setSelectedPlan(plan)}
                    className={`px-6 py-4 rounded-lg border-2 transition-all ${
                      selectedPlan === plan
                        ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                        : 'border-border bg-surface-0 text-ink hover:border-brand-blue/50'
                    }`}
                  >
                    <div className="font-semibold capitalize mb-1">
                      {plan === 'starter' && 'Starter'}
                      {plan === 'professional' && 'Professional'}
                      {plan === 'enterprise' && 'Enterprise'}
                    </div>
                    <div className="text-2xl font-bold mb-1">
                      {formatCurrency(DEFAULT_VALUES.plans[plan])}
                    </div>
                    <div className="text-xs text-ink-secondary">
                      {plan === 'starter' && 'até 50 buscas/mês'}
                      {plan === 'professional' && 'até 300 buscas/mês'}
                      {plan === 'enterprise' && 'até 1.000 buscas/mês'}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-border my-8"></div>

            {/* ROI Results */}
            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-error/10 border border-error/30 rounded-lg p-6">
                <p className="text-sm text-ink-secondary mb-1">
                  💸 Custo Mensal da Busca Manual
                </p>
                <p className="text-3xl font-bold text-error">
                  {roiResult.formatted.manualSearchCostPerMonth}
                </p>
                <p className="text-xs text-ink-muted mt-2">
                  {hoursPerWeek}h/semana × {formatCurrency(costPerHour)}/h × 4 semanas
                </p>
              </div>

              <div className="bg-success/10 border border-success/30 rounded-lg p-6">
                <p className="text-sm text-ink-secondary mb-1">
                  💸 Plano SmartLic
                </p>
                <p className="text-3xl font-bold text-success">
                  {roiResult.formatted.smartlicPlanCost}
                </p>
                <p className="text-xs text-ink-muted mt-2">
                  Fixo mensal, sem taxas ocultas
                </p>
              </div>
            </div>

            <div className="bg-brand-blue/10 border border-brand-blue/30 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm text-ink-secondary mb-1">
                    ✅ Economia Mensal
                  </p>
                  <p className="text-4xl font-bold text-brand-blue">
                    {roiResult.formatted.monthlySavings}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-ink-secondary mb-1">📊 ROI</p>
                  <p className="text-4xl font-bold text-brand-blue">
                    {roiResult.formatted.roi}
                  </p>
                </div>
              </div>
              <div className="border-t border-brand-blue/20 pt-4">
                <p className="font-semibold text-ink mb-2">{roiMessage.headline}</p>
                <p className="text-sm text-ink-secondary">{roiMessage.explanation}</p>
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
          <h2 className="text-3xl font-bold text-ink mb-8 text-center">
            SmartLic vs Plataformas Tradicionais
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full bg-surface-0 rounded-lg overflow-hidden shadow-lg">
              <thead className="bg-surface-2">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-ink">
                    Aspecto
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-ink">
                    Plataformas Tradicionais
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-brand-blue">
                    SmartLic
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className="px-6 py-4 font-medium text-ink">Modelo de Preço</td>
                  <td className="px-6 py-4 text-sm text-ink-secondary">
                    {pricing.comparison.pricingModel.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.pricingModel.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-ink">Taxas Ocultas</td>
                  <td className="px-6 py-4 text-sm text-error">
                    {pricing.comparison.hiddenFees.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.hiddenFees.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-ink">Cancelamento</td>
                  <td className="px-6 py-4 text-sm text-error">
                    {pricing.comparison.cancellation.traditional}
                  </td>
                  <td className="px-6 py-4 text-sm text-success font-medium">
                    {pricing.comparison.cancellation.smartlic}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 font-medium text-ink">Garantia</td>
                  <td className="px-6 py-4 text-sm text-ink-secondary">
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
          <div className="bg-success/10 border border-success/30 rounded-lg p-8">
            <h2 className="text-3xl font-bold text-ink mb-4">
              {pricing.guarantee.headline}
            </h2>
            <p className="text-lg text-ink-secondary mb-6">
              {pricing.guarantee.description}
            </p>
            <a
              href="/signup?source=pricing-guarantee"
              className="inline-flex items-center gap-2 bg-success text-white px-8 py-4 rounded-lg font-semibold hover:bg-success/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
            >
              <span>Começar Teste Grátis de 7 Dias</span>
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

      {/* Transparency Statement */}
      <section className="py-20 bg-surface-1">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-lg text-ink-secondary">
            {pricing.transparency}
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
