"use client";

import { useState, useRef, useEffect } from "react";

/**
 * CustomSelect Component
 *
 * Accessible custom select component to replace native <select>
 * Issue #89 feat(frontend): substituir native form controls por custom
 *
 * Features:
 * - Full keyboard navigation (Arrow keys, Enter, Escape, Home, End)
 * - ARIA compliant (role="listbox", aria-activedescendant, etc.)
 * - Click outside to close
 * - Visual consistency with design system
 */

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

export interface CustomSelectProps {
  id: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export function CustomSelect({
  id,
  value,
  options,
  onChange,
  label,
  placeholder = "Selecione uma opção",
  className = "",
  disabled = false,
}: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const selectedOption = options.find(opt => opt.value === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Close dropdown on Escape key - prevent propagation to global handlers
  useEffect(() => {
    if (!isOpen) return;

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        setIsOpen(false);
      }
    };

    // Use capture phase to intercept before other handlers
    window.addEventListener('keydown', handleEscapeKey, true);

    return () => {
      window.removeEventListener('keydown', handleEscapeKey, true);
    };
  }, [isOpen]);

  // Reset highlighted index when opening
  useEffect(() => {
    if (isOpen) {
      const currentIndex = options.findIndex(opt => opt.value === value);
      setHighlightedIndex(currentIndex >= 0 ? currentIndex : 0);
    }
  }, [isOpen, value, options]);

  // Scroll highlighted option into view
  useEffect(() => {
    if (isOpen && highlightedIndex >= 0 && listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [isOpen, highlightedIndex]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (isOpen && highlightedIndex >= 0) {
          onChange(options[highlightedIndex].value);
          setIsOpen(false);
        } else {
          setIsOpen(true);
        }
        break;

      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        break;

      case 'ArrowDown':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => Math.min(prev + 1, options.length - 1));
        }
        break;

      case 'ArrowUp':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => Math.max(prev - 1, 0));
        }
        break;

      case 'Home':
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(0);
        }
        break;

      case 'End':
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(options.length - 1);
        }
        break;

      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
        }
        break;
    }
  };

  const handleOptionClick = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {label && (
        <label htmlFor={id} className="block text-base font-semibold text-ink mb-2">
          {label}
        </label>
      )}

      {/* Select Button */}
      <button
        id={id}
        type="button"
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={`${id}-listbox`}
        aria-activedescendant={isOpen && highlightedIndex >= 0 ? `${id}-option-${highlightedIndex}` : undefined}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        className={`w-full border border-strong rounded-input px-4 py-3 text-base text-left
                   bg-surface-0 text-ink
                   focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue
                   disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
                   transition-colors flex items-center justify-between`}
      >
        <span className={selectedOption ? 'text-ink' : 'text-ink-muted'}>
          {selectedOption?.label || placeholder}
        </span>
        <svg
              role="img"
              aria-label="Expandir seção"
          className={`w-5 h-5 text-ink-secondary transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown List */}
      {isOpen && (
        <ul
          ref={listRef}
          id={`${id}-listbox`}
          role="listbox"
          aria-labelledby={id}
          className="absolute z-50 w-full mt-1 bg-surface-0 border border-strong rounded-input shadow-lg
                     max-h-60 overflow-auto animate-fade-in"
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={option.value === value}
              onClick={() => handleOptionClick(option.value)}
              onMouseEnter={() => setHighlightedIndex(index)}
              className={`px-4 py-3 cursor-pointer transition-colors ${
                highlightedIndex === index
                  ? 'bg-brand-blue-subtle text-brand-navy'
                  : option.value === value
                    ? 'bg-surface-1 text-brand-blue font-medium'
                    : 'text-ink hover:bg-surface-1'
              }`}
            >
              <div className="flex flex-col">
                <span>{option.label}</span>
                {option.description && (
                  <span className="text-sm text-ink-muted mt-0.5">{option.description}</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
