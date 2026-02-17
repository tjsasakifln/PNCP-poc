'use client';

import Link from 'next/link';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../AuthProvider';
import MobileMenu from '../../../components/layout/MobileMenu';

interface LandingNavbarProps {
  className?: string;
}

export default function LandingNavbar({ className = '' }: LandingNavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { user, loading } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = useCallback((id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-surface-0/95 backdrop-blur-md shadow-glass border-b border-[var(--border)]'
          : 'bg-transparent'
      } ${className}`}
    >
      <nav className="max-w-landing mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link
              href="/"
              className="text-2xl font-bold text-brand-navy hover:text-brand-blue transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2 rounded-button px-1"
            >
              SmartLic<span className="text-brand-blue">.tech</span>
            </Link>
          </div>

          {/* Navigation Links — hidden on mobile */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/planos"
              className="text-ink-secondary hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Planos
            </Link>
            <button
              onClick={() => scrollToSection('como-funciona')}
              className="text-ink-secondary hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Como Funciona
            </button>
            <Link
              href="#suporte"
              className="text-ink-secondary hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
            >
              Suporte
            </Link>
          </div>

          {/* CTA Buttons (desktop) + Hamburger (mobile) */}
          <div className="flex items-center space-x-4">
            {/* Desktop CTA — hidden on mobile */}
            <div className="hidden md:flex items-center space-x-4">
              {loading ? (
                <div className="w-[180px]" />
              ) : user ? (
                <Link
                  href="/buscar"
                  className="bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
                >
                  Ir para Busca
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="text-brand-navy hover:text-brand-blue font-semibold transition-colors focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] rounded px-2 py-1"
                  >
                    Login
                  </Link>
                  <Link
                    href="/signup?source=landing-cta"
                    className="bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
                  >
                    Criar conta
                  </Link>
                </>
              )}
            </div>

            {/* Hamburger button — AC1: visible only on mobile */}
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
          </div>
        </div>
      </nav>

      {/* Mobile Menu — AC2-AC6 */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        user={user}
        scrollToSection={scrollToSection}
      />
    </header>
  );
}
