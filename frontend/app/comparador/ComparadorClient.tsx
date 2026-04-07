'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

const ALL_UFS = [
  { value: 'AC', label: 'Acre' },
  { value: 'AL', label: 'Alagoas' },
  { value: 'AM', label: 'Amazonas' },
  { value: 'AP', label: 'Amapá' },
  { value: 'BA', label: 'Bahia' },
  { value: 'CE', label: 'Ceará' },
  { value: 'DF', label: 'Distrito Federal' },
  { value: 'ES', label: 'Espírito Santo' },
  { value: 'GO', label: 'Goiás' },
  { value: 'MA', label: 'Maranhão' },
  { value: 'MG', label: 'Minas Gerais' },
  { value: 'MS', label: 'Mato Grosso do Sul' },
  { value: 'MT', label: 'Mato Grosso' },
  { value: 'PA', label: 'Pará' },
  { value: 'PB', label: 'Paraíba' },
  { value: 'PE', label: 'Pernambuco' },
  { value: 'PI', label: 'Piauí' },
  { value: 'PR', label: 'Paraná' },
  { value: 'RJ', label: 'Rio de Janeiro' },
  { value: 'RN', label: 'Rio Grande do Norte' },
  { value: 'RO', label: 'Rondônia' },
  { value: 'RR', label: 'Roraima' },
  { value: 'RS', label: 'Rio Grande do Sul' },
  { value: 'SC', label: 'Santa Catarina' },
  { value: 'SE', label: 'Sergipe' },
  { value: 'SP', label: 'São Paulo' },
  { value: 'TO', label: 'Tocantins' },
];

interface Bid {
  pncp_id: string;
  titulo: string;
  orgao: string;
  valor: number | null;
  uf: string;
  municipio: string;
  modalidade: string;
  data_publicacao: string;
  data_abertura: string | null;
  link_pncp: string;
}

function formatBRL(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}

function calcDaysUntil(dateStr: string | null): string {
  if (!dateStr) return '—';
  const target = new Date(dateStr);
  const now = new Date();
  const diff = Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  if (diff < 0) return 'Encerrado';
  if (diff === 0) return 'Hoje';
  return `${diff} dia${diff !== 1 ? 's' : ''}`;
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 1) + '…';
}

interface SearchSectionProps {
  onResults: (bids: Bid[]) => void;
}

function SearchSection({ onResults }: SearchSectionProps) {
  const [query, setQuery] = useState('');
  const [uf, setUf] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim().length < 3) {
      setError('Digite pelo menos 3 caracteres para buscar.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const params = new URLSearchParams({ q: query.trim() });
      if (uf) params.set('uf', uf);
      const res = await fetch(`/api/comparador/buscar?${params}`);
      const data = await res.json();
      onResults(data.bids || []);
    } catch {
      setError('Erro ao buscar editais. Tente novamente.');
      onResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ex: serviços de engenharia, TI, limpeza…"
        className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-4 py-2.5 text-[var(--ink)] placeholder:text-[var(--ink-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
        minLength={3}
        required
      />
      <select
        value={uf}
        onChange={(e) => setUf(e.target.value)}
        className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2.5 text-[var(--ink)] focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
      >
        <option value="">Todos os estados</option>
        {ALL_UFS.map((u) => (
          <option key={u.value} value={u.value}>
            {u.label} ({u.value})
          </option>
        ))}
      </select>
      <button
        type="submit"
        disabled={loading}
        className="rounded-lg bg-[var(--brand-blue)] px-6 py-2.5 font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
      >
        {loading ? 'Buscando…' : 'Buscar'}
      </button>
      {error && <p className="w-full text-sm text-red-500">{error}</p>}
    </form>
  );
}

interface BidCardProps {
  bid: Bid;
  selected: boolean;
  onAdd: () => void;
  disabled: boolean;
}

function BidCard({ bid, selected, onAdd, disabled }: BidCardProps) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
      <p className="mb-1 text-sm font-semibold text-[var(--ink)] line-clamp-2">{bid.titulo}</p>
      <p className="mb-1 text-xs text-[var(--ink-secondary)]">{bid.orgao}</p>
      <div className="mb-3 flex flex-wrap gap-2 text-xs text-[var(--ink-secondary)]">
        {bid.uf && <span className="rounded bg-[var(--surface-2)] px-2 py-0.5">{bid.uf}</span>}
        {bid.modalidade && (
          <span className="rounded bg-[var(--surface-2)] px-2 py-0.5">{bid.modalidade}</span>
        )}
        {bid.valor !== null && (
          <span className="rounded bg-[var(--surface-2)] px-2 py-0.5">{formatBRL(bid.valor)}</span>
        )}
      </div>
      <button
        onClick={onAdd}
        disabled={selected || disabled}
        className="w-full rounded-lg border border-[var(--brand-blue)] px-3 py-1.5 text-xs font-semibold text-[var(--brand-blue)] transition hover:bg-[var(--brand-blue)] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
      >
        {selected ? 'Adicionado' : 'Adicionar à comparação'}
      </button>
    </div>
  );
}

interface ComparisonColumnProps {
  bid: Bid;
  onRemove: () => void;
}

function ComparisonColumn({ bid, onRemove }: ComparisonColumnProps) {
  return (
    <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
      <p className="mb-1 text-sm font-bold text-[var(--ink)]" title={bid.titulo}>
        {truncate(bid.titulo, 90)}
      </p>
      <p className="mb-4 text-xs text-[var(--ink-secondary)]">{bid.orgao}</p>

      <dl className="flex flex-1 flex-col gap-3 text-sm">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-secondary)]">
            Valor estimado
          </dt>
          <dd className="mt-0.5 font-semibold text-[var(--ink)]">{formatBRL(bid.valor)}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-secondary)]">
            Modalidade
          </dt>
          <dd className="mt-0.5 text-[var(--ink)]">{bid.modalidade || '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-secondary)]">
            Prazo para abertura
          </dt>
          <dd className="mt-0.5 text-[var(--ink)]">{calcDaysUntil(bid.data_abertura)}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-secondary)]">
            Localização
          </dt>
          <dd className="mt-0.5 text-[var(--ink)]">
            {[bid.municipio, bid.uf].filter(Boolean).join(' — ') || '—'}
          </dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-secondary)]">
            Publicado em
          </dt>
          <dd className="mt-0.5 text-[var(--ink)]">
            {bid.data_publicacao
              ? new Date(bid.data_publicacao).toLocaleDateString('pt-BR')
              : '—'}
          </dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-col gap-2">
        {bid.link_pncp && (
          <a
            href={bid.link_pncp}
            target="_blank"
            rel="noopener noreferrer"
            className="block rounded-lg bg-[var(--brand-blue)] px-4 py-2 text-center text-xs font-semibold text-white transition hover:opacity-90"
          >
            Ver no PNCP
          </a>
        )}
        <button
          onClick={onRemove}
          className="block rounded-lg border border-[var(--border)] px-4 py-2 text-xs font-medium text-[var(--ink-secondary)] transition hover:border-red-400 hover:text-red-500"
        >
          Remover
        </button>
      </div>
    </div>
  );
}

export default function ComparadorClient() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [searchResults, setSearchResults] = useState<Bid[]>([]);
  const [selected, setSelected] = useState<Bid[]>([]);
  const [loadingIds, setLoadingIds] = useState(false);
  const [copied, setCopied] = useState(false);

  // On mount, check if ids are in URL and pre-load them
  useEffect(() => {
    const idsParam = searchParams.get('ids');
    if (!idsParam) return;
    const ids = idsParam
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 5);
    if (ids.length === 0) return;

    setLoadingIds(true);
    fetch(`/api/comparador/bids?ids=${encodeURIComponent(ids.join(','))}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.bids && data.bids.length > 0) {
          setSelected(data.bids.slice(0, 3));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingIds(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddBid = useCallback(
    (bid: Bid) => {
      if (selected.length >= 3) return;
      if (selected.some((b) => b.pncp_id === bid.pncp_id)) return;
      setSelected((prev) => [...prev, bid]);
    },
    [selected],
  );

  const handleRemoveBid = useCallback((pncpId: string) => {
    setSelected((prev) => prev.filter((b) => b.pncp_id !== pncpId));
  }, []);

  async function handleShare() {
    if (selected.length === 0) return;
    const ids = selected.map((b) => b.pncp_id).join(',');
    const url = `${window.location.origin}/comparador?ids=${encodeURIComponent(ids)}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      // Update URL without navigation
      router.replace(`/comparador?ids=${encodeURIComponent(ids)}`, { scroll: false });
    } catch {
      // Fallback: just update URL
      router.replace(`/comparador?ids=${encodeURIComponent(ids)}`, { scroll: false });
    }
  }

  return (
    <div className="space-y-10">
      {/* Search Section */}
      <section>
        <h2 className="mb-4 text-xl font-bold text-[var(--ink)]">Buscar editais</h2>
        <SearchSection onResults={setSearchResults} />
      </section>

      {/* Results Section */}
      {searchResults.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-base font-semibold text-[var(--ink)]">
              {searchResults.length} resultado{searchResults.length !== 1 ? 's' : ''} encontrado
              {searchResults.length !== 1 ? 's' : ''}
            </h3>
            {selected.length >= 3 && (
              <span className="text-xs text-[var(--ink-secondary)]">
                Máximo de 3 editais selecionados
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((bid) => (
              <BidCard
                key={bid.pncp_id}
                bid={bid}
                selected={selected.some((b) => b.pncp_id === bid.pncp_id)}
                onAdd={() => handleAddBid(bid)}
                disabled={selected.length >= 3 && !selected.some((b) => b.pncp_id === bid.pncp_id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Loading pre-selected ids from URL */}
      {loadingIds && (
        <div className="py-8 text-center text-sm text-[var(--ink-secondary)]">
          Carregando editais compartilhados…
        </div>
      )}

      {/* Comparison Section */}
      {selected.length > 0 && (
        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold text-[var(--ink)]">
              Comparando {selected.length} edital{selected.length !== 1 ? 'is' : ''}
            </h2>
            <button
              onClick={handleShare}
              className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-medium text-[var(--ink-secondary)] transition hover:border-[var(--brand-blue)] hover:text-[var(--brand-blue)]"
            >
              {copied ? (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Link copiado!
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                    />
                  </svg>
                  Compartilhar comparação
                </>
              )}
            </button>
          </div>

          <div
            className={`grid gap-4 ${
              selected.length === 1
                ? 'grid-cols-1 max-w-sm'
                : selected.length === 2
                  ? 'grid-cols-1 sm:grid-cols-2'
                  : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
            }`}
          >
            {selected.map((bid) => (
              <ComparisonColumn
                key={bid.pncp_id}
                bid={bid}
                onRemove={() => handleRemoveBid(bid.pncp_id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-6 text-center">
        <p className="mb-2 text-base font-semibold text-[var(--ink)]">
          Quer analisar editais com score de viabilidade e IA?
        </p>
        <p className="mb-4 text-sm text-[var(--ink-secondary)]">
          O SmartLic classifica automaticamente editais por relevância, modalidade, prazo e valor
          — e dá uma nota de viabilidade para você focar nas melhores oportunidades.
        </p>
        <Link
          href="/signup?ref=comparador"
          className="inline-block rounded-lg bg-[var(--brand-blue)] px-6 py-3 font-semibold text-white transition hover:opacity-90"
        >
          Testar grátis por 14 dias →
        </Link>
      </section>
    </div>
  );
}
