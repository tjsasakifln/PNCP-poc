// DEBT-v3-S2 AC20: LandingNavbar is now an RSC -- client islands (NavbarScrollStyler,
// NavScrollButton, NavbarAuthCTA, NavbarMobileControls) are in NavbarClientIsland.tsx
// to minimize the 'use client' footprint.
import Link from 'next/link';
import {
  NavbarScrollStyler,
  NavScrollButton,
  NavbarAuthCTA,
  NavbarMobileControls,
} from './NavbarClientIsland';

interface LandingNavbarProps {
  className?: string;
}

export default function LandingNavbar({ className = '' }: LandingNavbarProps) {
  return (
    <header
      data-navbar-header
      className={`sticky top-0 z-50 transition-all duration-300 bg-transparent data-[scrolled]:bg-[var(--surface-0)] data-[scrolled]:md:bg-surface-0/70 data-[scrolled]:md:backdrop-blur-xl data-[scrolled]:shadow-[0_1px_3px_rgba(0,0,0,0.04)] data-[scrolled]:border-b data-[scrolled]:border-[var(--border)]/50 ${className}`}
    >
      {/* Client island: toggles data-scrolled attribute on header based on scroll position */}
      <NavbarScrollStyler />

      <nav className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo -- fully static, server-rendered */}
          <div className="flex-shrink-0">
            <Link
              href="/"
              className="text-xl font-semibold text-brand-navy hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded-button px-1 tracking-tight"
            >
              SmartLic<span className="text-brand-blue font-normal">.tech</span>
            </Link>
          </div>

          {/* Navigation Links -- hidden on mobile */}
          <div className="hidden md:flex items-center space-x-6">
            <Link
              href="/planos"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Planos
            </Link>
            {/* Client island: scroll-to-section button */}
            <NavScrollButton sectionId="como-funciona" label="Como Funciona" />
            <Link
              href="/blog"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Blog
            </Link>
            {/* SEO-PLAYBOOK Fundação §5: link to calculator for PageRank flow */}
            <Link
              href="/calculadora"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Calculadora
            </Link>
            {/* STORY-431 AC1: Observatório no menu de navegação */}
            <Link
              href="/observatorio"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Observatório
            </Link>
            <Link
              href="/casos"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Casos
            </Link>
            <Link
              href="/sobre"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Sobre
            </Link>
            <Link
              href="/perguntas"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Perguntas
            </Link>
            <Link
              href="#suporte"
              className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Suporte
            </Link>
          </div>

          {/* CTA Buttons (desktop) + Hamburger (mobile) */}
          <div className="flex items-center space-x-4">
            {/* Desktop CTA -- hidden on mobile. Client island: auth-aware */}
            <div className="hidden md:flex items-center space-x-3">
              <NavbarAuthCTA />
            </div>

            {/* Mobile controls: hamburger + mobile menu. Client island */}
            <NavbarMobileControls />
          </div>
        </div>
      </nav>
    </header>
  );
}
