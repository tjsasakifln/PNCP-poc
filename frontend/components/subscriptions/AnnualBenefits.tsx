"use client";

import { FeatureBadge, FeatureStatus } from "./FeatureBadge";
import { BillingPeriod } from "./PlanToggle";

/**
 * AnnualBenefits Component
 *
 * Displays annual subscription benefits with status badges
 * STORY-171 AC3: Exibição de Benefícios por Plano
 *
 * Features:
 * - Only shows when billingPeriod = "annual"
 * - Status badges (active, coming_soon, future)
 * - Tooltips with launch dates
 * - Special section for SmartLic Pro exclusive benefits
 */

export interface Benefit {
  key: string;
  title: string;
  description: string;
  status: FeatureStatus;
  launchDate?: string;
  planExclusive?: string; // e.g., "sala_guerra"
}

export interface AnnualBenefitsProps {
  billingPeriod: BillingPeriod;
  planId?: string; // "consultor_agil", "maquina", "sala_guerra"
  className?: string;
}

// All benefits configuration
const ALL_BENEFITS: Benefit[] = [
  {
    key: 'early_access',
    title: 'Early Access',
    description: 'Recebe novas features 2-4 semanas antes',
    status: 'active',
  },
  {
    key: 'proactive_search',
    title: 'Busca Proativa',
    description: 'Sistema busca automaticamente oportunidades do seu setor',
    status: 'coming_soon',
    launchDate: 'Março 2026',
  },
  {
    key: 'ai_edital_analysis',
    title: 'Análise IA de Editais',
    description: 'IA avalia oportunidades e gera análise estratégica',
    status: 'coming_soon',
    launchDate: 'Abril 2026',
    planExclusive: 'smartlic_pro',
  },
  {
    key: 'dashboard_executivo',
    title: 'Dashboard Executivo',
    description: 'Gráficos de tendências, heatmaps, análise de concorrência',
    status: 'future',
    planExclusive: 'smartlic_pro',
  },
  {
    key: 'alertas_multi_canal',
    title: 'Alertas Multi-Canal',
    description: 'Telegram, Email, notificações in-app e mais',
    status: 'future',
    planExclusive: 'smartlic_pro',
  },
];

export function AnnualBenefits({
  billingPeriod,
  planId,
  className = "",
}: AnnualBenefitsProps) {
  // Only show when annual billing is selected
  if (billingPeriod !== 'annual') {
    return null;
  }

  // Filter benefits based on plan
  const allPlansBenefits = ALL_BENEFITS.filter(b => !b.planExclusive);
  const proBenefits = ALL_BENEFITS.filter(b => b.planExclusive === 'smartlic_pro');
  const showProExclusive = planId === 'smartlic_pro' || planId === 'sala_guerra' || planId === 'maquina' || planId === 'consultor_agil';

  return (
    <div className={`space-y-6 ${className}`} data-testid="annual-benefits">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold font-display text-ink mb-2">
          Benefícios Exclusivos do Plano Anual
        </h3>
        <p className="text-ink-secondary">
          Aproveite recursos avançados disponíveis apenas para assinantes anuais
        </p>
      </div>

      {/* All Plans Benefits */}
      <div className="bg-surface-1 rounded-card p-6 border">
        <h4 className="text-lg font-semibold text-ink mb-4 flex items-center gap-2">
          <span aria-hidden="true">🎁</span>
          Benefícios para Todos os Planos Anuais
        </h4>
        <ul className="space-y-4">
          {allPlansBenefits.map((benefit) => (
            <li key={benefit.key} className="flex items-start gap-3">
              <FeatureBadge
                status={benefit.status}
                launchDate={benefit.launchDate}
              />
              <div className="flex-1">
                <p className="font-semibold text-ink">{benefit.title}</p>
                <p className="text-sm text-ink-secondary mt-0.5">{benefit.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* SmartLic Pro Exclusive Benefits */}
      {showProExclusive && proBenefits.length > 0 && (
        <div className="bg-gradient-to-br from-brand-blue-subtle to-surface-1 rounded-card p-6 border-2 border-brand-blue">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-2xl" aria-hidden="true">👑</span>
            <h4 className="text-lg font-semibold text-brand-navy">
              Exclusivo SmartLic Pro
            </h4>
          </div>
          <ul className="space-y-4">
            {proBenefits.map((benefit) => (
              <li key={benefit.key} className="flex items-start gap-3">
                <FeatureBadge
                  status={benefit.status}
                  launchDate={benefit.launchDate}
                />
                <div className="flex-1">
                  <p className="font-semibold text-ink">{benefit.title}</p>
                  <p className="text-sm text-ink-secondary mt-0.5">{benefit.description}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Early Adopter Message */}
      <div className="bg-surface-0 rounded-card p-4 border border-brand-blue-subtle">
        <p className="text-sm text-ink-secondary text-center">
          <span className="font-semibold text-brand-navy">Como early adopter</span>, você será notificado por email assim que
          essas features forem lançadas. Obrigado por acreditar em nós! 🚀
        </p>
      </div>
    </div>
  );
}
