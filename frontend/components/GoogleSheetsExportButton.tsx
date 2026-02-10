'use client';

/**
 * Google Sheets Export Button Component
 *
 * Provides one-click export of search results to Google Sheets.
 * Handles OAuth flow, loading states, and error messages.
 *
 * Features:
 * - Auto-redirect to OAuth consent if not authorized
 * - Opens spreadsheet in new tab on success
 * - Toast notifications for success/error
 * - Disabled state when no results
 *
 * STORY-180: Google Sheets Export
 */

import { useState } from 'react';
import { FileSpreadsheet, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface GoogleSheetsExportButtonProps {
  /** List of licitações to export */
  licitacoes: any[];
  /** Label for spreadsheet title (e.g., "Uniformes - SP, RJ") */
  searchLabel: string;
  /** Disable button (e.g., while search is loading) */
  disabled?: boolean;
  /** Session object with access_token (from useAuth) */
  session?: any;
}

export default function GoogleSheetsExportButton({
  licitacoes,
  searchLabel,
  disabled = false,
  session
}: GoogleSheetsExportButtonProps) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    // Check authentication
    if (!session?.access_token) {
      toast.error('Você precisa estar logado para exportar');
      window.location.href = '/login';
      return;
    }

    // Validate data
    if (!licitacoes || licitacoes.length === 0) {
      toast.error('Nenhum resultado para exportar');
      return;
    }

    setExporting(true);

    try {
      // Call export API
      const response = await fetch('/api/export/google-sheets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          licitacoes,
          title: `SmartLic - ${searchLabel} - ${new Date().toLocaleDateString('pt-BR')}`,
          mode: 'create'
        })
      });

      // Handle OAuth required (401)
      if (response.status === 401) {
        const error = await response.json();

        // Check if it's OAuth-specific error
        if (error.detail?.includes('Google Sheets') || error.detail?.includes('autorizado')) {
          toast.info('Conectando ao Google Sheets...', {
            description: 'Você será redirecionado para autorizar o acesso'
          });

          // Redirect to OAuth flow
          const currentPath = window.location.pathname + window.location.search;
          const redirectUrl = `/api/auth/google?redirect=${encodeURIComponent(currentPath)}`;

          setTimeout(() => {
            window.location.href = redirectUrl;
          }, 1500);
          return;
        }

        throw new Error(error.detail || 'Autenticação necessária');
      }

      // Handle other HTTP errors
      if (!response.ok) {
        const error = await response.json();

        // Handle specific error codes
        if (response.status === 403) {
          throw new Error(
            'Sem permissão para acessar Google Sheets. ' +
            'Revogue e reconecte sua conta Google nas configurações.'
          );
        } else if (response.status === 429) {
          throw new Error(
            'Limite de exportações excedido. ' +
            'Aguarde 1 minuto e tente novamente.'
          );
        } else {
          throw new Error(error.detail || 'Erro ao exportar para Google Sheets');
        }
      }

      // Success - get spreadsheet URL
      const result = await response.json();

      // Open spreadsheet in new tab
      window.open(result.spreadsheet_url, '_blank', 'noopener,noreferrer');

      // Show success toast
      toast.success('Planilha criada com sucesso!', {
        description: `${result.total_rows} licitações exportadas para Google Sheets`,
        duration: 5000
      });

    } catch (error: any) {
      // Show error toast
      toast.error('Falha ao exportar para Google Sheets', {
        description: error.message || 'Erro desconhecido. Tente novamente.',
        duration: 5000
      });
      console.error('Google Sheets export error:', error);

    } finally {
      setExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={disabled || exporting || licitacoes.length === 0}
      className={`
        inline-flex items-center gap-2 px-4 py-2.5
        border border-strong rounded-button
        bg-surface-0 hover:bg-surface-1
        text-ink-primary font-medium text-sm
        transition-all duration-200
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
      `}
      aria-label="Exportar resultados para Google Sheets"
    >
      {exporting ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-[#4285F4]" aria-hidden="true" />
          <span>Exportando...</span>
        </>
      ) : (
        <>
          <FileSpreadsheet className="w-4 h-4 text-[#4285F4]" aria-hidden="true" />
          <span>Exportar para Google Sheets</span>
        </>
      )}
    </button>
  );
}
