/**
 * STORY-2.3: Catálogo de mensagens de erro humanizadas (pt-BR).
 *
 * Cada entrada tem: title (linha 1 clara), body (causa + ação), action (opcional).
 *
 * Inventário de callsites auditados (AC1):
 * ─────────────────────────────────────────────────────────────────────
 * Arquivo                                          Ln   Tipo
 * app/error.tsx                                     54  inline render
 * components/ErrorBoundary.tsx                      84  inline render
 * components/PageErrorBoundary.tsx                  87  inline render
 * components/ErrorStateWithRetry.tsx                70  inline render
 * app/buscar/components/SearchErrorBanner.tsx       79  inline render
 * app/buscar/components/ErrorDetail.tsx             80  toast.error
 * app/buscar/components/GoogleSheetsExportButton    62  toast.error (x5)
 * app/admin/cache/page.tsx                          96  toast.error (x3)
 * app/admin/components/AdminCreateUser.tsx          57  toast.error
 * app/admin/components/AdminUserTable.tsx           73  toast.error (x4)
 * app/admin/page.tsx                                96  toast.error (x3)
 * app/admin/partners/page.tsx                      114  toast.error (x2)
 * app/alertas/page.tsx                              98  toast.error (x3)
 * app/conta/dados/page.tsx                          --  toast.error
 * app/conta/perfil/page.tsx                         --  toast.error
 * app/conta/seguranca/page.tsx                      --  toast.error
 * app/conta/equipe/page.tsx                         --  toast.error
 * app/dashboard/page.tsx                            --  throw new Error
 * app/calculadora/CalculadoraClient.tsx             --  toast.error
 * lib/error-messages.ts (ERROR_CODE_MESSAGES)       --  mapped codes
 * ─────────────────────────────────────────────────────────────────────
 * Total: ~40+ callsites. Top 20 humanizados abaixo (AC2).
 */

export type ErrorSeverity = 'error' | 'warning' | 'info';
export type ActionKind = 'retry' | 'refresh' | 'support' | 'custom';

export interface ErrorEntry {
  /** Título curto — sem jargão técnico */
  title: string;
  /** Corpo — causa provável + próxima ação */
  body: string;
  /** Severidade visual: error=vermelho, warning=âmbar, info=azul */
  severity?: ErrorSeverity;
  /** Ação primária sugerida */
  action?: {
    label: string;
    kind: ActionKind;
  };
}

/**
 * Top 20 mensagens de erro humanizadas para o SmartLic.
 * Chaves alinham com SearchErrorCode do backend + cenários comuns do frontend.
 */
export const ERROR_MESSAGES: Record<string, ErrorEntry> = {
  // ── Busca / Pipeline ───────────────────────────────────────────────
  'search.timeout': {
    title: 'A busca está demorando mais que o esperado',
    body: 'Sua análise ainda está sendo processada. Tente novamente em alguns segundos ou reduza o número de estados selecionados.',
    severity: 'info',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'search.all_sources_failed': {
    title: 'Fontes de dados indisponíveis',
    body: 'Não conseguimos acessar nenhuma fonte de licitações no momento. Isso costuma ser temporário — aguarde 2–3 minutos e tente de novo.',
    severity: 'warning',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'search.source_unavailable': {
    title: 'Uma das fontes está em manutenção',
    body: 'O PNCP ou outra fonte está temporariamente indisponível. Os resultados podem estar parciais. Tente novamente em instantes.',
    severity: 'warning',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'search.backend_unavailable': {
    title: 'Servidor indisponível',
    body: 'Não conseguimos conectar ao servidor. Estamos voltando em instantes — aguarde alguns segundos e tente novamente.',
    severity: 'warning',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'search.rate_limit': {
    title: 'Muitas análises em seguida',
    body: 'Você realizou várias buscas em sequência. Aguarde 1 minuto antes de tentar novamente.',
    severity: 'warning',
    action: { label: 'Aguardar e tentar', kind: 'retry' },
  },
  'search.quota_exceeded': {
    title: 'Limite de análises atingido',
    body: 'Você utilizou todas as análises disponíveis no seu plano este mês. Faça upgrade para continuar.',
    severity: 'error',
    action: { label: 'Ver planos', kind: 'custom' },
  },
  'search.validation_error': {
    title: 'Filtros inválidos',
    body: 'Alguns filtros selecionados não são válidos. Verifique as datas e os estados selecionados e tente novamente.',
    severity: 'warning',
    action: { label: 'Revisar filtros', kind: 'custom' },
  },
  'search.internal_error': {
    title: 'Erro inesperado na análise',
    body: 'Algo deu errado do nosso lado. Nossa equipe já foi notificada. Tente novamente em alguns instantes.',
    severity: 'error',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },

  // ── Autenticação / Sessão ─────────────────────────────────────────
  'auth.session_expired': {
    title: 'Sua sessão expirou',
    body: 'Por segurança, sua sessão foi encerrada após um período inativo. Faça login novamente para continuar.',
    severity: 'warning',
    action: { label: 'Fazer login', kind: 'custom' },
  },
  'auth.access_denied': {
    title: 'Acesso não permitido',
    body: 'Você não tem permissão para realizar esta ação. Se acreditar que é um engano, entre em contato com o suporte.',
    severity: 'error',
    action: { label: 'Falar com suporte', kind: 'support' },
  },
  'auth.not_found': {
    title: 'Usuário não encontrado',
    body: 'Não encontramos uma conta com esse email. Verifique o endereço ou crie uma nova conta.',
    severity: 'warning',
    action: { label: 'Criar conta', kind: 'custom' },
  },

  // ── Rede / Conexão ─────────────────────────────────────────────────
  'network.offline': {
    title: 'Sem conexão com a internet',
    body: 'Verifique sua conexão Wi-Fi ou dados móveis e tente novamente.',
    severity: 'error',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'network.server_error': {
    title: 'O servidor está temporariamente indisponível',
    body: 'Pode ser uma atualização em andamento. Aguarde alguns segundos e tente novamente.',
    severity: 'warning',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
  'network.gateway_timeout': {
    title: 'A requisição demorou demais',
    body: 'O servidor não respondeu a tempo. Tente novamente em alguns minutos.',
    severity: 'warning',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },

  // ── Exportação ─────────────────────────────────────────────────────
  'export.not_logged_in': {
    title: 'Login necessário para exportar',
    body: 'Você precisa estar logado para exportar os resultados. Faça login e tente novamente.',
    severity: 'warning',
    action: { label: 'Fazer login', kind: 'custom' },
  },
  'export.no_results': {
    title: 'Nada para exportar',
    body: 'Não há resultados para exportar. Realize uma busca primeiro.',
    severity: 'info',
  },
  'export.failed': {
    title: 'Falha na exportação',
    body: 'Não conseguimos gerar o arquivo. Tente novamente — se o problema persistir, entre em contato com o suporte.',
    severity: 'error',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },

  // ── Faturamento ────────────────────────────────────────────────────
  'billing.payment_failed': {
    title: 'Falha no pagamento',
    body: 'Não conseguimos cobrar seu cartão. Atualize sua forma de pagamento para evitar a interrupção do acesso.',
    severity: 'warning',
    action: { label: 'Atualizar pagamento', kind: 'custom' },
  },
  'billing.plan_required': {
    title: 'Recurso disponível apenas nos planos pagos',
    body: 'Este recurso não está disponível no trial gratuito. Faça upgrade para continuar utilizando.',
    severity: 'info',
    action: { label: 'Ver planos', kind: 'custom' },
  },

  // ── Genérico / Fallback ────────────────────────────────────────────
  'generic.unexpected': {
    title: 'Algo deu errado',
    body: 'Ocorreu um erro inesperado. Tente novamente — se o problema persistir, entre em contato com o suporte.',
    severity: 'error',
    action: { label: 'Tentar novamente', kind: 'retry' },
  },
};

/**
 * Retorna a entrada humanizada para uma chave do catálogo.
 * Retorna null se a chave não existir — o componente deve usar um fallback.
 */
export function getHumanizedMessage(key: string): ErrorEntry | null {
  return ERROR_MESSAGES[key] ?? null;
}
