"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import Link from "next/link";
import PullToRefresh from "react-simple-pull-to-refresh";
import { useAnalytics } from "../../hooks/useAnalytics";
import { useOnboarding } from "../../hooks/useOnboarding";
import { useKeyboardShortcuts, getShortcutDisplay, type KeyboardShortcut } from "../../hooks/useKeyboardShortcuts";
import { usePlan } from "../../hooks/usePlan";
import { useAuth } from "../components/AuthProvider";
import { ThemeToggle } from "../components/ThemeToggle";
import { UserMenu } from "../components/UserMenu";
import { SavedSearchesDropdown } from "../components/SavedSearchesDropdown";
import { QuotaBadge } from "../components/QuotaBadge";
import { PlanBadge } from "../components/PlanBadge";
import { MessageBadge } from "../components/MessageBadge";
import { UpgradeModal } from "../components/UpgradeModal";
import { useSearchFilters } from "./hooks/useSearchFilters";
import { useSearch } from "./hooks/useSearch";
import SearchForm from "./components/SearchForm";
import SearchResults from "./components/SearchResults";

import { dateDiffInDays } from "../../lib/utils/dateDiffInDays";

// White label branding configuration
const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME || "SmartLic.tech";

function HomePageContent() {
  const { session, loading: authLoading } = useAuth();
  const { planInfo } = usePlan();
  const { trackEvent } = useAnalytics();

  // Upgrade modal state
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [preSelectedPlan, setPreSelectedPlan] = useState<"consultor_agil" | "maquina" | "sala_guerra" | undefined>();
  const [upgradeSource, setUpgradeSource] = useState<string | undefined>();
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);

  // Onboarding
  const { shouldShowOnboarding, restartTour } = useOnboarding({
    autoStart: true,
    onComplete: () => trackEvent('onboarding_completed', { completion_time: Date.now() }),
    onDismiss: () => trackEvent('onboarding_dismissed', { dismissed_at: Date.now() }),
    onStepChange: (stepId, stepIndex) => trackEvent('onboarding_step', { step_id: stepId, step_index: stepIndex }),
  });

  // Ref to break circular dependency between hooks:
  // useSearchFilters needs clearResult (from useSearch), useSearch needs filters
  const clearResultRef = useRef<() => void>(() => {});
  const filters = useSearchFilters(() => clearResultRef.current());
  const search = useSearch(filters);
  clearResultRef.current = () => search.setResult(null);

  // Restore search state on mount
  useEffect(() => { search.restoreSearchStateOnMount(); }, []);

  // Keyboard shortcuts
  useKeyboardShortcuts({ shortcuts: [
    { key: 'k', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) search.buscar(); }, description: 'Search' },
    { key: 'a', ctrlKey: true, action: filters.selecionarTodos, description: 'Select all' },
    { key: 'Enter', ctrlKey: true, action: () => { if (filters.canSearch && !search.loading) search.buscar(); }, description: 'Search alt' },
    { key: '/', action: () => setShowKeyboardHelp(true), description: 'Show shortcuts' },
    { key: 'Escape', action: filters.limparSelecao, description: 'Clear' },
  ] });

  const handleShowUpgradeModal = (plan?: string, source?: string) => {
    setPreSelectedPlan(plan as typeof preSelectedPlan);
    setUpgradeSource(source);
    setShowUpgradeModal(true);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--brand-blue)] mx-auto mb-4"></div>
          <p className="text-[var(--ink-secondary)]">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Navigation Header */}
      <header className="border-b border-strong bg-[var(--surface-0)] sticky top-0 z-50 backdrop-blur-sm supports-[backdrop-filter]:bg-[var(--surface-0)]/95">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-xl font-bold text-brand-navy hover:text-brand-blue transition-colors">
              SmartLic<span className="text-brand-blue">.tech</span>
            </Link>
            <span className="hidden sm:block text-sm text-ink-muted font-medium border-l border-strong pl-3">
              Busca inteligente de licitações
            </span>
          </div>
          <div className="flex items-center gap-3">
            <SavedSearchesDropdown onLoadSearch={search.handleLoadSearch} onAnalyticsEvent={trackEvent} />
            <ThemeToggle />
            <MessageBadge />
            <UserMenu
              onRestartTour={!shouldShowOnboarding ? restartTour : undefined}
              statusSlot={
                <>
                  <QuotaBadge />
                  {planInfo && (
                    <PlanBadge
                      planId={planInfo.plan_id}
                      planName={planInfo.plan_name}
                      trialExpiresAt={planInfo.trial_expires_at ?? undefined}
                      onClick={() => handleShowUpgradeModal(undefined, "plan_badge")}
                    />
                  )}
                </>
              }
            />
          </div>
        </div>
      </header>

      <main id="main-content" className="max-w-4xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <PullToRefresh
          onRefresh={search.handleRefresh}
          pullingContent=""
          refreshingContent={
            <div className="flex justify-center py-4">
              <div className="w-6 h-6 border-2 border-brand-blue border-t-transparent rounded-full animate-spin" />
            </div>
          }
          resistance={3}
          className="pull-to-refresh-wrapper"
        >
          <div>
            {/* Page Title */}
            <div className="mb-8 animate-fade-in-up">
              <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink">Busca de Licitações</h1>
              <p className="text-ink-secondary mt-1 text-sm sm:text-base">
                Encontre oportunidades de contratação pública de acordo com o momento do seu negócio.
              </p>
            </div>

            <SearchForm
              {...filters}
              loading={search.loading}
              buscar={search.buscar}
              searchButtonRef={search.searchButtonRef}
              result={search.result}
              handleSaveSearch={search.handleSaveSearch}
              isMaxCapacity={search.isMaxCapacity}
              planInfo={planInfo}
              onShowUpgradeModal={handleShowUpgradeModal}
              clearResult={() => search.setResult(null)}
            />

            <SearchResults
              loading={search.loading}
              loadingStep={search.loadingStep}
              estimatedTime={search.estimateSearchTime(filters.ufsSelecionadas.size, dateDiffInDays(filters.dataInicial, filters.dataFinal))}
              stateCount={filters.ufsSelecionadas.size}
              statesProcessed={search.statesProcessed}
              onCancel={search.cancelSearch}
              sseEvent={search.sseEvent}
              useRealProgress={search.useRealProgress}
              sseAvailable={search.sseAvailable}
              onStageChange={(stage) => trackEvent('search_progress_stage', { stage, is_sse: search.useRealProgress && search.sseAvailable })}
              error={search.error}
              quotaError={search.quotaError}
              result={search.result}
              rawCount={search.rawCount}
              ufsSelecionadas={filters.ufsSelecionadas}
              sectorName={filters.sectorName}
              searchMode={filters.searchMode}
              termosArray={filters.termosArray}
              ordenacao={filters.ordenacao}
              onOrdenacaoChange={filters.setOrdenacao}
              downloadLoading={search.downloadLoading}
              downloadError={search.downloadError}
              onDownload={search.handleDownload}
              onSearch={search.buscar}
              planInfo={planInfo}
              session={session}
              onShowUpgradeModal={handleShowUpgradeModal}
              onTrackEvent={trackEvent}
            />
          </div>
        </PullToRefresh>
      </main>

      {/* Save Search Dialog */}
      {search.showSaveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
          <div className="bg-surface-0 rounded-card shadow-xl max-w-md w-full p-6 animate-fade-in-up">
            <h3 className="text-lg font-semibold text-ink mb-4">Salvar Busca</h3>
            <div className="mb-4">
              <label htmlFor="save-search-name" className="block text-sm font-medium text-ink-secondary mb-2">Nome da busca:</label>
              <input
                id="save-search-name"
                type="text"
                value={search.saveSearchName}
                onChange={(e) => search.setSaveSearchName(e.target.value)}
                placeholder="Ex: Uniformes Sul do Brasil"
                className="w-full border border-strong rounded-input px-4 py-2.5 text-base bg-surface-0 text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue transition-colors"
                maxLength={50}
                autoFocus
              />
              <p className="text-xs text-ink-muted mt-1">{search.saveSearchName.length}/50 caracteres</p>
            </div>
            {search.saveError && (
              <div className="mb-4 p-3 bg-error-subtle border border-error/20 rounded text-sm text-error" role="alert">{search.saveError}</div>
            )}
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => { search.setShowSaveDialog(false); search.setSaveSearchName(""); }}
                type="button"
                className="px-4 py-2 text-sm font-medium text-ink-secondary hover:text-ink hover:bg-surface-1 rounded-button transition-colors"
              >Cancelar</button>
              <button
                onClick={search.confirmSaveSearch}
                disabled={!search.saveSearchName.trim()}
                type="button"
                className="px-4 py-2 text-sm font-medium text-white bg-brand-navy hover:bg-brand-blue-hover rounded-button transition-colors disabled:bg-ink-faint disabled:cursor-not-allowed"
              >Salvar</button>
            </div>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      {showKeyboardHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
          <div className="bg-surface-0 rounded-card shadow-xl max-w-lg w-full p-6 animate-fade-in-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-ink">Atalhos de Teclado</h3>
              <button onClick={() => setShowKeyboardHelp(false)} type="button" className="text-ink-muted hover:text-ink transition-colors" aria-label="Fechar">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div className="space-y-3">
              {([
                ["Executar busca", { key: 'k', ctrlKey: true, action: () => {}, description: '' }],
                ["Selecionar todos os estados", { key: 'a', ctrlKey: true, action: () => {}, description: '' }],
                ["Executar busca (alternativo)", { key: 'Enter', ctrlKey: true, action: () => {}, description: '' }],
              ] as [string, KeyboardShortcut][]).map(([label, shortcut]) => (
                <div key={label} className="flex items-center justify-between py-2 border-b border-strong">
                  <span className="text-ink">{label}</span>
                  <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">
                    {getShortcutDisplay(shortcut)}
                  </kbd>
                </div>
              ))}
              <div className="flex items-center justify-between py-2 border-b border-strong">
                <span className="text-ink">Limpar todos os filtros</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">Ctrl+Shift+L</kbd>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-strong">
                <span className="text-ink">Limpar seleção</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">Esc</kbd>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-ink">Mostrar atalhos</span>
                <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">/</kbd>
              </div>
            </div>
            <button
              onClick={() => setShowKeyboardHelp(false)}
              type="button"
              className="mt-4 w-full px-4 py-2 text-sm font-medium text-white bg-brand-navy hover:bg-brand-blue-hover rounded-button transition-colors"
            >Entendi</button>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-surface-1 text-ink border-t border-[var(--border)] mt-12" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Sobre</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/#sobre" className="hover:text-brand-blue transition-colors">Quem somos</a></li>
                <li><a href="/#como-funciona" className="hover:text-brand-blue transition-colors">Como funciona</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Planos</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/planos" className="hover:text-brand-blue transition-colors">Planos e Preços</a></li>
                <li><button onClick={() => setShowKeyboardHelp(true)} className="hover:text-brand-blue transition-colors text-left">Atalhos de Teclado</button></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Suporte</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/mensagens" className="hover:text-brand-blue transition-colors">Central de Ajuda</a></li>
                <li><a href="/mensagens" className="hover:text-brand-blue transition-colors">Contato</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4 text-ink">Legal</h3>
              <ul className="space-y-2 text-sm text-ink-secondary">
                <li><a href="/privacidade" className="hover:text-brand-blue transition-colors">Política de Privacidade</a></li>
                <li><a href="/termos" className="hover:text-brand-blue transition-colors">Termos de Uso</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[var(--border-strong)] pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-sm text-ink-secondary">© 2026 {APP_NAME}. Todos os direitos reservados.</p>
              <p className="text-sm text-ink-secondary">Sistema desenvolvido por servidores públicos</p>
            </div>
          </div>
        </div>
      </footer>

      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        preSelectedPlan={preSelectedPlan}
        source={upgradeSource}
      />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[var(--canvas)]">
        <p className="text-[var(--ink-secondary)]">Carregando...</p>
      </div>
    }>
      <HomePageContent />
    </Suspense>
  );
}
