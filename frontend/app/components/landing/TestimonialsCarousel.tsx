'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import { useScrollAnimation, fadeInUp, slideInRight } from '@/lib/animations';

interface Testimonial {
  quote: string;
  author: string;
  role: string;
  company: string;
  avatar?: string;
}

const testimonials: Testimonial[] = [
  {
    quote: "O SmartLic reduziu nosso tempo de prospecção de licitações de 8 horas para menos de 30 minutos por semana. A precisão dos filtros é impressionante.",
    author: "Carlos Mendes",
    role: "Gerente Comercial",
    company: "Uniformes Excellence",
  },
  {
    quote: "Antes usávamos 3 plataformas diferentes. Agora, o SmartLic consolida tudo em um só lugar com inteligência artificial que realmente funciona.",
    author: "Ana Paula Silva",
    role: "Diretora de Vendas",
    company: "Facilities Pro",
  },
  {
    quote: "A função de busca automatizada nos permitiu participar de 3x mais licitações sem aumentar a equipe. ROI positivo em 2 meses.",
    author: "Roberto Santos",
    role: "CEO",
    company: "Tech Solutions BR",
  },
];

/**
 * STORY-174 AC5: Testimonials Carousel - NEW Component
 *
 * Features:
 * - Horizontal scrolling carousel (desktop)
 * - Auto-scroll with pause on hover
 * - Dot indicators for navigation
 * - Glassmorphism testimonial cards
 * - Quote icon (subtle, gradient)
 * - Avatar + Name + Role layout
 * - Smooth transitions (fade + slide)
 */
export default function TestimonialsCarousel() {
  const { ref, isVisible } = useScrollAnimation(0.1);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Auto-scroll every 5 seconds
  useEffect(() => {
    if (isPaused || !isVisible) return;

    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % testimonials.length);
    }, 5000);

    return () => clearInterval(interval);
  }, [isPaused, isVisible]);

  return (
    <section
      ref={ref}
      className="py-20 bg-surface-0"
      id="testimonials"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          className="text-center mb-12"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-ink mb-4">
            O que nossos clientes dizem
          </h2>
          <p className="text-lg text-ink-secondary max-w-3xl mx-auto">
            Empresas que transformaram sua prospecção de licitações
          </p>
        </motion.div>

        {/* Carousel Container */}
        <div className="relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentIndex}
              variants={slideInRight}
              initial="hidden"
              animate="visible"
              exit="hidden"
              className="flex justify-center"
            >
              <GlassCard
                hoverable={false}
                variant="default"
                className="max-w-3xl w-full"
              >
                {/* Quote Icon */}
                <div className="text-6xl text-gradient mb-6 opacity-20">
                  "
                </div>

                {/* Quote Text */}
                <blockquote className="text-lg sm:text-xl text-ink italic leading-relaxed mb-8">
                  {testimonials[currentIndex].quote}
                </blockquote>

                {/* Author Info */}
                <div className="flex items-center gap-4">
                  {/* Avatar */}
                  <div className="
                    w-14
                    h-14
                    rounded-full
                    bg-brand-blue-subtle
                    flex
                    items-center
                    justify-center
                    text-brand-blue
                    font-bold
                    text-xl
                  ">
                    {testimonials[currentIndex].author.charAt(0)}
                  </div>

                  {/* Name, Role, Company */}
                  <div>
                    <p className="font-semibold text-ink">
                      {testimonials[currentIndex].author}
                    </p>
                    <p className="text-sm text-ink-secondary">
                      {testimonials[currentIndex].role}
                    </p>
                    <p className="text-sm text-brand-blue font-medium">
                      {testimonials[currentIndex].company}
                    </p>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </AnimatePresence>

          {/* Dot Indicators */}
          <div className="flex justify-center gap-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={`
                  w-3
                  h-3
                  rounded-full
                  transition-all
                  duration-300
                  ${index === currentIndex
                    ? 'bg-brand-blue w-8'
                    : 'bg-ink-faint hover:bg-brand-blue/50'
                  }
                `}
                aria-label={`Go to testimonial ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Trust Badges (Optional) */}
        <motion.div
          className="mt-12 flex justify-center items-center gap-8 flex-wrap grayscale hover:grayscale-0 transition-all duration-300"
          variants={fadeInUp}
          initial="hidden"
          animate={isVisible ? 'visible' : 'hidden'}
        >
          <div className="text-ink-muted text-sm font-medium px-6 py-3 bg-surface-1 rounded-lg border border-border">
            🏆 Avaliação 4.8/5.0
          </div>
          <div className="text-ink-muted text-sm font-medium px-6 py-3 bg-surface-1 rounded-lg border border-border">
            ✅ 98% Taxa de Satisfação
          </div>
          <div className="text-ink-muted text-sm font-medium px-6 py-3 bg-surface-1 rounded-lg border border-border">
            🚀 500+ Empresas Atendidas
          </div>
        </motion.div>
      </div>
    </section>
  );
}
