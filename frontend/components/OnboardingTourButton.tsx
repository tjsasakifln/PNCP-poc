'use client';

import { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';

interface TourOption {
  id: string;
  label: string;
  path: string;
}

const TOUR_OPTIONS: TourOption[] = [
  { id: 'search', label: 'Tour de busca', path: '/buscar' },
  { id: 'results', label: 'Tour de resultados', path: '/buscar' },
  { id: 'pipeline', label: 'Tour de pipeline', path: '/pipeline' },
];

interface OnboardingTourButtonProps {
  availableTours?: {
    search?: () => void;
    results?: () => void;
    pipeline?: () => void;
  };
}

export function OnboardingTourButton({ availableTours = {} }: OnboardingTourButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    function handleEsc(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false);
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      return () => document.removeEventListener('keydown', handleEsc);
    }
  }, [isOpen]);

  const handleTourClick = (option: TourOption) => {
    setIsOpen(false);
    const restartFn = availableTours[option.id as keyof typeof availableTours];
    if (restartFn) {
      restartFn();
    } else if (pathname !== option.path) {
      router.push(`${option.path}?tour=${option.id}`);
    }
  };

  return (
    <div ref={menuRef} className="fixed bottom-6 right-6 z-50" data-testid="onboarding-tour-button">
      {/* Menu */}
      {isOpen && (
        <div
          className="absolute bottom-14 right-0 w-52 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-200 dark:border-slate-600 py-2 animate-fade-in-up"
          role="menu"
          data-testid="tour-menu"
        >
          <div className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            Guias interativos
          </div>
          {TOUR_OPTIONS.map((option) => (
            <button
              key={option.id}
              onClick={() => handleTourClick(option)}
              className="w-full text-left px-3 py-2.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
              role="menuitem"
              data-testid={`tour-option-${option.id}`}
            >
              <span className="w-5 h-5 flex items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-xs font-bold">
                {option.id === 'search' ? '1' : option.id === 'results' ? '2' : '3'}
              </span>
              {option.label}
            </button>
          ))}
        </div>
      )}

      {/* Floating button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 rounded-full bg-[#1e3a5f] text-white shadow-lg hover:bg-[#2a4d7a] transition-all hover:scale-105 flex items-center justify-center text-lg font-bold"
        aria-label="Guia interativo"
        aria-expanded={isOpen}
        data-testid="tour-trigger-button"
      >
        ?
      </button>
    </div>
  );
}
