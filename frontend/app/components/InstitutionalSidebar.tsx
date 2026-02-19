import React from 'react';
import Link from 'next/link';

// ============================================================================
// TypeScript Interfaces
// ============================================================================

interface Benefit {
  icon: string;
  text: string;
}

interface Stat {
  value: string;
  label: string;
}

interface SidebarContent {
  headline: string;
  subheadline: string;
  benefits: Benefit[];
  stats: Stat[];
}

type SidebarContentMap = {
  login: SidebarContent;
  signup: SidebarContent;
};

interface InstitutionalSidebarProps {
  variant: 'login' | 'signup';
  className?: string;
}

// ============================================================================
// Inline SVG Icon Components
// ============================================================================

const ICONS: Record<string, React.FC<{ className?: string }>> = {
  clock: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),

  filter: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
  ),

  brain: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),

  download: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
    </svg>
  ),

  history: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12a9 9 0 019-9" />
    </svg>
  ),

  gift: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
    </svg>
  ),

  'credit-card-off': ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12" opacity="0.5" />
    </svg>
  ),

  zap: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),

  headset: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
  ),

  shield: ({ className = "w-6 h-6" }) => (
    <svg
              role="img"
              aria-label="Ícone" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),

  check: ({ className = "w-5 h-5" }) => (
    <svg
              role="img"
              aria-label="Confirmado" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
};

// ============================================================================
// Content Configuration
// ============================================================================

const SIDEBAR_CONTENT: SidebarContentMap = {
  login: {
    headline: "Descubra oportunidades de licitação antes da concorrência",
    subheadline: "Acesse seu painel e encontre as melhores oportunidades para sua empresa",
    benefits: [
      { icon: "clock", text: "Cobertura nacional de fontes oficiais" },
      { icon: "filter", text: "Filtros por estado, valor e setor" },
      { icon: "brain", text: "Avaliação estratégica por IA" },
      { icon: "download", text: "Exportação de relatórios em Excel" },
      { icon: "history", text: "Histórico completo de buscas" },
    ],
    stats: [
      { value: "27", label: "estados cobertos" },
      { value: "15", label: "setores especializados" },
      { value: "24h", label: "atualização diária" },
    ],
  },
  signup: {
    headline: "Sua empresa a um passo das melhores oportunidades públicas",
    subheadline: "Crie sua conta e comece a encontrar licitações compatíveis com seu negócio",
    benefits: [
      { icon: "gift", text: "7 dias do produto completo — 3 análises incluídas" },
      { icon: "credit-card-off", text: "Sem necessidade de cartão de crédito" },
      { icon: "zap", text: "Configuração em menos de 2 minutos" },
      { icon: "headset", text: "Suporte dedicado via plataforma" },
      { icon: "shield", text: "Dados protegidos e conformidade LGPD" },
    ],
    stats: [
      { value: "27", label: "estados cobertos" },
      { value: "1000+", label: "licitações/dia" },
      { value: "100%", label: "fonte oficial" },
    ],
  },
};

// ============================================================================
// InstitutionalSidebar Component
// ============================================================================

export default function InstitutionalSidebar({ variant, className = "" }: InstitutionalSidebarProps) {
  const content = SIDEBAR_CONTENT[variant];

  return (
    <div
      className={`
        min-h-screen md:min-h-0 md:h-auto
        bg-gradient-to-br from-[var(--brand-navy)] to-[var(--brand-blue)]
        flex items-center justify-center
        p-6 md:p-12 lg:p-16
        ${className}
      `.trim()}
    >
      <div className="max-w-xl w-full space-y-8">
        {/* Brand + Back to Home */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-white/70 hover:text-white transition-colors group"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
          <span className="text-2xl font-bold text-white group-hover:text-white/90 transition-colors">
            SmartLic<span className="text-white/60">.tech</span>
          </span>
        </Link>

        {/* Headline Section */}
        <div className="space-y-4">
          <h1 className="text-3xl md:text-4xl font-display font-bold text-white leading-tight">
            {content.headline}
          </h1>
          <p className="text-base md:text-lg text-white/90">
            {content.subheadline}
          </p>
        </div>

        {/* Benefits List */}
        <ul className="space-y-4" role="list">
          {content.benefits.map((benefit, index) => {
            const IconComponent = ICONS[benefit.icon];
            return (
              <li
                key={index}
                className="flex items-start gap-3 text-white/90"
              >
                <div className="flex-shrink-0 mt-0.5">
                  <IconComponent className="w-6 h-6 text-white" />
                </div>
                <span className="text-sm md:text-base leading-relaxed">
                  {benefit.text}
                </span>
              </li>
            );
          })}
        </ul>

        {/* Statistics Grid */}
        <div className="grid grid-cols-3 gap-4 pt-4">
          {content.stats.map((stat, index) => (
            <div
              key={index}
              className="text-center px-4 py-3 bg-white/5 rounded-lg backdrop-blur-sm"
            >
              <div className="text-2xl font-bold text-white mb-1">
                {stat.value}
              </div>
              <div className="text-xs uppercase tracking-wide text-white/70">
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Official Data Badge */}
        <div className="pt-4">
          <div className="flex items-center gap-2 px-4 py-3 bg-white/10 backdrop-blur-sm rounded-lg border border-white/20">
            <ICONS.check className="w-5 h-5 text-white flex-shrink-0" />
            <span className="text-sm text-white/90">
              Dados de fontes oficiais federais e estaduais
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
