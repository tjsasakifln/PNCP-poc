"use client";

import { useRef, useState, useEffect } from "react";
import { DayPicker } from "react-day-picker";
import { format, parse } from "date-fns";
import { ptBR } from "date-fns/locale";
import "react-day-picker/dist/style.css";

/**
 * CustomDateInput Component
 *
 * Accessible custom date input with mobile-optimized date picker
 * Issue #118: Mobile-optimized date picker using react-day-picker
 * Issue #89: Replace native form controls with custom components
 *
 * Features:
 * - Desktop: Native date input (familiar, fast)
 * - Mobile: Visual calendar picker (touch-optimized)
 * - Styled date input with calendar icon
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 * - Responsive modal for mobile date selection
 */

export interface CustomDateInputProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  label?: string;
  min?: string;
  max?: string;
  className?: string;
  disabled?: boolean;
}

export function CustomDateInput({
  id,
  value,
  onChange,
  label,
  min,
  max,
  className = "",
  disabled = false,
}: CustomDateInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [showPicker, setShowPicker] = useState(false);

  // Detect mobile device (Issue #118)
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.matchMedia("(max-width: 767px)").matches);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleCalendarClick = () => {
    if (disabled) return;

    if (isMobile) {
      // Mobile: Open visual picker modal
      setShowPicker(true);
    } else {
      // Desktop: Use native picker
      if (inputRef.current) {
        inputRef.current.focus();
        inputRef.current.showPicker?.();
      }
    }
  };

  const handleDaySelect = (day: Date | undefined) => {
    if (day) {
      const formatted = format(day, "yyyy-MM-dd");
      onChange(formatted);
      setShowPicker(false);
    }
  };

  const formatDateDisplay = (dateStr: string): string => {
    if (!dateStr) return '';

    const date = new Date(dateStr + 'T00:00:00'); // Prevent timezone issues
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="block text-base font-semibold text-ink mb-2">
          {label}
        </label>
      )}

      <div className="relative">
        {/* Custom styled display container */}
        <div
          className={`w-full border rounded-input px-4 py-3 text-base
                     bg-surface-0 text-ink
                     transition-all duration-200
                     flex items-center justify-between
                     ${isFocused ? 'ring-2 ring-brand-blue border-brand-blue' : 'border-strong'}
                     ${disabled ? 'bg-surface-1 text-ink-muted cursor-not-allowed' : 'cursor-pointer'}`}
        >
          {/* Hidden native date input - z-10 ensures it captures all clicks */}
          <input
            ref={inputRef}
            id={id}
            type="date"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            min={min}
            max={max}
            disabled={disabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-10"
            aria-label={label}
          />
          <span className={value ? 'text-ink' : 'text-ink-muted'}>
            {value ? formatDateDisplay(value) : 'DD/MM/AAAA'}
          </span>

          {/* Calendar Icon - z-20 to be above the input overlay */}
          <button
            type="button"
            onClick={handleCalendarClick}
            disabled={disabled}
            className="pointer-events-auto relative z-20"
            aria-label="Abrir seletor de data"
            tabIndex={-1}
          >
            <svg
              role="img"
              aria-label="Ícone"
              className="w-5 h-5 text-ink-secondary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Date Picker Modal - Issue #118, improved landscape support */}
      {isMobile && showPicker && (
        <div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 animate-fade-in"
          onClick={() => setShowPicker(false)}
        >
          <div
            className="bg-surface-0 rounded-t-card sm:rounded-card shadow-xl w-full sm:max-w-md p-4 sm:p-6
                       max-h-[85vh] overflow-y-auto animate-fade-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-ink">
                {label || 'Selecionar Data'}
              </h3>
              <button
                onClick={() => setShowPicker(false)}
                type="button"
                className="text-ink-muted hover:text-ink transition-colors"
                aria-label="Fechar seletor de data"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="mobile-date-picker">
              <DayPicker
                mode="single"
                selected={value ? parse(value, "yyyy-MM-dd", new Date()) : undefined}
                onSelect={handleDaySelect}
                locale={ptBR}
                disabled={disabled}
                fromDate={min ? parse(min, "yyyy-MM-dd", new Date()) : undefined}
                toDate={max ? parse(max, "yyyy-MM-dd", new Date()) : undefined}
                defaultMonth={value ? parse(value, "yyyy-MM-dd", new Date()) : new Date()}
                className="mx-auto"
              />
            </div>

            <button
              onClick={() => setShowPicker(false)}
              type="button"
              className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-brand-navy
                         hover:bg-brand-blue-hover rounded-button transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
