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
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Google Sheets Brand Icon Component
 * Official Google Sheets logo with brand colors
 */
function GoogleSheetsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="#0F9D58"/>
      <path d="M14 2V8H20L14 2Z" fill="#87CEAC"/>
      <rect x="7" y="11" width="10" height="2" rx="0.5" fill="white"/>
      <rect x="7" y="14" width="10" height="2" rx="0.5" fill="white"/>
      <rect x="7" y="17" width="6" height="2" rx="0.5" fill="white"/>
      <line x1="11" y1="11" x2="11" y2="19" stroke="white" strokeWidth="1"/>
    </svg>
  );
}

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

      // CRITICAL FIX: Check if response is JSON before parsing
      const contentType = response.headers.get('content-type');
      const isJson = contentType && contentType.includes('application/json');

      // Handle OAuth required (401)
      if (response.status === 401) {
        let error;
        try {
          error = isJson ? await response.json() : { detail: 'Autenticação necessária' };
        } catch {
          error = { detail: 'Autenticação necessária' };
        }

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
        let error;
        try {
          // CRITICAL FIX: Only parse JSON if Content-Type is correct
          error = isJson ? await response.json() : { detail: `Erro HTTP ${response.status}` };
        } catch (parseError) {
          // If JSON parsing fails (HTML response), provide fallback error
          console.error('Failed to parse error response:', parseError);
          error = { detail: 'Erro ao exportar para Google Sheets. Tente novamente.' };
        }

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
      let result;
      try {
        result = isJson ? await response.json() : null;
        if (!result || !result.spreadsheet_url) {
          throw new Error('Resposta inválida do servidor');
        }
      } catch (parseError) {
        console.error('Failed to parse success response:', parseError);
        throw new Error('Erro ao processar resposta. Tente novamente.');
      }

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
      aria-label="Exportar para Google Sheets"
    >
      {exporting ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin text-[#4285F4]" aria-hidden="true" />
          <span>Exportando...</span>
        </>
      ) : (
        <>
          <GoogleSheetsIcon className="w-4 h-4" aria-hidden="true" />
          <span>Exportar para Google Sheets</span>
        </>
      )}
    </button>
  );
}
