'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { Tour, type TourStepDef } from '../../components/tour/Tour';
import { MOCK_BIDS, DEMO_SECTOR, DEMO_UF, formatBRL, getViabilityColor } from './mock-data';

type DemoState = 'idle' | 'selecting' | 'searching' | 'results' | 'detail';

const SECTORS = [
  { id: 'engenharia', name: 'Engenharia e Construção' },
  { id: 'ti', name: 'Tecnologia da Informação' },
  { id: 'saude', name: 'Saúde e Farmácia' },
  { id: 'limpeza', name: 'Limpeza e Conservação' },
];

const UFS = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'GO'];

const PERIODS = [
  { value: '10', label: 'Últimos 10 dias' },
  { value: '20', label: 'Últimos 20 dias' },
  { value: '30', label: 'Últimos 30 dias' },
];

const VIABILITY_FACTORS = [
  { key: 'modalidade' as const, label: 'Modalidade', weight: 30 },
  { key: 'prazo' as const, label: 'Prazo', weight: 25 },
  { key: 'valor' as const, label: 'Valor', weight: 25 },
  { key: 'geografia' as const, label: 'Geografia', weight: 20 },
];

export default function DemoClient() {
  const [state, setState] = useState<DemoState>('selecting');
  const [selectedBidId, setSelectedBidId] = useState<string | null>(null);
  const [tourCompleted, setTourCompleted] = useState(false);
  const [tourActive, setTourActive] = useState(false);
  const stateRef = useRef<DemoState>('selecting');

  // Keep stateRef in sync so beforeShowPromise closures can read current state
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const transitionTo = useCallback((next: DemoState): Promise<void> => {
    return new Promise((resolve) => {
      setState(next);
      stateRef.current = next;
      // Give React time to render the new state before the tour attaches
      setTimeout(resolve, 350);
    });
  }, []);

  const startSearchAnimation = useCallback((): Promise<void> => {
    return new Promise((resolve) => {
      setState('searching');
      stateRef.current = 'searching';
      setTimeout(() => {
        setState('results');
        stateRef.current = 'results';
        setTimeout(resolve, 350);
      }, 2000);
    });
  }, []);

  // Tour steps: beforeShow replaces shepherd's beforeShowPromise.
  // Defined via useMemo so closures capture stable transitionTo/startSearchAnimation refs.
  const demoTourSteps: TourStepDef[] = useMemo(
    () => [
      {
        id: 'demo-step-1',
        title: 'Selecione seu setor de atuação',
        text: 'O SmartLic classifica editais por setor usando IA. Escolha entre 15 setores pré-configurados — cada um com keywords, exclusões e faixas de valor ideais.',
        attachTo: { selector: '[data-tour="demo-sector"]', placement: 'bottom' },
        beforeShow: () => transitionTo('selecting'),
      },
      {
        id: 'demo-step-2',
        title: 'Inicie a busca multi-fonte',
        text: 'Um clique aciona busca simultânea no PNCP, Portal de Compras Públicas e ComprasGov. O SmartLic deduplica e normaliza resultados de todas as fontes automaticamente.',
        attachTo: { selector: '[data-tour="demo-search"]', placement: 'bottom' },
        beforeShow: () => transitionTo('selecting'),
      },
      {
        id: 'demo-step-3',
        title: 'Resultados com score de viabilidade',
        text: 'Cada edital recebe um score de 0–100 calculado com 4 fatores: modalidade (30%), prazo (25%), valor (25%) e geografia (20%). Verde = alta viabilidade.',
        attachTo: { selector: '[data-tour="demo-results"]', placement: 'top' },
        beforeShow: startSearchAnimation,
      },
      {
        id: 'demo-step-4',
        title: 'Análise detalhada com 4 fatores',
        text: 'Expanda qualquer edital para ver o detalhamento fator a fator com justificativa em linguagem natural. Chega de decisões no feeling — tome decisões baseadas em dados.',
        attachTo: { selector: '[data-tour="demo-analysis"]', placement: 'top' },
        beforeShow: async () => {
          setSelectedBidId(MOCK_BIDS[0].id);
          await transitionTo('detail');
        },
      },
    ],
    [transitionTo, startSearchAnimation],
  );

  // Auto-start after a short delay so the page finishes rendering
  useEffect(() => {
    const timer = setTimeout(() => setTourActive(true), 600);
    return () => { clearTimeout(timer); setTourActive(false); };
  }, []);

  const selectedBid = selectedBidId ? MOCK_BIDS.find((b) => b.id === selectedBidId) ?? MOCK_BIDS[0] : MOCK_BIDS[0];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">

      {/* Mock search form */}
      {(state === 'idle' || state === 'selecting') && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-[var(--ink)] mb-5">Configure sua busca</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            {/* Sector selector */}
            <div data-tour="demo-sector">
              <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1.5">
                Setor de atuação
              </label>
              <select
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue={DEMO_SECTOR.id}
              >
                {SECTORS.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            {/* UF selector */}
            <div data-tour="demo-uf">
              <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1.5">
                Estado (UF)
              </label>
              <select
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue={DEMO_UF}
              >
                {UFS.map((uf) => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>

            {/* Period selector */}
            <div data-tour="demo-period">
              <label className="block text-sm font-medium text-[var(--ink-secondary)] mb-1.5">
                Período
              </label>
              <select
                className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-[var(--ink)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue="10"
              >
                {PERIODS.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Source indicators */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['PNCP', 'Portal de Compras', 'ComprasGov'].map((src) => (
              <span key={src} className="inline-flex items-center gap-1.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-2.5 py-1 rounded-full font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 inline-block" />
                {src}
              </span>
            ))}
          </div>

          <button
            data-tour="demo-search"
            onClick={() => {
              setState('searching');
              setTimeout(() => setState('results'), 2000);
            }}
            className="w-full sm:w-auto px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-colors text-sm shadow-sm"
          >
            Buscar editais
          </button>
        </div>
      )}

      {/* Loading / searching state */}
      {state === 'searching' && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-10 shadow-sm text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
            </svg>
            <span className="text-[var(--ink)] font-medium">Buscando editais em 3 fontes…</span>
          </div>
          <div className="max-w-xs mx-auto space-y-2">
            {['PNCP', 'Portal de Compras', 'ComprasGov'].map((src, i) => (
              <div key={src} className="flex items-center gap-3 text-sm">
                <div className="flex-1 h-1.5 bg-[var(--surface-0)] rounded-full overflow-hidden">
                  {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width and transition are computed from source index for demo animation */}
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all"
                    style={{ width: i === 0 ? '100%' : i === 1 ? '70%' : '40%', transition: 'width 1.5s ease' }}
                  />
                </div>
                <span className="text-[var(--ink-secondary)] w-32 text-right">{src}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-[var(--ink-secondary)] mt-4">Classificando relevância com IA…</p>
        </div>
      )}

      {/* Results list */}
      {(state === 'results' || state === 'detail') && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-[var(--ink)]">
              {MOCK_BIDS.length} editais encontrados em {DEMO_UF} — {DEMO_SECTOR.name}
            </h2>
            <button
              onClick={() => setState('selecting')}
              className="text-sm text-blue-600 hover:underline"
            >
              ← Nova busca
            </button>
          </div>

          <div data-tour="demo-results" className="space-y-3">
            {MOCK_BIDS.map((bid) => {
              const color = getViabilityColor(bid.viability_score);
              const isSelected = state === 'detail' && bid.id === selectedBidId;

              return (
                <article
                  key={bid.id}
                  className={`bg-[var(--surface-1)] border rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${isSelected ? 'border-blue-400 ring-1 ring-blue-400/30 shadow-md' : 'border-[var(--border)]'}`}
                  onClick={() => {
                    setSelectedBidId(bid.id);
                    setState('detail');
                  }}
                >
                  <div className="flex items-start gap-3">
                    {/* Viability score badge */}
                    <div className={`flex-none w-12 h-12 rounded-xl flex flex-col items-center justify-center ring-1 ${color.bg} ${color.ring}`}>
                      <span className={`text-lg font-bold leading-none ${color.text}`}>{bid.viability_score}</span>
                      <span className={`text-[10px] font-medium ${color.text} opacity-80`}>score</span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-semibold text-[var(--ink)] leading-snug line-clamp-2 mb-1">
                        {bid.titulo}
                      </h3>
                      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-[var(--ink-secondary)]">
                        <span>{bid.orgao}</span>
                        <span>{bid.municipio}</span>
                        <span className="bg-[var(--surface-0)] px-1.5 py-0.5 rounded font-medium">{bid.modalidade}</span>
                        <span className="text-blue-600 dark:text-blue-400 font-semibold">{formatBRL(bid.valor)}</span>
                      </div>
                      <p className="text-xs text-[var(--ink-secondary)] mt-1">
                        Publicado: {bid.data_publicacao} · Abertura: {bid.data_abertura}
                      </p>
                    </div>

                    <svg className="flex-none w-4 h-4 text-[var(--ink-secondary)] mt-1 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      )}

      {/* Expanded detail / 4-factor analysis */}
      {state === 'detail' && (
        <div data-tour="demo-analysis" className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-semibold text-[var(--ink)]">Análise de Viabilidade — 4 Fatores</h3>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold ring-1 ${getViabilityColor(selectedBid.viability_score).bg} ${getViabilityColor(selectedBid.viability_score).text} ${getViabilityColor(selectedBid.viability_score).ring}`}>
              Score: {selectedBid.viability_score}/100
            </div>
          </div>

          <p className="text-sm text-[var(--ink-secondary)] mb-5 line-clamp-2">{selectedBid.titulo}</p>

          <div className="space-y-4">
            {VIABILITY_FACTORS.map(({ key, label, weight }) => {
              const factor = selectedBid.viability_factors[key];
              const color = getViabilityColor(factor.score);
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[var(--ink)]">{label}</span>
                      <span className="text-xs text-[var(--ink-secondary)] bg-[var(--surface-0)] px-1.5 py-0.5 rounded">{weight}%</span>
                    </div>
                    <span className={`text-sm font-bold ${color.text}`}>{factor.score}/100</span>
                  </div>
                  <div className="h-2 bg-[var(--surface-0)] rounded-full overflow-hidden mb-1.5">
                    {/* eslint-disable-next-line local-rules/no-inline-styles -- DYNAMIC: width is computed from viability factor score */}
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${factor.score >= 70 ? 'bg-emerald-500' : factor.score >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                      style={{ width: `${factor.score}%` }}
                    />
                  </div>
                  <p className="text-xs text-[var(--ink-secondary)]">{factor.label}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border)] flex flex-col sm:flex-row gap-3">
            <Link
              href={`/signup?ref=demo&utm_source=demo&utm_medium=analysis_cta`}
              className="flex-1 text-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-colors"
            >
              Analisar editais reais da minha empresa →
            </Link>
            <button
              onClick={() => setState('results')}
              className="px-4 py-2.5 border border-[var(--border)] text-[var(--ink)] rounded-xl text-sm hover:bg-[var(--surface-0)] transition-colors"
            >
              Ver todos os resultados
            </button>
          </div>
        </div>
      )}

      {/* Always-visible CTA */}
      <div className="border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-semibold text-[var(--ink)] text-sm mb-0.5">
            Pronto para buscar editais reais da sua empresa?
          </p>
          <p className="text-xs text-[var(--ink-secondary)]">
            14 dias grátis · Sem cartão de crédito · Dados reais do PNCP
          </p>
        </div>
        <Link
          href="/signup?ref=demo&utm_source=demo&utm_medium=footer_cta"
          className="flex-none px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-colors whitespace-nowrap shadow-sm"
        >
          Começar grátis →
        </Link>
      </div>

      <Tour
        tourId="demo"
        steps={demoTourSteps}
        active={tourActive}
        onComplete={() => { setTourCompleted(true); setTourActive(false); }}
        onSkip={() => { setTourCompleted(true); setTourActive(false); }}
      />

      {/* Post-tour CTA card */}
      {tourCompleted && (
        <div className="rounded-2xl border-2 border-blue-400 dark:border-blue-600 bg-gradient-to-br from-blue-600 to-blue-800 text-white p-8 text-center shadow-lg">
          <div className="text-4xl mb-3">✓</div>
          <h3 className="text-xl font-bold mb-2">Demo concluído!</h3>
          <p className="text-blue-100 text-sm mb-6 max-w-md mx-auto">
            Você acabou de ver como o SmartLic funciona com dados de demo. Agora experimente com editais reais do seu setor — é gratuito por 14 dias.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/signup?ref=demo&utm_source=demo&utm_medium=tour_complete"
              className="px-8 py-3 bg-white text-blue-700 font-bold rounded-xl hover:bg-blue-50 transition-colors"
            >
              Criar conta gratuita →
            </Link>
            <Link
              href="/planos"
              className="px-8 py-3 bg-blue-700/60 hover:bg-blue-700/80 text-white font-semibold rounded-xl transition-colors"
            >
              Ver planos
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
