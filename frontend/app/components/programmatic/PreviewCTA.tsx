"use client";
/**
 * PreviewCTA — Issue #1009 (COPY-PSEO-CTA-010)
 *
 * Secondary CTA for pSEO pages: "Só quero ver os dados — Ver 3 editais grátis"
 * Opens an inline preview showing 3 free bid cards + 2-3 premium blurred cards
 * with a signup banner for the remaining count.
 *
 * Drugay UX Ethics — visitor SEO research mode: show value before paywall.
 * No auth required for the preview state.
 */

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface EditalItem {
  orgao: string;
  objeto: string;
  valor_estimado: number | null;
  data_limite: string | null;
  data_publicacao: string | null;
  link_interno: string;
}

interface RecentEditaisResponse {
  items: EditalItem[];
  total: number;
}

export interface PreviewCTAProps {
  setor: string; // URL slug, e.g. "pavimentacao-asfaltica"
  uf?: string; // UF code, e.g. "SC"
  setorLabel: string; // Human label, e.g. "Pavimentacao asfaltica"
  ufLabel: string; // Human label, e.g. "Santa Catarina"
  totalOpen?: number; // Total open editais for the banner label
  /** Pre-fetched items — when provided, skips API fetch and renders data immediately.
   *  Used by entity pages (fornecedores, orgaos, municipios) that have their own data. */
  items?: EditalItem[];
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const VISIBLE_COUNT = 3;
const PREMIUM_COUNT = 3; // blurred
const FETCH_LIMIT = VISIBLE_COUNT + PREMIUM_COUNT; // 6

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatBRL(value: number | null): string {
  if (value === null || value === undefined) return "N/I";
  if (value >= 1_000_000) {
    return `R$ ${(value / 1_000_000).toFixed(1)} M`;
  }
  if (value >= 1_000) {
    return `R$ ${(value / 1_000).toFixed(0)} mil`;
  }
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  try {
    return new Date(dateStr).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

/** Check if `?preview=true` is in the current URL (for auto-open). */
function hasPreviewParam(): boolean {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("preview") === "true";
}

/* ------------------------------------------------------------------ */
/*  Skeleton card shown while loading                                  */
/* ------------------------------------------------------------------ */

function SkeletonCard({ delay }: { delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4"
    >
      <div className="h-4 w-3/5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-3" />
      <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-2" />
      <div className="h-3 w-4/5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-3" />
      <div className="flex justify-between">
        <div className="h-3 w-1/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
        <div className="h-3 w-1/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Bid card — fully visible or blurred (premium)                     */
/* ------------------------------------------------------------------ */

function BidCard({
  item,
  isPremium,
  index,
}: {
  item: EditalItem;
  isPremium: boolean;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08 }}
      className={`rounded-xl border p-4 transition-colors ${
        isPremium
          ? "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
          : "border-brand-blue/20 dark:border-brand-blue/30 bg-white dark:bg-gray-800"
      }`}
      aria-hidden={isPremium ? "true" : undefined}
    >
      {/* Órgão */}
      <p
        className={`text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 ${
          isPremium ? "blur-[3px] select-none" : ""
        }`}
      >
        {item.orgao}
      </p>

      {/* Objeto */}
      <p
        className={`text-sm font-medium text-gray-900 dark:text-white line-clamp-2 mb-3 leading-snug ${
          isPremium ? "blur-[2px] select-none" : ""
        }`}
      >
        {item.objeto}
      </p>

      {/* Valor + Data */}
      <div className="flex items-center justify-between text-xs">
        <span
          className={`text-gray-600 dark:text-gray-400 ${
            isPremium ? "blur-[4px] select-none" : ""
          }`}
        >
          {formatBRL(item.valor_estimado)}
        </span>
        <span
          className={`text-gray-500 dark:text-gray-500 ${
            isPremium ? "blur-[3px] select-none" : ""
          }`}
        >
          {formatDate(item.data_limite)}
        </span>
      </div>

      {/* Detail link (blurred for premium) */}
      {isPremium ? (
        <div className="mt-3 h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded blur-[2px]" />
      ) : (
        <Link
          href={item.link_interno}
          className="mt-3 inline-block text-xs text-brand-blue hover:underline font-medium"
        >
          Ver detalhes →
        </Link>
      )}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

export default function PreviewCTA({
  setor,
  uf,
  setorLabel,
  ufLabel,
  totalOpen,
  items: preFetchedItems,
}: PreviewCTAProps) {
  const [isOpen, setIsOpen] = useState(hasPreviewParam);
  const [data, setData] = useState<RecentEditaisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(false);

    const params = new URLSearchParams({ setor, limit: String(FETCH_LIMIT) });
    if (uf) params.set("uf", uf);

    try {
      const res = await fetch(`/api/pseo/recent-editais?${params.toString()}`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error("Fetch failed");
      const json: RecentEditaisResponse = await res.json();
      setData(json);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [setor, uf]);

  const handleOpen = useCallback(() => {
    setIsOpen(true);

    // Track click
    if (typeof window !== "undefined") {
      window.mixpanel?.track("pseo_preview_cta_click", {
        setor,
        uf: uf ?? null,
      });
    }

    // If pre-fetched items provided, use them directly — skip API fetch
    if (preFetchedItems) {
      setData({ items: preFetchedItems, total: preFetchedItems.length });
      return;
    }

    fetchData();
  }, [setor, uf, fetchData, preFetchedItems]);

  // Auto-open if ?preview=true was in the URL on mount
  useEffect(() => {
    if (hasPreviewParam() && !data && !loading && !error) {
      if (preFetchedItems) {
        setData({ items: preFetchedItems, total: preFetchedItems.length });
      } else {
        fetchData();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const visibleItems = data?.items.slice(0, VISIBLE_COUNT) ?? [];
  const premiumItems = data?.items.slice(VISIBLE_COUNT, FETCH_LIMIT) ?? [];
  const remaining = totalOpen
    ? Math.max(0, totalOpen - VISIBLE_COUNT)
    : data
      ? Math.max(0, data.total - VISIBLE_COUNT)
      : 0;

  /* ---- CTA button (closed state) ---- */
  if (!isOpen) {
    return (
      <section
        aria-label="Preview gratuito de editais"
        className="max-w-5xl mx-auto px-4"
      >
        <button
          type="button"
          onClick={handleOpen}
          className="
            w-full sm:w-auto
            inline-flex items-center justify-center
            px-6 py-3
            bg-white dark:bg-gray-800
            text-brand-blue dark:text-brand-blue
            font-semibold text-sm sm:text-base
            rounded-xl
            border-2 border-brand-blue/40 dark:border-brand-blue/60
            hover:bg-brand-blue/5 hover:border-brand-blue
            transition-all duration-200
            shadow-sm hover:shadow-md
            cursor-pointer
          "
          data-testid="preview-cta-button"
        >
          Só quero ver os dados — Ver {VISIBLE_COUNT} editais grátis →
        </button>
      </section>
    );
  }

  /* ---- Preview state ---- */
  return (
    <AnimatePresence mode="wait">
      <section
        aria-label="Preview de editais"
        className="max-w-5xl mx-auto px-4"
        data-testid="preview-section"
      >
        {/* Loading */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: FETCH_LIMIT }).map((_, i) => (
              <SkeletonCard key={i} delay={i * 0.06} />
            ))}
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 p-6 text-center"
            data-testid="preview-error"
          >
            <p className="text-sm text-red-700 dark:text-red-400 mb-3">
              Não foi possível carregar os editais no momento.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                type="button"
                onClick={fetchData}
                className="px-4 py-2 text-sm font-medium text-red-700 dark:text-red-400 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
              >
                Tentar novamente
              </button>
              <Link
                href={`/consultoria-b2g?ref=pseo-preview-error-${setor}${uf ? `-${uf.toLowerCase()}` : ""}&utm_medium=preview_error`}
                className="px-4 py-2 text-sm font-semibold text-white bg-brand-blue rounded-lg hover:bg-blue-700 transition-colors"
                onClick={() => {
                  if (typeof window !== "undefined") {
                    window.mixpanel?.track("pseo_error_fallback_cta_click", { setor, uf: uf ?? null });
                  }
                }}
              >
                Pedir leitura à CONFENGE →
              </Link>
            </div>
          </motion.div>
        )}

        {/* Data */}
        {!loading && !error && data && (
          <>
            {/* Section heading */}
            <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">
              Últimos editais de {setorLabel}{uf ? ` em ${ufLabel}` : ""}
            </h3>

            {/* Cards grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Visible (free) */}
              {visibleItems.map((item, idx) => (
                <BidCard key={`free-${idx}`} item={item} isPremium={false} index={idx} />
              ))}

              {/* Premium (blurred) */}
              {premiumItems.map((item, idx) => (
                <BidCard
                  key={`premium-${idx}`}
                  item={item}
                  isPremium={true}
                  index={VISIBLE_COUNT + idx}
                />
              ))}
            </div>

            {/* Signup banner */}
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="mt-6 rounded-xl border border-brand-blue/30 bg-gradient-to-r from-brand-blue/5 to-blue-50 dark:from-brand-blue/10 dark:to-blue-950/20 p-5 sm:p-6 text-center"
              data-testid="preview-signup-banner"
            >
              <p className="text-base font-semibold text-gray-900 dark:text-white mb-2">
                {remaining > 0
                  ? `Peça à CONFENGE a leitura dos ${remaining} editais restantes →`
                  : "Peça à CONFENGE para monitorar novos editais →"}
              </p>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mb-4 max-w-md mx-auto">
                O dado fica público. A interpretação consultiva é da CONFENGE. Sem conta. Sem trial.
              </p>
              <Link
                href={`/consultoria-b2g?ref=pseo-preview-${setor}${uf ? `-${uf.toLowerCase()}` : ""}`}
                className="inline-block px-6 py-2.5 bg-brand-blue text-white font-semibold text-sm rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
              >
                Pedir leitura à CONFENGE →
              </Link>
            </motion.div>
          </>
        )}
      </section>
    </AnimatePresence>
  );
}
