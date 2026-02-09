"use client";

import { useState, useMemo } from "react";
import type { LicitacaoItem } from "../types";
import { StatusBadge, parseStatus, type LicitacaoStatus } from "./StatusBadge";
import { CountdownStatic, daysUntil } from "./Countdown";

/**
 * LicitacaoCard Component
 *
 * Enhanced card for displaying individual licitacao items with:
 * - Status badge (visual indicator: green=aberta, yellow=julgamento, red=encerrada)
 * - Countdown to opening date
 * - Prominent value display
 * - Matched keyword tags
 * - Quick actions: Ver Edital, Documentos, Favoritar
 *
 * Based on specification from docs/reports/especificacoes-tecnicas-melhorias-bidiq.md
 */

interface LicitacaoCardProps {
  licitacao: LicitacaoItem;
  /** Keywords that matched this licitacao (for highlighting) */
  matchedKeywords?: string[];
  /** Status string from API (will be parsed) */
  status?: string;
  /** Callback when favorite button is clicked */
  onFavorite?: (licitacao: LicitacaoItem) => void;
  /** Whether this item is favorited */
  isFavorited?: boolean;
  /** Callback when share button is clicked */
  onShare?: (licitacao: LicitacaoItem) => void;
  /** Show compact variant (less spacing, no description) */
  compact?: boolean;
  /** Additional CSS classes */
  className?: string;
}

// SVG Icons
function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}

function ExternalLinkIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
      />
    </svg>
  );
}

function HeartIcon({ className, filled }: { className?: string; filled?: boolean }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill={filled ? "currentColor" : "none"}
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={filled ? 0 : 2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
      />
    </svg>
  );
}

function ShareIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
      />
    </svg>
  );
}

function LocationIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg
              role="img"
              aria-label="Ícone"
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
  );
}

// Utility functions
function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  try {
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  } catch {
    return dateStr;
  }
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + "...";
}

export function LicitacaoCard({
  licitacao,
  matchedKeywords = [],
  status: rawStatus,
  onFavorite,
  isFavorited = false,
  onShare,
  compact = false,
  className = "",
}: LicitacaoCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Parse status
  const status: LicitacaoStatus = useMemo(() => {
    return parseStatus(rawStatus);
  }, [rawStatus]);

  // Calculate if abertura is in the future
  const hasUpcomingAbertura = useMemo(() => {
    if (!licitacao.data_abertura) return false;
    const aberturaDate = new Date(licitacao.data_abertura);
    return aberturaDate > new Date();
  }, [licitacao.data_abertura]);

  // Determine if we should show countdown
  const showCountdown = hasUpcomingAbertura && (status === "aberta" || status === "recebendo_proposta");

  // Highlight matched keywords in object text
  const highlightedObjeto = useMemo(() => {
    if (matchedKeywords.length === 0) return licitacao.objeto;

    let text = licitacao.objeto;
    matchedKeywords.forEach((keyword) => {
      const regex = new RegExp(`(${keyword})`, "gi");
      text = text.replace(regex, "**$1**");
    });
    return text;
  }, [licitacao.objeto, matchedKeywords]);

  // Handle share action
  const handleShare = async () => {
    if (onShare) {
      onShare(licitacao);
      return;
    }

    // Default share behavior using Web Share API
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Licitacao: ${truncateText(licitacao.objeto, 50)}`,
          text: `${licitacao.orgao} - ${formatCurrency(licitacao.valor)}`,
          url: licitacao.link,
        });
      } catch (err) {
        // User cancelled or share failed
        console.log("Share cancelled or failed:", err);
      }
    } else {
      // Fallback: copy link to clipboard
      try {
        await navigator.clipboard.writeText(licitacao.link);
        // Could show a toast notification here
      } catch (err) {
        console.error("Failed to copy link:", err);
      }
    }
  };

  return (
    <article
      className={`
        bg-surface-0 border border-strong rounded-card
        transition-all duration-200
        ${isHovered ? "border-brand-blue shadow-md" : ""}
        ${className}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      aria-labelledby={`licitacao-title-${licitacao.pncp_id}`}
    >
      {/* Header: Status + Modalidade + Countdown */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-4 pb-3 border-b border-strong">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={status} size="sm" />
          {licitacao.modalidade && (
            <span className="inline-flex items-center px-2 py-0.5 rounded bg-surface-2 text-ink-secondary text-xs font-medium">
              {licitacao.modalidade}
            </span>
          )}
        </div>

        {showCountdown && licitacao.data_abertura && (
          <CountdownStatic
            targetDate={licitacao.data_abertura}
            size="sm"
          />
        )}
      </div>

      {/* Main Content */}
      <div className={`p-4 ${compact ? "space-y-2" : "space-y-3"}`}>
        {/* Title/Object */}
        <h3
          id={`licitacao-title-${licitacao.pncp_id}`}
          className={`font-medium text-ink leading-snug ${compact ? "text-sm line-clamp-2" : "text-base line-clamp-3"}`}
        >
          {matchedKeywords.length > 0
            ? highlightedObjeto.split("**").map((part, i) =>
                i % 2 === 1 ? (
                  <mark
                    key={i}
                    className="bg-brand-blue-subtle text-brand-navy px-0.5 rounded"
                  >
                    {part}
                  </mark>
                ) : (
                  part
                )
              )
            : licitacao.objeto}
        </h3>

        {/* Orgao */}
        <p className="text-sm text-ink-secondary truncate">{licitacao.orgao}</p>

        {/* Location and Date Info */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
          <span className="inline-flex items-center gap-1 text-ink-muted">
            <LocationIcon className="w-4 h-4" />
            <span>
              {licitacao.uf}
              {licitacao.municipio && ` - ${licitacao.municipio}`}
            </span>
          </span>

          {licitacao.data_abertura && (
            <span className="inline-flex items-center gap-1 text-ink-muted">
              <CalendarIcon className="w-4 h-4" />
              <span>Abertura: {formatDate(licitacao.data_abertura)}</span>
            </span>
          )}
        </div>

        {/* Value - Prominent Display */}
        <div className="pt-2">
          <span className="text-2xl font-bold font-data tabular-nums text-brand-navy">
            {formatCurrency(licitacao.valor)}
          </span>
        </div>

        {/* Matched Keywords Tags */}
        {matchedKeywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-2">
            {matchedKeywords.slice(0, 5).map((keyword, idx) => (
              <span
                key={`${keyword}-${idx}`}
                className="inline-flex items-center px-2 py-0.5 rounded-full bg-brand-blue-subtle text-brand-navy text-xs font-medium"
              >
                {keyword}
              </span>
            ))}
            {matchedKeywords.length > 5 && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-surface-2 text-ink-muted text-xs">
                +{matchedKeywords.length - 5} mais
              </span>
            )}
          </div>
        )}
      </div>

      {/* Actions Footer */}
      <div className="flex items-center justify-between gap-2 p-4 pt-3 border-t border-strong bg-surface-1/50">
        {/* Primary Action: View on PNCP */}
        <a
          href={licitacao.link}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button
                     hover:bg-brand-blue-hover transition-colors"
        >
          <DocumentIcon className="w-4 h-4" />
          Ver Edital
          <ExternalLinkIcon className="w-3.5 h-3.5" />
        </a>

        {/* Secondary Actions */}
        <div className="flex items-center gap-1">
          {/* Favorite Button */}
          {onFavorite && (
            <button
              onClick={() => onFavorite(licitacao)}
              className={`p-2 rounded-button transition-colors ${
                isFavorited
                  ? "text-error bg-error-subtle"
                  : "text-ink-muted hover:text-error hover:bg-error-subtle"
              }`}
              title={isFavorited ? "Remover dos favoritos" : "Adicionar aos favoritos"}
              aria-label={isFavorited ? "Remover dos favoritos" : "Adicionar aos favoritos"}
              aria-pressed={isFavorited}
            >
              <HeartIcon className="w-5 h-5" filled={isFavorited} />
            </button>
          )}

          {/* Share Button */}
          <button
            onClick={handleShare}
            className="p-2 rounded-button text-ink-muted hover:text-brand-blue hover:bg-brand-blue-subtle transition-colors"
            title="Compartilhar"
            aria-label="Compartilhar esta licitacao"
          >
            <ShareIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </article>
  );
}

/**
 * Compact version of LicitacaoCard for list views
 */
export function LicitacaoCardCompact({
  licitacao,
  matchedKeywords,
  status,
  onFavorite,
  isFavorited,
  className,
}: Omit<LicitacaoCardProps, "compact" | "onShare">) {
  return (
    <LicitacaoCard
      licitacao={licitacao}
      matchedKeywords={matchedKeywords}
      status={status}
      onFavorite={onFavorite}
      isFavorited={isFavorited}
      compact
      className={className}
    />
  );
}

export default LicitacaoCard;
