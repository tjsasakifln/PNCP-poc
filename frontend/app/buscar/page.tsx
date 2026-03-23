"use client";

import { Suspense } from "react";
import Link from "next/link";
import PullToRefresh from "react-simple-pull-to-refresh";

import SearchForm from "./components/SearchForm";
import SearchResults from "./components/SearchResults";
import { SearchErrorBoundary } from "./components/SearchErrorBoundary";
import { OnboardingBanner } from "./components/OnboardingBanner";
import { OnboardingSuccessBanner } from "./components/OnboardingSuccessBanner";
import { OnboardingEmptyState } from "./components/OnboardingEmptyState";
import { BuscarModals } from "./components/BuscarModals";
import { useSearchOrchestration } from "./hooks/useSearchOrchestration";

import BackendStatusIndicator from "../components/BackendStatusIndicator";
import { MobileDrawer } from "../../components/MobileDrawer";
import { SavedSearchesDropdown } from "../components/SavedSearchesDropdown";
import { ThemeToggle } from "../components/ThemeToggle";
import { UserMenu } from "../components/UserMenu";
import { QuotaBadge } from "../components/QuotaBadge";
import { PlanBadge } from "../components/PlanBadge";
import { TrialCountdown } from "../components/TrialCountdown";
import { TrialExpiringBanner } from "../components/TrialExpiringBanner";
import { Button } from "../../components/ui/button";
import { APP_NAME } from "../../lib/config";

function HomePageContent() {
  const orch = useSearchOrchestration();

  if (orch.authLoading) {
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
      {/* Page Header */}
      <header className="sticky top-0 z-40 bg-[var(--surface-0)] backdrop-blur-sm supports-[backdrop-filter]:bg-[var(--surface-0)]/95 border-b border-[var(--border)] shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            <Link href="/buscar" className="lg:hidden text-xl font-bold text-brand-navy hover:text-brand-blue transition-colors">
              SmartLic<span className="text-brand-blue">.tech</span>
            </Link>
            <span className="hidden lg:block text-base font-semibold text-[var(--ink)]">
              Buscar Licitações
            </span>
          </div>

          {/* UX-340 AC1: Mobile hamburger */}
          <button
            onClick={() => orch.setDrawerOpen(true)}
            className="lg:hidden flex items-center gap-1.5 min-w-[44px] min-h-[44px] px-3 rounded-lg text-[var(--ink-secondary)] hover:text-[var(--ink)] hover:bg-[var(--surface-1)] transition-colors"
            aria-label="Abrir menu"
            data-testid="mobile-menu-button"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
            <span className="text-sm font-medium">Menu</span>
          </button>

          {/* Desktop controls */}
          <div className="hidden lg:flex items-center gap-2 sm:gap-3">
            <BackendStatusIndicator />
            <SavedSearchesDropdown onLoadSearch={orch.search.handleLoadSearch} onAnalyticsEvent={orch.trackEvent} />
            <ThemeToggle />
            <UserMenu
              onRestartTour={!orch.shouldShowOnboarding ? orch.restartTour : undefined}
              statusSlot={
                <>
                  <QuotaBadge />
                  {orch.planInfo && (
                    <PlanBadge
                      planId={orch.planInfo.plan_id}
                      planName={orch.planInfo.plan_name}
                      trialExpiresAt={orch.planInfo.trial_expires_at ?? undefined}
                      onClick={() => orch.handleShowUpgradeModal(undefined, "plan_badge")}
                    />
                  )}
                  {orch.trialDaysRemaining !== null && orch.trialDaysRemaining > 0 && (
                    <TrialCountdown daysRemaining={orch.trialDaysRemaining} />
                  )}
                </>
              }
            />
          </div>
        </div>
      </header>

      <MobileDrawer open={orch.drawerOpen} onClose={() => orch.setDrawerOpen(false)} />

      <main id="buscar-content" className="max-w-5xl mx-auto px-4 py-6 sm:px-6 sm:py-8">
        <PullToRefresh
          onRefresh={orch.search.handleRefresh}
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
            {/* Trial expiring banner */}
            {orch.trialDaysRemaining !== null && orch.trialDaysRemaining <= 1 && !orch.isTrialExpired && (
              <TrialExpiringBanner
                daysRemaining={orch.trialDaysRemaining}
                onConvert={() => {
                  orch.setShowTrialConversion(true);
                  orch.fetchTrialValue();
                }}
              />
            )}

            {/* Page Title */}
            <div className="mb-8 animate-fade-in-up">
              <h1 className="text-2xl sm:text-3xl font-bold font-display text-ink">Análise de Licitações</h1>
              <p className="text-ink-secondary mt-1 text-sm sm:text-base">
                Encontre oportunidades de contratação pública de acordo com o momento do seu negócio.
              </p>
            </div>

            <SearchForm
              {...orch.filters}
              loading={orch.search.loading}
              buscar={orch.buscarWithCollapse}
              searchButtonRef={orch.search.searchButtonRef}
              result={orch.search.result}
              handleSaveSearch={orch.search.handleSaveSearch}
              isMaxCapacity={orch.search.isMaxCapacity}
              planInfo={orch.planInfo}
              onShowUpgradeModal={orch.handleShowUpgradeModal}
              clearResult={() => orch.search.setResult(null)}
              customizeOpen={orch.customizeOpen}
              setCustomizeOpen={orch.setCustomizeOpen}
              showFirstUseTip={orch.showFirstUseTip}
              onDismissFirstUseTip={orch.dismissFirstUseTip}
              isTrialExpired={orch.isTrialExpired || orch.search.quotaError === "trial_expired"}
              isGracePeriod={orch.isGracePeriod}
            />

            {/* GTM-004: Auto-search banners */}
            {orch.showOnboardingBanner && !orch.autoSearchDismissed && orch.search.loading && (
              <OnboardingBanner />
            )}
            {orch.showOnboardingBanner && !orch.autoSearchDismissed && !orch.search.loading && orch.search.result && orch.search.result.resumo.total_oportunidades > 0 && (
              <OnboardingSuccessBanner
                count={orch.search.result.resumo.total_oportunidades}
                onDismiss={() => {
                  orch.setAutoSearchDismissed(true);
                  orch.setShowOnboardingBanner(false);
                }}
              />
            )}
            {orch.showOnboardingBanner && !orch.autoSearchDismissed && !orch.search.loading && orch.search.result && orch.search.result.resumo.total_oportunidades === 0 && (
              <OnboardingEmptyState
                onAdjustFilters={() => {
                  orch.setAutoSearchDismissed(true);
                  orch.setShowOnboardingBanner(false);
                }}
              />
            )}

            {/* Scroll target for progress area */}
            <div ref={orch.progressAreaRef} />

            {/* Error boundary wraps results area */}
            <SearchErrorBoundary onReset={orch.handleErrorBoundaryReset}>
              <SearchResults {...orch.searchResultsProps} />
            </SearchErrorBoundary>
          </div>
        </PullToRefresh>
      </main>

      {/* DEBT-111 AC9: Feature-rich search footer — intentional dual-footer with NavigationShell minimal footer (SAB-013 AC7, DEBT-105 AC8) */}
      <footer className="bg-surface-1 text-ink border-t border-[var(--border)] mt-12" aria-label="Links uteis da busca">
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
                <li><a href="/planos" className="hover:text-brand-blue transition-colors">Planos e Precos</a></li>
                <li><button onClick={() => orch.setShowKeyboardHelp(true)} className="hover:text-brand-blue transition-colors text-left">Atalhos de Teclado</button></li>
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
                <li><a href="/privacidade" className="hover:text-brand-blue transition-colors">Politica de Privacidade</a></li>
                <li><a href="/termos" className="hover:text-brand-blue transition-colors">Termos de Uso</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[var(--border-strong)] pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-sm text-ink-secondary">© 2026 {APP_NAME}. Todos os direitos reservados.</p>
              <p className="text-sm text-ink-secondary">CONFENGE Avaliacoes e Inteligencia Artificial LTDA</p>
            </div>
          </div>
        </div>
      </footer>

      <BuscarModals
        showSaveDialog={orch.search.showSaveDialog}
        onCloseSaveDialog={() => { orch.search.setShowSaveDialog(false); orch.search.setSaveSearchName(""); }}
        saveSearchName={orch.search.saveSearchName}
        onSaveSearchNameChange={orch.search.setSaveSearchName}
        saveError={orch.search.saveError}
        onConfirmSave={orch.search.confirmSaveSearch}
        showKeyboardHelp={orch.showKeyboardHelp}
        onCloseKeyboardHelp={() => orch.setShowKeyboardHelp(false)}
        showUpgradeModal={orch.showUpgradeModal}
        onCloseUpgradeModal={() => orch.setShowUpgradeModal(false)}
        upgradeSource={orch.upgradeSource}
        pdfModalOpen={orch.pdfModalOpen}
        onClosePdfModal={() => orch.setPdfModalOpen(false)}
        onGeneratePdf={orch.handleGeneratePdf}
        pdfLoading={orch.pdfLoading}
        sectorName={orch.filters.sectorName}
        totalResults={orch.search.result?.resumo?.total_oportunidades ?? 0}
        showTrialConversion={orch.showTrialConversion}
        trialValue={orch.trialValue}
        trialValueLoading={orch.trialValueLoading}
        onCloseTrialConversion={() => {
          orch.setShowTrialConversion(false);
          orch.router.push("/planos");
        }}
        restartSearchTour={orch.restartSearchTour}
        restartResultsTour={orch.restartResultsTour}
        showPaymentRecovery={orch.showPaymentRecovery}
        graceDaysRemaining={orch.graceDaysRemaining}
        onClosePaymentRecovery={() => orch.setShowPaymentRecovery(false)}
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
