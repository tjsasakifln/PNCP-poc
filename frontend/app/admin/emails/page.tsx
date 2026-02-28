'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../components/AuthProvider';

interface EmailPreview {
  number: number;
  day: number;
  type: string;
  subject: string;
  html?: string;
  error?: string;
}

interface TestSendResult {
  status: string;
  email_id?: string;
  to?: string;
  type?: string;
  subject?: string;
}

export default function AdminEmailsPage() {
  const { session, loading: authLoading, isAdmin } = useAuth();
  const [previews, setPreviews] = useState<EmailPreview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedEmail, setSelectedEmail] = useState<EmailPreview | null>(null);
  const [sending, setSending] = useState<string | null>(null);
  const [sendResult, setSendResult] = useState<TestSendResult | null>(null);

  const fetchPreviews = useCallback(async () => {
    if (!session?.access_token) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/admin/trial-emails/preview', {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      setPreviews(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar previews');
    } finally {
      setLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (session?.access_token && isAdmin) {
      fetchPreviews();
    }
  }, [session?.access_token, isAdmin, fetchPreviews]);

  const handleTestSend = async (emailType: string) => {
    if (!session?.access_token) return;

    setSending(emailType);
    setSendResult(null);

    try {
      const res = await fetch('/api/admin/trial-emails/test-send', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email_type: emailType }),
      });

      const data = await res.json();
      setSendResult(data);
    } catch (err) {
      setSendResult({
        status: 'error',
        type: emailType,
        subject: err instanceof Error ? err.message : 'Erro ao enviar',
      });
    } finally {
      setSending(null);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-2xl mb-2">Acesso Restrito</p>
          <p className="text-gray-500">Esta pagina requer permissoes de administrador.</p>
        </div>
      </div>
    );
  }

  const EMAIL_TYPE_LABELS: Record<string, string> = {
    welcome: 'Boas-vindas',
    engagement: 'Engajamento',
    paywall_alert: 'Paywall Alert',
    value: 'Valor Acumulado',
    last_day: 'Ultimo Dia',
    expired: 'Expirado (20% off)',
  };

  const DAY_COLORS: Record<string, string> = {
    welcome: 'bg-green-100 text-green-800',
    engagement: 'bg-blue-100 text-blue-800',
    paywall_alert: 'bg-orange-100 text-orange-800',
    value: 'bg-emerald-100 text-emerald-800',
    last_day: 'bg-red-100 text-red-800',
    expired: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Email Sequence — Trial 14 Dias
            </h1>
            <p className="text-gray-500 mt-1">
              STORY-321 — Preview e teste dos 6 emails da sequencia trial
            </p>
          </div>
          <div className="flex gap-3">
            <a
              href="/admin"
              className="px-4 py-2 text-sm text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
            >
              Usuarios
            </a>
            <a
              href="/admin/cache"
              className="px-4 py-2 text-sm text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
            >
              Cache
            </a>
            <a
              href="/admin/metrics"
              className="px-4 py-2 text-sm text-gray-700 bg-white border rounded-lg hover:bg-gray-50"
            >
              Metrics
            </a>
          </div>
        </div>

        {/* Send Result Toast */}
        {sendResult && (
          <div
            className={`mb-4 p-4 rounded-lg ${
              sendResult.status === 'sent'
                ? 'bg-green-50 border border-green-200 text-green-800'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            {sendResult.status === 'sent' ? (
              <p>
                Email enviado para <strong>{sendResult.to}</strong> — {sendResult.subject}
              </p>
            ) : (
              <p>Erro ao enviar: {sendResult.subject}</p>
            )}
            <button
              onClick={() => setSendResult(null)}
              className="text-sm underline mt-1"
            >
              Fechar
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            <p>{error}</p>
            <button onClick={fetchPreviews} className="text-sm underline mt-1">
              Tentar novamente
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
          </div>
        )}

        {/* Email Cards */}
        {!loading && (
          <div className="grid gap-4">
            {previews.map((preview) => (
              <div
                key={preview.number}
                className="bg-white rounded-lg border shadow-sm p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-gray-300">
                      #{preview.number}
                    </span>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            DAY_COLORS[preview.type] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          Dia {preview.day}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {EMAIL_TYPE_LABELS[preview.type] || preview.type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-900 font-medium">
                        {preview.subject || preview.error}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {preview.html && (
                      <button
                        onClick={() =>
                          setSelectedEmail(
                            selectedEmail?.number === preview.number ? null : preview
                          )
                        }
                        className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        {selectedEmail?.number === preview.number
                          ? 'Fechar Preview'
                          : 'Preview'}
                      </button>
                    )}
                    <button
                      onClick={() => handleTestSend(preview.type)}
                      disabled={sending === preview.type}
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {sending === preview.type ? 'Enviando...' : 'Enviar teste'}
                    </button>
                  </div>
                </div>

                {/* Inline Preview */}
                {selectedEmail?.number === preview.number && preview.html && (
                  <div className="mt-4 border rounded-lg overflow-hidden">
                    <div className="bg-gray-100 px-4 py-2 text-xs text-gray-500 border-b">
                      Preview: {preview.subject}
                    </div>
                    <iframe
                      srcDoc={preview.html}
                      title={`Preview email #${preview.number}`}
                      className="w-full border-0"
                      style={{ height: '600px' }}
                      sandbox="allow-same-origin"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && previews.length === 0 && !error && (
          <div className="text-center py-12 text-gray-500">
            <p>Nenhum template de email encontrado.</p>
          </div>
        )}
      </div>
    </div>
  );
}
