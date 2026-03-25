"use client";

import { Dialog } from "../../components/Dialog";
import { UpgradeModal } from "../../components/UpgradeModal";
import { TrialConversionScreen } from "../../components/TrialConversionScreen";
import { OnboardingTourButton } from "../../../components/OnboardingTourButton";
import { PaymentRecoveryModal } from "../../../components/billing/PaymentRecoveryModal";
import PdfOptionsModal from "../../../components/reports/PdfOptionsModal";
import { Button } from "../../../components/ui/button";
import { getShortcutDisplay, type KeyboardShortcut } from "../../../hooks/useKeyboardShortcuts";
import type { TrialValue } from "../constants/tour-steps";

interface BuscarModalsProps {
  // Save Search
  showSaveDialog: boolean;
  onCloseSaveDialog: () => void;
  saveSearchName: string;
  onSaveSearchNameChange: (name: string) => void;
  saveError: string | null;
  onConfirmSave: () => void;

  // Keyboard Help
  showKeyboardHelp: boolean;
  onCloseKeyboardHelp: () => void;

  // Upgrade
  showUpgradeModal: boolean;
  onCloseUpgradeModal: () => void;
  upgradeSource?: string;

  // PDF
  pdfModalOpen: boolean;
  onClosePdfModal: () => void;
  onGeneratePdf: (options: { clientName: string; maxItems: number }) => void;
  pdfLoading: boolean;
  sectorName: string;
  totalResults: number;

  // Trial Conversion
  showTrialConversion: boolean;
  trialValue: TrialValue | null;
  trialValueLoading: boolean;
  onCloseTrialConversion: () => void;

  // Tour
  restartSearchTour: () => void;
  restartResultsTour: () => void;

  // Payment Recovery
  showPaymentRecovery: boolean;
  graceDaysRemaining: number;
  onClosePaymentRecovery: () => void;
}

export function BuscarModals({
  showSaveDialog,
  onCloseSaveDialog,
  saveSearchName,
  onSaveSearchNameChange,
  saveError,
  onConfirmSave,
  showKeyboardHelp,
  onCloseKeyboardHelp,
  showUpgradeModal,
  onCloseUpgradeModal,
  upgradeSource,
  pdfModalOpen,
  onClosePdfModal,
  onGeneratePdf,
  pdfLoading,
  sectorName,
  totalResults,
  showTrialConversion,
  trialValue,
  trialValueLoading,
  onCloseTrialConversion,
  restartSearchTour,
  restartResultsTour,
  showPaymentRecovery,
  graceDaysRemaining,
  onClosePaymentRecovery,
}: BuscarModalsProps) {
  return (
    <>
      {/* Save Search Dialog */}
      <Dialog
        isOpen={showSaveDialog}
        onClose={onCloseSaveDialog}
        title="Salvar Análise"
        className="max-w-md"
        id="save-search"
      >
        <div className="mb-4">
          <label htmlFor="save-search-name" className="block text-sm font-medium text-ink-secondary mb-2">Nome da análise:</label>
          <input
            id="save-search-name"
            type="text"
            value={saveSearchName}
            onChange={(e) => onSaveSearchNameChange(e.target.value)}
            placeholder="Ex: Informatica Sul do Brasil"
            className="w-full border border-strong rounded-input px-4 py-2.5 text-base bg-surface-0 text-ink focus:outline-none focus:ring-2 focus:ring-brand-blue focus:border-brand-blue transition-colors"
            maxLength={50}
            autoFocus
          />
          <p className="text-xs text-ink-muted mt-1">{(saveSearchName ?? '').length}/50 caracteres</p>
        </div>
        {saveError && (
          <div className="mb-4 p-3 bg-error-subtle border border-error/20 rounded text-sm text-error" role="alert">{saveError}</div>
        )}
        <div className="flex gap-3 justify-end">
          <Button variant="ghost" onClick={onCloseSaveDialog} type="button">Cancelar</Button>
          <Button variant="primary" onClick={onConfirmSave} disabled={!(saveSearchName ?? '').trim()} type="button">Salvar</Button>
        </div>
      </Dialog>

      {/* Keyboard Shortcuts Help */}
      <Dialog
        isOpen={showKeyboardHelp}
        onClose={onCloseKeyboardHelp}
        title="Atalhos de Teclado"
        className="max-w-lg"
        id="keyboard-help"
      >
        <div className="space-y-3">
          {([
            ["Executar analise", { key: 'k', ctrlKey: true, action: () => {}, description: '' }],
            ["Selecionar todos os estados", { key: 'a', ctrlKey: true, action: () => {}, description: '' }],
            ["Executar analise (alternativo)", { key: 'Enter', ctrlKey: true, action: () => {}, description: '' }],
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
            <span className="text-ink">Limpar selecao</span>
            <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">Esc</kbd>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-ink">Mostrar atalhos</span>
            <kbd className="px-3 py-1.5 bg-surface-2 rounded text-sm font-mono border border-strong">/</kbd>
          </div>
        </div>
        <Button variant="primary" className="mt-4 w-full" onClick={onCloseKeyboardHelp} type="button">Entendi</Button>
      </Dialog>

      <UpgradeModal isOpen={showUpgradeModal} onClose={onCloseUpgradeModal} source={upgradeSource} />

      <PdfOptionsModal
        isOpen={pdfModalOpen}
        onClose={onClosePdfModal}
        onGenerate={onGeneratePdf}
        isGenerating={pdfLoading}
        sectorName={sectorName}
        totalResults={totalResults}
      />

      {showTrialConversion && (
        <TrialConversionScreen
          trialValue={trialValue}
          onClose={onCloseTrialConversion}
          loading={trialValueLoading}
        />
      )}

      <OnboardingTourButton
        availableTours={{
          search: restartSearchTour,
          results: restartResultsTour,
        }}
      />

      {showPaymentRecovery && (
        <PaymentRecoveryModal
          daysRemaining={graceDaysRemaining}
          trialValue={trialValue}
          onClose={onClosePaymentRecovery}
        />
      )}
    </>
  );
}
