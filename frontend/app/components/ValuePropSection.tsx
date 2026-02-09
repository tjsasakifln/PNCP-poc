/**
 * ValuePropSection Component
 *
 * Displays 4 key differentiators with icons, metrics, and descriptions
 * Used on landing page to highlight unfair advantages (STORY-173)
 *
 * @component
 */

import { valueProps } from '@/lib/copy/valueProps';

export default function ValuePropSection() {
  const props = [
    valueProps.speed,
    valueProps.precision,
    valueProps.consolidation,
    valueProps.intelligence,
  ];

  return (
    <section className="py-20 bg-surface-0" id="value-props">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            Por Que SmartLic?
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            Enquanto outras plataformas exigem trabalho manual, o SmartLic entrega inteligência automatizada.
          </p>
        </div>

        {/* 4-Column Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {props.map((prop, index) => (
            <div
              key={index}
              className="bg-surface-1 rounded-lg p-6 border border-border hover:border-brand-blue transition-all hover:shadow-lg group"
            >
              {/* Icon */}
              <div className="text-5xl mb-4 group-hover:scale-110 transition-transform">
                {prop.icon}
              </div>

              {/* Metric */}
              <div className="text-3xl font-bold text-brand-blue mb-2">
                {prop.metric}
              </div>

              {/* Title */}
              <h3 className="text-xl font-semibold text-ink mb-3">
                {prop.title}
              </h3>

              {/* Short Description */}
              <p className="text-sm text-ink-secondary mb-4">
                {prop.shortDescription}
              </p>

              {/* Long Description */}
              <p className="text-sm text-ink-secondary leading-relaxed">
                {prop.longDescription}
              </p>

              {/* Proof Point (if exists) */}
              {prop.proof && (
                <p className="text-xs text-ink-muted mt-4 italic">
                  {prop.proof}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <a
            href="/signup?source=value-props"
            className="inline-flex items-center gap-2 bg-brand-blue text-white px-8 py-4 rounded-lg font-semibold hover:bg-brand-blue/90 transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
          >
            <span>Economize 10h/Semana Agora</span>
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
