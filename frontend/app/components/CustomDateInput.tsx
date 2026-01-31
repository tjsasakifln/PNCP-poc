"use client";

import { useRef, useState } from "react";

/**
 * CustomDateInput Component
 *
 * Accessible custom date input to replace native date inputs
 * Issue #89 feat(frontend): substituir native form controls por custom
 *
 * Features:
 * - Styled date input with calendar icon
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 * - Maintains native date picker functionality
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

  const handleCalendarClick = () => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.showPicker?.();
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
        {/* Hidden native date input */}
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
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          aria-label={label}
        />

        {/* Custom styled display */}
        <div
          className={`w-full border rounded-input px-4 py-3 text-base
                     bg-surface-0 text-ink
                     transition-all duration-200
                     flex items-center justify-between
                     ${isFocused ? 'ring-2 ring-brand-blue border-brand-blue' : 'border-strong'}
                     ${disabled ? 'bg-surface-1 text-ink-muted cursor-not-allowed' : 'cursor-pointer'}
                     pointer-events-none`}
        >
          <span className={value ? 'text-ink' : 'text-ink-muted'}>
            {value ? formatDateDisplay(value) : 'DD/MM/AAAA'}
          </span>

          {/* Calendar Icon */}
          <button
            type="button"
            onClick={handleCalendarClick}
            disabled={disabled}
            className="pointer-events-auto"
            aria-label="Abrir seletor de data"
            tabIndex={-1}
          >
            <svg
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
    </div>
  );
}
