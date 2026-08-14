'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useAuth } from '../AuthProvider';
import MobileMenu from '../../../components/layout/MobileMenu';

/**
 * DEBT-v3-S2 AC20: Client island for LandingNavbar interactive parts.
 * Extracted from LandingNavbar to enable RSC rendering of static navbar shell.
 * REPO-010: Added NavSolucoesDropdown for Soluções nav item.
 *
 * Handles:
 * - Scroll-based background styling (isScrolled)
 * - Mobile menu toggle
 * - Auth-aware CTA buttons
 * - Soluções dropdown (desktop)
 */

/**
 * ScrollStyler: applies background/shadow classes to <header> on scroll.
 * Uses a data-attribute approach — the server renders both states in CSS,
 * and this component toggles a data-scrolled attribute on the parent header.
 */
export function NavbarScrollStyler() {
  useEffect(() => {
    const header = document.querySelector('[data-navbar-header]');
    if (!header) return;

    const handleScroll = () => {
      if (window.scrollY > 10) {
        header.setAttribute('data-scrolled', 'true');
      } else {
        header.removeAttribute('data-scrolled');
      }
    };

    // Run once on mount in case page is already scrolled
    handleScroll();

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return null;
}

/**
 * NavScrollButton: scroll-to-section button (kept for backward compat and direct use).
 * Replaces a server-rendered placeholder with an interactive button.
 */
export function NavScrollButton({ sectionId, label }: { sectionId: string; label: string }) {
  const scrollToSection = useCallback((id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return (
    <button
      onClick={() => scrollToSection(sectionId)}
      className="text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
    >
      {label}
    </button>
  );
}

/**
 * NavSolucoesDropdown: Desktop dropdown for "Soluções" nav item. (REPO-010)
 * Phase 0 — all items except SaaS point to /consultoria-b2g with ?modalidade= query param.
 */
const SOLUCOES_ITEMS = [
  { label: 'Licitações', href: '/licitacoes', description: 'Decidir se vale disputar' },
  { label: 'Contratos', href: '/contratos', description: 'Risco e oportunidade homologada' },
  { label: 'Empresas', href: '/cnpj', description: 'Carteira pública por CNPJ' },
  { label: 'Consultoria CONFENGE', href: '/consultoria-b2g', description: 'Diagnóstico sem criar conta' },
] as const;

export function NavSolucoesDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [isOpen]);

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen((v) => !v)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        data-testid="nav-solucoes-dropdown"
        className="flex items-center gap-1 text-sm text-ink-secondary/80 hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
      >
        Soluções
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute top-full left-0 mt-2 w-56 rounded-xl bg-[var(--surface-0)] shadow-lg border border-[var(--border)] py-1 z-50"
        >
          {SOLUCOES_ITEMS.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              role="menuitem"
              onClick={() => setIsOpen(false)}
              className="block px-4 py-2.5 text-sm text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors focus-visible:outline-none focus-visible:bg-[var(--surface-1)]"
            >
              <span className="font-medium">{item.label}</span>
              <span className="block text-xs text-[var(--ink-secondary)] mt-0.5">{item.description}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * NavbarAuthCTA: Auth-aware CTA buttons (desktop).
 * Shows loading placeholder, "Ir para Busca" for logged-in, or "Entrar" + diagnóstico CONFENGE for visitors.
 */
export function NavbarAuthCTA() {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="w-[160px]" />;
  }

  if (user) {
    return (
      <Link
        href="/buscar"
        className="bg-brand-navy hover:bg-brand-blue-hover text-white text-sm font-medium px-4 py-1.5 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
      >
        Ir para Busca
      </Link>
    );
  }

  return (
    <>
      <Link
        href="/login"
        className="text-sm text-ink-secondary/80 hover:text-ink font-medium px-3 py-1.5 rounded-button transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
      >
        Entrar
      </Link>
      <Link
        href="/consultoria-b2g?cta=cta.home.diagnostico"
        className="bg-brand-navy hover:bg-brand-blue-hover text-white text-sm font-medium px-4 py-1.5 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
      >
        Diagnóstico CONFENGE
      </Link>
    </>
  );
}

/**
 * NavbarMobileControls: Hamburger button + MobileMenu (mobile only).
 * Requires client state for open/close toggle and auth for menu content.
 */
export function NavbarMobileControls() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user } = useAuth();

  const scrollToSection = useCallback((id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return (
    <>
      {/* Hamburger button -- visible only on mobile */}
      <button
        onClick={() => setIsMobileMenuOpen(true)}
        className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg
                   text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors
                   focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]"
        aria-label="Abrir menu"
        aria-expanded={isMobileMenuOpen}
        data-testid="hamburger-button"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        user={user}
        scrollToSection={scrollToSection}
      />
    </>
  );
}
