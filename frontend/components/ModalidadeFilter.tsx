"use client";

import { useState } from "react";

/**
 * ModalidadeFilter Component
 *
 * Multi-select filter for procurement modality types.
 * Complies with Lei 14.133/2021 (Nova Lei de Licitacoes e Contratos).
 * Based on specs from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 *
 * Features:
 * - Multi-select with checkboxes
 * - 3 popular modalities always visible: Pregao Eletronico, Pregao Presencial, Dispensa
 * - Collapsible section for other modalities
 * - "Todas" and "Limpar" buttons
 * - Counter showing selected count
 * - Full keyboard accessibility
 * - ARIA compliant
 * - Visual consistency with design system
 */

export interface Modalidade {
  codigo: number;
  nome: string;
  descricao: string;
  popular?: boolean;
}

const MODALIDADES: Modalidade[] = [
  {
    codigo: 1,
    nome: "Pregao Eletronico",
    descricao: "Licitacao eletronica para bens e servicos comuns (Lei 14.133/21, Art. 6º XL)",
    popular: true,
  },
  {
    codigo: 2,
    nome: "Pregao Presencial",
    descricao: "Licitacao presencial para bens e servicos comuns (Lei 14.133/21, Art. 6º XL)",
    popular: true,
  },
  {
    codigo: 6,
    nome: "Dispensa de Licitacao",
    descricao: "Contratacao direta sem processo licitatorio (Lei 14.133/21, Art. 75)",
    popular: true,
  },
  {
    codigo: 3,
    nome: "Concorrencia",
    descricao: "Para obras e servicos de grande valor (Lei 14.133/21, Art. 28 I)",
  },
  {
    codigo: 7,
    nome: "Inexigibilidade",
    descricao: "Quando ha inviabilidade de competicao (Lei 14.133/21, Art. 74)",
  },
  {
    codigo: 9,
    nome: "Leilao",
    descricao: "Para alienacao de bens (Lei 14.133/21, Art. 28 V)",
  },
  {
    codigo: 10,
    nome: "Dialogo Competitivo",
    descricao: "Para solucoes inovadoras (Lei 14.133/21, Art. 32 VII)",
  },
  {
    codigo: 11,
    nome: "Concurso",
    descricao: "Escolha de trabalho tecnico, cientifico ou artistico (Lei 14.133/21, Art. 6º XLIV)",
  },
];

export interface ModalidadeFilterProps {
  value: number[];
  onChange: (modalidades: number[]) => void;
  disabled?: boolean;
}

export function ModalidadeFilter({
  value,
  onChange,
  disabled = false,
}: ModalidadeFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Separate popular and other modalities
  const popularModalidades = MODALIDADES.filter((m) => m.popular);
  const outrasModalidades = MODALIDADES.filter((m) => !m.popular);

  // Count selected in "outras" section
  const outrasSelectedCount = outrasModalidades.filter((m) =>
    value.includes(m.codigo)
  ).length;

  const handleToggle = (codigo: number) => {
    if (disabled) return;

    if (value.includes(codigo)) {
      onChange(value.filter((c) => c !== codigo));
    } else {
      onChange([...value, codigo]);
    }
  };

  const handleSelectAll = () => {
    if (disabled) return;
    onChange(MODALIDADES.map((m) => m.codigo));
  };

  const handleClear = () => {
    if (disabled) return;
    onChange([]);
  };

  const handleKeyDown = (
    event: React.KeyboardEvent,
    codigo: number
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleToggle(codigo);
    }
  };

  const renderCheckbox = (modalidade: Modalidade) => {
    const isChecked = value.includes(modalidade.codigo);

    return (
      <div
        key={modalidade.codigo}
        role="checkbox"
        aria-checked={isChecked}
        aria-disabled={disabled}
        tabIndex={disabled ? -1 : 0}
        onClick={() => handleToggle(modalidade.codigo)}
        onKeyDown={(e) => handleKeyDown(e, modalidade.codigo)}
        title={modalidade.descricao}
        className={`
          flex items-center gap-3 p-3 rounded-button cursor-pointer
          transition-colors duration-200
          ${disabled ? "cursor-not-allowed opacity-50" : "hover:bg-surface-1"}
          focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-inset
        `}
      >
        {/* Checkbox indicator */}
        <span
          className={`
            w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0
            transition-colors duration-200
            ${
              isChecked
                ? "bg-brand-blue border-brand-blue"
                : "border-ink-muted bg-surface-0"
            }
          `}
        >
          {isChecked && (
            <svg
              className="w-3 h-3 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={3}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </span>

        {/* Label */}
        <span className={`text-sm font-medium ${isChecked ? "text-ink" : "text-ink-secondary"}`}>
          {modalidade.nome}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Header with label and action buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <label className="text-base font-semibold text-ink">
          Modalidade de Contratacao:
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSelectAll}
            disabled={disabled}
            className={`
              text-sm font-medium text-brand-blue hover:text-brand-blue-hover
              transition-colors
              ${disabled ? "opacity-50 cursor-not-allowed" : "hover:underline"}
            `}
          >
            Todas
          </button>
          <span className="text-ink-faint">|</span>
          <button
            type="button"
            onClick={handleClear}
            disabled={disabled || value.length === 0}
            className={`
              text-sm font-medium text-ink-muted hover:text-ink
              transition-colors
              ${disabled || value.length === 0 ? "opacity-50 cursor-not-allowed" : "hover:underline"}
            `}
          >
            Limpar
          </button>
        </div>
      </div>

      {/* Popular modalities - always visible */}
      <div
        role="group"
        aria-label="Modalidades populares"
        className="grid grid-cols-1 sm:grid-cols-2 gap-1 p-3 bg-surface-1 rounded-card border border-strong"
      >
        {popularModalidades.map(renderCheckbox)}
      </div>

      {/* Collapsible section for other modalities */}
      <div>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={disabled}
          className={`
            w-full flex items-center justify-between py-2 px-3
            text-sm font-medium text-ink-secondary
            hover:text-ink transition-colors
            focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-inset rounded-button
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
          `}
          aria-expanded={isExpanded}
          aria-controls="outras-modalidades"
        >
          <span className="flex items-center gap-2">
            {isExpanded ? "Menos opcoes" : "Mais opcoes"}
            {!isExpanded && outrasSelectedCount > 0 && (
              <span className="text-brand-blue">
                ({outrasSelectedCount} selecionadas)
              </span>
            )}
          </span>
          <svg
            className={`w-5 h-5 transition-transform duration-200 ${
              isExpanded ? "rotate-180" : ""
            }`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {/* Expanded content */}
        {isExpanded && (
          <div
            id="outras-modalidades"
            role="group"
            aria-label="Outras modalidades"
            className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1 p-3 bg-surface-1 rounded-card border border-strong animate-fade-in"
          >
            {outrasModalidades.map(renderCheckbox)}
          </div>
        )}
      </div>

      {/* Counter */}
      {value.length > 0 && (
        <p className="text-sm text-ink-muted">
          {value.length}{" "}
          {value.length === 1 ? "modalidade selecionada" : "modalidades selecionadas"}
        </p>
      )}
    </div>
  );
}

export { MODALIDADES };
