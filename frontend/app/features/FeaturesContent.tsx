'use client';

/**
 * Features Content — Client Component
 *
 * GTM-009: Transformation narrative cards with GlassCard + gem accents.
 * Separated as client component for framer-motion animations.
 */

import { features } from '@/lib/copy/valueProps';
import { GlassCard } from '../components/ui/GlassCard';
import { XCircle, CheckCircle2, Target, ShieldCheck, Globe, Brain, Trophy } from 'lucide-react';

type GemAccent = 'sapphire' | 'emerald' | 'amethyst' | 'ruby';

interface TransformFeature {
  title: string;
  without: string;
  withSmartLic: string;
  gemAccent: GemAccent;
}

const featureIcons = [Target, ShieldCheck, Globe, Brain, Trophy];

const featuresList: TransformFeature[] = [
  features.prioritization,
  features.adequacy,
  features.nationalCoverage,
  features.decisionIntelligence,
  features.competitiveAdvantage,
];

export function FeaturesContent() {
  return (
    <section className="py-20 bg-surface-0">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-12">
          {featuresList.map((feature, index) => {
            const Icon = featureIcons[index];
            return (
              <GlassCard
                key={index}
                variant="feature"
                gemAccent={feature.gemAccent}
                hoverable={false}
              >
                {/* Feature Header */}
                <div className="flex items-start gap-3 mb-8">
                  <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-brand-blue/10 dark:bg-brand-blue/20 flex-shrink-0 mt-1">
                    <Icon className="w-5 h-5 text-brand-blue" strokeWidth={2} aria-hidden="true" />
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-ink">
                    {feature.title}
                  </h2>
                </div>

                {/* Before/After Grid */}
                <div className="grid md:grid-cols-2 gap-6 md:gap-8">
                  {/* Without SmartLic */}
                  <div className="space-y-3 p-5 rounded-2xl bg-error/5 dark:bg-error/10 border border-error/20">
                    <div className="flex items-center gap-2 text-error">
                      <XCircle className="w-5 h-5 flex-shrink-0" strokeWidth={2} aria-hidden="true" />
                      <span className="font-semibold text-sm uppercase tracking-wide">Sem SmartLic</span>
                    </div>
                    <p className="text-ink-secondary leading-relaxed">
                      {feature.without}
                    </p>
                  </div>

                  {/* With SmartLic */}
                  <div className="space-y-3 p-5 rounded-2xl bg-success/5 dark:bg-success/10 border border-success/20">
                    <div className="flex items-center gap-2 text-success">
                      <CheckCircle2 className="w-5 h-5 flex-shrink-0" strokeWidth={2} aria-hidden="true" />
                      <span className="font-semibold text-sm uppercase tracking-wide">Com SmartLic</span>
                    </div>
                    <p className="text-ink-secondary leading-relaxed">
                      {feature.withSmartLic}
                    </p>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      </div>
    </section>
  );
}
