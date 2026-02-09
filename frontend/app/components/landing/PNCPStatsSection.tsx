'use client';

import { useEffect, useState } from 'react';
import { useInView } from '@/app/hooks/useInView';
import StatCard from './StatCard';
import type { PNCPStatsAPIResponse } from '@/app/types/pncp-stats';

interface PNCPStatsSectionProps {
  className?: string;
}

export default function PNCPStatsSection({ className = '' }: PNCPStatsSectionProps) {
  const { ref, isInView } = useInView({ threshold: 0.2 });
  const [stats, setStats] = useState<PNCPStatsAPIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/pncp-stats', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          // 25s client timeout (backend has 30s)
          signal: AbortSignal.timeout(25000),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data: PNCPStatsAPIResponse = await response.json();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch PNCP stats:', err);
        setError(
          err instanceof Error && err.name === 'TimeoutError'
            ? 'Timeout ao carregar estatísticas'
            : 'Erro ao carregar estatísticas'
        );
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  // Format large numbers with K/M/B suffixes
  const formatNumber = (num: number): string => {
    if (num >= 1_000_000_000) {
      return `${(num / 1_000_000_000).toFixed(1)}B`;
    }
    if (num >= 1_000_000) {
      return `${(num / 1_000_000).toFixed(1)}M`;
    }
    if (num >= 1_000) {
      return `${(num / 1_000).toFixed(0)}k`;
    }
    return num.toFixed(0);
  };

  // Format currency with B/M suffix
  const formatCurrency = (value: number): string => {
    if (value >= 1_000_000_000) {
      return `R$ ${(value / 1_000_000_000).toFixed(1)}B`;
    }
    if (value >= 1_000_000) {
      return `R$ ${(value / 1_000_000).toFixed(1)}M`;
    }
    return `R$ ${(value / 1_000).toFixed(0)}k`;
  };

  return (
    <section
      ref={ref as React.RefObject<HTMLElement>}
      className={`max-w-landing mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 ${className}`}
    >
      {/* Section title */}
      <h2
        className={`text-3xl sm:text-4xl font-bold text-center text-ink tracking-tight mb-12 transition-all duration-500 ${
          isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        Dados em tempo real do PNCP
      </h2>

      {/* Error state */}
      {error && !loading && (
        <div
          className={`text-center p-8 bg-error-subtle rounded-card border border-error/20 transition-all duration-500 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <p className="text-error font-medium">{error}</p>
          <p className="text-ink-secondary text-sm mt-2">
            Tente recarregar a página ou volte mais tarde.
          </p>
        </div>
      )}

      {/* Stats layout: Hero left + 3 smaller right */}
      {!error && (
        <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
          {/* Hero stat - annualized total bids */}
          <StatCard
            value={loading || !stats ? '...' : `${formatNumber(stats.annualized_total)}+`}
            label="licitações/ano"
            isHero
            loading={loading}
            delay={100}
            isInView={isInView}
          />

          {/* 3 smaller stats in grid */}
          <div className="flex-1 grid sm:grid-cols-3 gap-6 w-full">
            {/* Monthly bids */}
            <StatCard
              value={loading || !stats ? '...' : `${formatNumber(stats.total_bids_30d)}`}
              label="/mês processadas"
              sublabel="últimos 30 dias"
              loading={loading}
              delay={200}
              isInView={isInView}
            />

            {/* Annualized value */}
            <StatCard
              value={loading || !stats ? '...' : formatCurrency(stats.annualized_value)}
              label="valor total/ano"
              sublabel="estimado"
              loading={loading}
              delay={250}
              isInView={isInView}
            />

            {/* Total sectors */}
            <StatCard
              value={loading || !stats ? '...' : `${stats.total_sectors}`}
              label="setores"
              sublabel="disponíveis"
              loading={loading}
              delay={300}
              isInView={isInView}
            />
          </div>
        </div>
      )}

      {/* Metadata footer (only when data loaded) */}
      {stats && !loading && !error && (
        <p
          className={`text-xs text-ink-secondary/60 text-center mt-8 transition-all duration-500 delay-400 ${
            isInView ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          Dados atualizados em{' '}
          {new Date(stats.last_updated).toLocaleString('pt-BR', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      )}
    </section>
  );
}
