'use client';

import { motion } from 'framer-motion';
import { GlassCard } from './ui/GlassCard';
import { BentoGrid, BentoGridItem } from './ui/BentoGrid';
import { GradientButton } from './ui/GradientButton';
import { useScrollAnimation, fadeInUp, staggerContainer } from '@/lib/animations';
import { valueProps } from '@/lib/copy/valueProps';

/**
 * STORY-174 AC2: Value Props Section - Bento Grid with Glassmorphism
 *
 * Features:
 * - Asymmetric bento grid layout (different card sizes for hierarchy)
 * - Glassmorphism cards with backdrop-blur
 * - Hover animations (lift + shadow intensify)
 * - Custom SVG icons with gradient fills
 * - Scroll-triggered staggered entrance
 */
export default function ValuePropSection() {
  const { ref, isVisible } = useScrollAnimation(0.1);

  const props = [
    { ...valueProps.speed, size: 'large' as const },        // 2x2
    { ...valueProps.precision, size: 'medium' as const },   // 2x1
    { ...valueProps.intelligence, size: 'medium' as const }, // 2x1
    { ...valueProps.consolidation, size: 'wide' as const },  // 3x1 (full width)
  ];

  return (
    <section ref={ref} className="py-20 bg-surface-0" id="value-props">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-16"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            Por Que SmartLic?
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            Enquanto outras plataformas exigem trabalho manual, o SmartLic entrega inteligência automatizada.
          </p>
        </motion.div>

        {/* Bento Grid with Glassmorphism Cards */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <BentoGrid variant="default">
            {props.map((prop, index) => (
              <BentoGridItem key={index} size={prop.size}>
                <motion.div variants={fadeInUp}>
                  <GlassCard hoverable={true} variant="default" className="h-full">
                    {/* Icon with gradient */}
                    <div className="mb-4 transform transition-transform group-hover:scale-110">
                      <prop.icon
                        className="w-12 h-12 text-brand-blue"
                        strokeWidth={2}
                        aria-label={prop.title}
                        role="img"
                      />
                    </div>

                    {/* Metric */}
                    <div className="text-3xl sm:text-4xl font-bold text-gradient mb-2">
                      {prop.metric}
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-semibold text-ink mb-3">
                      {prop.title}
                    </h3>

                    {/* Short Description */}
                    <p className="text-sm text-ink-secondary mb-4 font-medium">
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
                  </GlassCard>
                </motion.div>
              </BentoGridItem>
            ))}
          </BentoGrid>
        </motion.div>

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
            onClick={() => window.location.href = '/signup?source=value-props'}
          >
            Economize 10h/Semana Agora
            <svg
              className="w-5 h-5 ml-2"
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
          </GradientButton>
        </motion.div>
      </div>
    </section>
  );
}
