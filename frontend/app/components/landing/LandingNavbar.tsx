'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useAuth } from '../AuthProvider';

interface LandingNavbarProps {
  className?: string;
}

export default function LandingNavbar({ className = '' }: LandingNavbarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const { user, loading } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-surface-0/95 backdrop-blur-sm shadow-sm border-b border-[var(--border)]'
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

          {/* Navigation Links */}
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

          {/* CTA Buttons - AC21-AC24: Auth-aware rendering */}
          <div className="flex items-center space-x-4">
            {loading ? (
              // AC24: Prevent layout shift during auth loading
              <div className="w-[180px]" />
            ) : user ? (
              // AC22: Logged-in user sees "Ir para Busca" button
              <Link
                href="/buscar"
                className="bg-brand-navy hover:bg-brand-blue-hover text-white font-semibold px-4 py-2 rounded-button transition-all hover:scale-[1.02] active:scale-[0.98] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)] focus-visible:ring-offset-2"
              >
                Ir para Busca
              </Link>
            ) : (
              // AC23: Not-logged-in user sees Login + Criar conta
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
        </div>
      </nav>
    </header>
  );
}
