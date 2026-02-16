'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { CategoryBadge } from '../ui/CategoryBadge';
import { ScoreBar } from '../ui/ScoreBar';
import { useScrollAnimation, fadeInUp } from '@/lib/animations';
import {
  ANALYSIS_EXAMPLES,
  SECTION_COPY,
  DECISION_META,
  formatCurrency,
  type AnalysisExample,
} from '@/lib/data/analysisExamples';

// ============================================================================
// ANALYSIS CARD
// ============================================================================

function AnalysisCard({ example }: { example: AnalysisExample }) {
  const decisionMeta = DECISION_META[example.decision.type];

  return (
    <GlassCard hoverable={false} variant="default" className="h-full flex flex-col">
      {/* Header: Category + UF + Value */}
      <div className="flex items-start justify-between mb-3">
        <CategoryBadge category={example.category} />
        <span className="text-xs font-medium text-ink-muted">
          {example.uf}
        </span>
      </div>

      <h3 className="text-base font-bold text-ink mb-1 line-clamp-2 leading-tight">
        {example.title}
      </h3>

      <p className="text-lg font-bold text-brand-blue mb-4">
        {formatCurrency(example.value)}
      </p>

      {/* Analysis Section */}
      <div className="space-y-2 mb-4 flex-1">
        <p className="text-xs font-semibold text-ink-secondary uppercase tracking-wider">
          Analise SmartLic
        </p>
        <div className="space-y-1.5 text-sm text-ink-secondary">
          <div className="flex gap-2">
            <span className="text-ink-muted flex-shrink-0">Prazo:</span>
            <span>{example.analysis.timeline}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-ink-muted flex-shrink-0">Requisitos:</span>
            <span className="line-clamp-2">{example.analysis.requirements}</span>
          </div>
          <div className="flex gap-2">
            <span className="text-ink-muted flex-shrink-0">Concorrencia:</span>
            <span>{example.analysis.competitiveness}</span>
          </div>
        </div>

        {/* Score */}
        <div className="pt-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-ink-muted">Compatibilidade</span>
          </div>
          <ScoreBar score={example.analysis.score} />
        </div>
      </div>

      {/* Decision Section */}
      <div
        className={`
          rounded-xl p-3
          ${decisionMeta.bgColor} ${decisionMeta.darkBgColor}
          border border-current/5
        `}
      >
        <p className={`text-xs font-bold mb-1 ${decisionMeta.color} ${decisionMeta.darkColor}`}>
          {decisionMeta.label}
        </p>
        <p className="text-sm text-ink-secondary leading-snug line-clamp-3">
          {example.decision.justification}
        </p>
      </div>
    </GlassCard>
  );
}

// ============================================================================
// FLOW INDICATOR
// ============================================================================

function FlowIndicator() {
  return (
    <div className="flex items-center justify-center gap-2 sm:gap-3 mb-8">
      {SECTION_COPY.flow.map((step, i) => (
        <div key={step} className="flex items-center gap-2 sm:gap-3">
          <span
            className={`
              text-xs sm:text-sm font-medium px-3 py-1.5 rounded-full
              ${i === 0 ? 'bg-surface-1 text-ink-secondary' : ''}
              ${i === 1 ? 'bg-brand-blue-subtle text-brand-blue font-semibold' : ''}
              ${i === 2 ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 font-semibold' : ''}
            `}
          >
            {step}
          </span>
          {i < SECTION_COPY.flow.length - 1 && (
            <svg
              className="w-4 h-4 text-ink-faint flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          )}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN CAROUSEL
// ============================================================================

/**
 * GTM-005: Analysis Examples Carousel
 *
 * Replaces TestimonialsCarousel with real analysis examples.
 *
 * Features:
 * - 5 curated real examples (AC1, AC11)
 * - Structured analysis cards (AC2)
 * - Narrative flow: Procurement -> Analysis -> Decision (AC3)
 * - Actionable decisions with justification (AC4)
 * - Auto-scroll 5s with pause on hover (AC7)
 * - Dot navigation (AC8)
 * - Responsive: 1 card mobile, 3 cards desktop (AC9)
 * - Glass morphism design (AC10)
 */
export default function AnalysisExamplesCarousel() {
  const { ref, isVisible } = useScrollAnimation(0.1);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  const examples = ANALYSIS_EXAMPLES;
  const visibleCount = isMobile ? 1 : 3;
  const maxIndex = examples.length - visibleCount;

  // Responsive breakpoint detection
  useEffect(() => {
    const mql = window.matchMedia('(max-width: 767px)');
    setIsMobile(mql.matches);

    const handler = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
      setCurrentIndex(0);
    };
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  // Auto-scroll every 5 seconds
  const advance = useCallback(() => {
    setCurrentIndex((prev) => (prev >= maxIndex ? 0 : prev + 1));
  }, [maxIndex]);

  useEffect(() => {
    if (isPaused || !isVisible) return;

    const interval = setInterval(advance, 5000);
    return () => clearInterval(interval);
  }, [isPaused, isVisible, advance]);

  // Dot count = scrollable positions
  const dotCount = maxIndex + 1;

  // Track dimensions: each card is 1/N of container visible
  const trackWidthPercent = (examples.length / visibleCount) * 100;
  const stepPercent = 100 / examples.length;

  return (
    <section
      ref={ref}
      className="py-20 bg-surface-0"
      id="analysis-examples"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-6"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            {SECTION_COPY.title}
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto mb-6">
            {SECTION_COPY.subtitle}
          </p>
        </motion.div>

        {/* Flow: Licitacao Real -> Analise -> Decisao */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <FlowIndicator />
        </motion.div>

        {/* Carousel Track */}
        <div className="overflow-hidden">
          <motion.div
            className="flex"
            style={{ width: `${trackWidthPercent}%` }}
            animate={{ x: `-${currentIndex * stepPercent}%` }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            {examples.map((example) => (
              <div
                key={example.id}
                className="px-2 sm:px-3"
                style={{ width: `${100 / examples.length}%` }}
              >
                <AnalysisCard example={example} />
              </div>
            ))}
          </motion.div>
        </div>

        {/* Dot Navigation */}
        <div className="flex justify-center gap-2 mt-8">
          {Array.from({ length: dotCount }, (_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className={`
                h-3
                rounded-full
                transition-all
                duration-300
                ${index === currentIndex
                  ? 'bg-brand-blue w-8'
                  : 'bg-ink-faint hover:bg-brand-blue/50 w-3'
                }
              `}
              aria-label={`Ver exemplo ${index + 1}`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
