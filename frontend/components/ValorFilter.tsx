"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * ValorFilter Component
 *
 * Value range filter with dual slider and quick preset buttons.
 * Based on specs from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 *
 * Features:
 * - Dual slider (range) from R$ 0 to R$ 10M
 * - Quick range presets: Até 50k, 50k-200k, 200k-1M, 1M-5M, Acima 5M, Qualquer
 * - Custom numeric inputs for min/max values
 * - Brazilian currency formatting (R$ with dots)
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 */

interface FaixaValor {
  id: string;
  label: string;
  min: number;
  max: number | null; // null = no limit
}

const FAIXAS_VALOR: FaixaValor[] = [
  { id: "micro", label: "Até 50k", min: 0, max: 50000 },
  { id: "pequeno", label: "50k-200k", min: 50000, max: 200000 },
  { id: "medio", label: "200k-1M", min: 200000, max: 1000000 },
  { id: "grande", label: "1M-5M", min: 1000000, max: 5000000 },
  { id: "muito_grande", label: "Acima 5M", min: 5000000, max: null },
  { id: "qualquer", label: "Qualquer", min: 0, max: null },
];

// Slider limits
const SLIDER_MIN = 0;
const SLIDER_MAX = 10000000; // R$ 10 million
const SLIDER_STEP = 10000; // R$ 10k steps

export interface ValorFilterProps {
  valorMin: number | null;
  valorMax: number | null;
  onChange: (min: number | null, max: number | null) => void;
  onValidationChange?: (isValid: boolean) => void;
  disabled?: boolean;
}

export function ValorFilter({
  valorMin,
  valorMax,
  onChange,
  onValidationChange,
  disabled = false,
}: ValorFilterProps) {
  // Internal state for input fields (allows typing without immediate validation)
  const [inputMin, setInputMin] = useState(
    valorMin !== null ? formatBRL(valorMin) : ""
  );
  const [inputMax, setInputMax] = useState(
    valorMax !== null ? formatBRL(valorMax) : ""
  );

  // Track which thumb is being dragged
  const [dragging, setDragging] = useState<"min" | "max" | null>(null);
  const sliderRef = useRef<HTMLDivElement>(null);

  // Sync internal state with props
  useEffect(() => {
    setInputMin(valorMin !== null ? formatBRL(valorMin) : "");
  }, [valorMin]);

  useEffect(() => {
    setInputMax(valorMax !== null ? formatBRL(valorMax) : "");
  }, [valorMax]);

  // Format number to Brazilian currency display (without R$ prefix)
  function formatBRL(value: number): string {
    return value.toLocaleString("pt-BR");
  }

  // Format number with R$ prefix
  function formatCurrency(value: number | null): string {
    if (value === null) return "Sem limite";
    return `R$ ${formatBRL(value)}`;
  }

  // Parse Brazilian formatted string to number
  function parseBRL(value: string): number | null {
    const cleaned = value.replace(/\D/g, "");
    return cleaned ? parseInt(cleaned, 10) : null;
  }

  // Validation state - check if min > max
  const isMinMaxInvalid = (() => {
    const minParsed = parseBRL(inputMin);
    const maxParsed = parseBRL(inputMax);
    return minParsed !== null && maxParsed !== null && minParsed > maxParsed;
  })();

  // Notify parent of validation state changes
  useEffect(() => {
    onValidationChange?.(!isMinMaxInvalid);
  }, [isMinMaxInvalid, onValidationChange]);

  // Identify which preset is currently selected
  const faixaSelecionada =
    FAIXAS_VALOR.find(
      (f) => f.min === valorMin && f.max === valorMax
    )?.id ?? "custom";

  const handleFaixaClick = (faixa: FaixaValor) => {
    if (disabled) return;
    onChange(faixa.min, faixa.max);
  };

  const handleInputMinBlur = () => {
    const parsed = parseBRL(inputMin);
    if (parsed !== null && (valorMax === null || parsed <= valorMax)) {
      onChange(parsed, valorMax);
    } else if (parsed !== null && valorMax !== null && parsed > valorMax) {
      // If min > max, set both to the same value
      onChange(parsed, parsed);
    }
  };

  const handleInputMaxBlur = () => {
    const parsed = parseBRL(inputMax);
    if (parsed === null) {
      onChange(valorMin, null);
    } else if (valorMin === null || parsed >= valorMin) {
      onChange(valorMin, parsed);
    } else {
      // If max < min, set both to the same value
      onChange(parsed, parsed);
    }
  };

  // Slider thumb position calculation
  const getThumbPosition = (value: number | null, isMax: boolean): number => {
    if (isMax && value === null) return 100;
    if (value === null) return 0;
    return Math.min(100, Math.max(0, (value / SLIDER_MAX) * 100));
  };

  // Calculate value from mouse position
  const getValueFromPosition = useCallback(
    (clientX: number): number => {
      if (!sliderRef.current) return 0;
      const rect = sliderRef.current.getBoundingClientRect();
      const percentage = Math.min(
        100,
        Math.max(0, ((clientX - rect.left) / rect.width) * 100)
      );
      const rawValue = (percentage / 100) * SLIDER_MAX;
      // Round to nearest step
      return Math.round(rawValue / SLIDER_STEP) * SLIDER_STEP;
    },
    []
  );

  // Handle slider drag
  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!dragging || disabled) return;
      const newValue = getValueFromPosition(e.clientX);

      if (dragging === "min") {
        const maxVal = valorMax ?? SLIDER_MAX;
        const clampedValue = Math.min(newValue, maxVal);
        onChange(clampedValue, valorMax);
      } else {
        const minVal = valorMin ?? 0;
        const clampedValue = Math.max(newValue, minVal);
        onChange(valorMin, clampedValue === SLIDER_MAX ? null : clampedValue);
      }
    },
    [dragging, disabled, valorMin, valorMax, onChange, getValueFromPosition]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(null);
  }, []);

  // Attach/detach mouse event listeners
  useEffect(() => {
    if (dragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      return () => {
        window.removeEventListener("mousemove", handleMouseMove);
        window.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [dragging, handleMouseMove, handleMouseUp]);

  // Touch support
  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!dragging || disabled) return;
      const touch = e.touches[0];
      const newValue = getValueFromPosition(touch.clientX);

      if (dragging === "min") {
        const maxVal = valorMax ?? SLIDER_MAX;
        const clampedValue = Math.min(newValue, maxVal);
        onChange(clampedValue, valorMax);
      } else {
        const minVal = valorMin ?? 0;
        const clampedValue = Math.max(newValue, minVal);
        onChange(valorMin, clampedValue === SLIDER_MAX ? null : clampedValue);
      }
    },
    [dragging, disabled, valorMin, valorMax, onChange, getValueFromPosition]
  );

  const handleTouchEnd = useCallback(() => {
    setDragging(null);
  }, []);

  useEffect(() => {
    if (dragging) {
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleTouchEnd);
      return () => {
        window.removeEventListener("touchmove", handleTouchMove);
        window.removeEventListener("touchend", handleTouchEnd);
      };
    }
  }, [dragging, handleTouchMove, handleTouchEnd]);

  const minPosition = getThumbPosition(valorMin, false);
  const maxPosition = getThumbPosition(valorMax, true);

  return (
    <div className="space-y-4">
      <label className="text-base font-semibold text-ink">
        Valor Estimado:
      </label>

      {/* Dual Range Slider */}
      <div className="px-2 py-4">
        <div
          ref={sliderRef}
          className="relative h-2 bg-surface-2 rounded-full cursor-pointer"
          role="group"
          aria-label="Seletor de faixa de valor"
        >
          {/* Active range highlight */}
          <div
            className="absolute h-full bg-brand-blue rounded-full"
            style={{
              left: `${minPosition}%`,
              width: `${maxPosition - minPosition}%`,
            }}
          />

          {/* Min thumb */}
          <button
            type="button"
            disabled={disabled}
            onMouseDown={() => !disabled && setDragging("min")}
            onTouchStart={() => !disabled && setDragging("min")}
            onKeyDown={(e) => {
              if (disabled) return;
              const currentMin = valorMin ?? 0;
              if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
                e.preventDefault();
                const newVal = Math.max(0, currentMin - SLIDER_STEP);
                onChange(newVal, valorMax);
              } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
                e.preventDefault();
                const maxVal = valorMax ?? SLIDER_MAX;
                const newVal = Math.min(maxVal, currentMin + SLIDER_STEP);
                onChange(newVal, valorMax);
              }
            }}
            className={`
              absolute top-1/2 -translate-y-1/2 -translate-x-1/2
              w-5 h-5 rounded-full bg-white border-2 border-brand-blue
              shadow-md cursor-grab active:cursor-grabbing
              focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 focus:ring-offset-[var(--surface-2)]
              ${disabled ? "opacity-50 cursor-not-allowed" : "hover:scale-110"}
              transition-transform duration-150
            `}
            style={{ left: `${minPosition}%` }}
            role="slider"
            aria-label="Valor mínimo"
            aria-valuemin={SLIDER_MIN}
            aria-valuemax={SLIDER_MAX}
            aria-valuenow={valorMin ?? 0}
            aria-valuetext={formatCurrency(valorMin)}
            tabIndex={disabled ? -1 : 0}
          />

          {/* Max thumb */}
          <button
            type="button"
            disabled={disabled}
            onMouseDown={() => !disabled && setDragging("max")}
            onTouchStart={() => !disabled && setDragging("max")}
            onKeyDown={(e) => {
              if (disabled) return;
              const currentMax = valorMax ?? SLIDER_MAX;
              if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
                e.preventDefault();
                const minVal = valorMin ?? 0;
                const newVal = Math.max(minVal, currentMax - SLIDER_STEP);
                onChange(valorMin, newVal === SLIDER_MAX ? null : newVal);
              } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
                e.preventDefault();
                const newVal = Math.min(SLIDER_MAX, currentMax + SLIDER_STEP);
                onChange(valorMin, newVal === SLIDER_MAX ? null : newVal);
              }
            }}
            className={`
              absolute top-1/2 -translate-y-1/2 -translate-x-1/2
              w-5 h-5 rounded-full bg-white border-2 border-brand-blue
              shadow-md cursor-grab active:cursor-grabbing
              focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 focus:ring-offset-[var(--surface-2)]
              ${disabled ? "opacity-50 cursor-not-allowed" : "hover:scale-110"}
              transition-transform duration-150
            `}
            style={{ left: `${maxPosition}%` }}
            role="slider"
            aria-label="Valor máximo"
            aria-valuemin={SLIDER_MIN}
            aria-valuemax={SLIDER_MAX}
            aria-valuenow={valorMax ?? SLIDER_MAX}
            aria-valuetext={formatCurrency(valorMax)}
            tabIndex={disabled ? -1 : 0}
          />
        </div>

        {/* Slider labels */}
        <div className="flex justify-between mt-2 text-xs text-ink-muted">
          <span>{formatCurrency(valorMin ?? 0)}</span>
          <span>{formatCurrency(valorMax)}</span>
        </div>
      </div>

      {/* Quick preset buttons */}
      <div className="flex flex-wrap gap-2">
        {FAIXAS_VALOR.map((faixa) => {
          const isSelected = faixaSelecionada === faixa.id;

          return (
            <button
              key={faixa.id}
              type="button"
              onClick={() => handleFaixaClick(faixa)}
              disabled={disabled}
              className={`
                px-3 py-1.5 rounded-button text-xs sm:text-sm font-medium
                transition-all duration-200 border
                ${disabled ? "opacity-50 cursor-not-allowed" : ""}
                ${
                  isSelected
                    ? "bg-brand-navy text-white border-brand-navy"
                    : "bg-surface-0 text-ink-secondary border-strong hover:border-accent hover:text-brand-blue hover:bg-brand-blue-subtle"
                }
              `}
            >
              {faixa.label}
            </button>
          );
        })}
      </div>

      {/* Custom value inputs */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label
            htmlFor="valor-min"
            className="block text-xs text-ink-muted font-medium"
          >
            Mínimo:
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-sm">
              R$
            </span>
            <input
              id="valor-min"
              type="text"
              inputMode="numeric"
              value={inputMin}
              onChange={(e) => {
                // Strip non-numeric characters except dots and commas (Brazilian formatting)
                const raw = e.target.value.replace(/[^\d.,]/g, '');
                setInputMin(raw);
              }}
              onBlur={handleInputMinBlur}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleInputMinBlur();
                }
              }}
              placeholder="0"
              disabled={disabled}
              aria-invalid={isMinMaxInvalid}
              aria-describedby={isMinMaxInvalid ? "error-min-max" : undefined}
              className={`
                w-full border rounded-input pl-10 pr-4 py-2.5 text-sm
                bg-surface-0 text-ink
                focus:outline-none focus:ring-2 transition-colors
                disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
                ${isMinMaxInvalid
                  ? "border-[var(--error)] focus:ring-[var(--error)] focus:border-[var(--error)]"
                  : "border-strong focus:ring-brand-blue focus:border-brand-blue"}
              `}
            />
          </div>
        </div>

        <div className="space-y-1">
          <label
            htmlFor="valor-max"
            className="block text-xs text-ink-muted font-medium"
          >
            Máximo:
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted text-sm">
              R$
            </span>
            <input
              id="valor-max"
              type="text"
              inputMode="numeric"
              value={inputMax}
              onChange={(e) => {
                const raw = e.target.value.replace(/[^\d.,]/g, '');
                setInputMax(raw);
              }}
              onBlur={handleInputMaxBlur}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleInputMaxBlur();
                }
              }}
              placeholder="Sem limite"
              disabled={disabled}
              aria-invalid={isMinMaxInvalid}
              aria-describedby={isMinMaxInvalid ? "error-min-max" : undefined}
              className={`
                w-full border rounded-input pl-10 pr-4 py-2.5 text-sm
                bg-surface-0 text-ink
                focus:outline-none focus:ring-2 transition-colors
                disabled:bg-surface-1 disabled:text-ink-muted disabled:cursor-not-allowed
                ${isMinMaxInvalid
                  ? "border-[var(--error)] focus:ring-[var(--error)] focus:border-[var(--error)]"
                  : "border-strong focus:ring-brand-blue focus:border-brand-blue"}
              `}
            />
          </div>
        </div>
      </div>

      {/* Validation error message */}
      {isMinMaxInvalid && (
        <p id="error-min-max" role="alert" aria-live="polite" className="text-sm text-[var(--error)] font-medium">
          Valor mínimo não pode ser maior que máximo
        </p>
      )}

      {/* Helper text */}
      <p className="text-xs text-ink-muted">
        Deixe "Máximo" vazio ou selecione "Qualquer" para buscar sem limite de valor
      </p>
    </div>
  );
}

export { FAIXAS_VALOR };
