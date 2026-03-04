/**
 * Maps technical error messages to user-friendly Portuguese equivalents.
 * STORY-170 AC6 — No technical jargon exposed to users.
 */

const ERROR_MAP: Record<string, string> = {
  // Network errors
  "fetch failed": "Erro de conexão. Verifique sua internet.",
  "Failed to fetch": "Erro de conexão. Verifique sua internet.",
  "NetworkError": "Erro de conexão. Verifique sua internet.",
  "network error": "Erro de conexão. Verifique sua internet.",
  "Load failed": "Erro de conexão. Verifique sua internet.",

  // SSL errors
  "ERR_CERT_COMMON_NAME_INVALID": "Problema de segurança no servidor. Tente novamente em instantes.",
  "ERR_CERT": "Problema de segurança no servidor. Tente novamente em instantes.",

  // HTTP status errors (TD-006 AC2: all 10 codes mapped)
  "400": "Requisição inválida. Verifique os dados e tente novamente.",
  "503": "Serviço temporariamente indisponível. Tente em alguns minutos.",
  "502": "O servidor está temporariamente indisponível. Tente novamente em instantes.",
  "504": "A busca demorou demais. Tente com menos estados ou um período menor.",
  "500": "Erro interno do servidor. Tente novamente.",
  "429": "Muitas requisições. Aguarde um momento e tente novamente.",
  "401": "Sessão expirada. Faça login novamente.",
  "403": "Acesso negado. Verifique suas permissões.",
  "404": "Recurso não encontrado.",
  "408": "A requisição demorou muito. Tente novamente.",

  // JSON parse errors (backend returned HTML instead of JSON)
  "Unexpected token": "Erro temporário de comunicação. Tente novamente.",
  "is not valid JSON": "Erro temporário de comunicação. Tente novamente.",
  "Resposta inesperada": "Erro temporário de comunicação. Tente novamente.",

  // CRIT-017: Infrastructure errors that should never leak (defense-in-depth)
  "Application not found": "Nossos servidores estão sendo atualizados. Tente novamente em alguns instantes.",
  "Bad Gateway": "O servidor está temporariamente indisponível. Tente novamente em instantes.",
  "Service Unavailable": "Serviço temporariamente indisponível. Tente em alguns minutos.",
  "Gateway Timeout": "A requisição demorou muito. Tente novamente.",
  "Nossos servidores estão sendo atualizados": "keep_original",

  // UX-354 AC4-AC5 + UX-357 AC1-AC4: Server restart messages (unified to max 2 variants)
  "Server restart": "O servidor reiniciou. Recomendamos tentar novamente.",
  "retry recommended": "O servidor reiniciou. Recomendamos tentar novamente.",
  "reiniciou": "O servidor reiniciou. Recomendamos tentar novamente.",
  "Connection reset": "A conexão foi interrompida. Tente novamente.",
  "connection refused": "Servidor temporariamente indisponível. Tente novamente em instantes.",
  "Internal server error": "Erro interno do servidor. Tente novamente.",
  "Pipeline failed": "A busca não pôde ser concluída. Tente novamente.",
  "All sources failed": "Nenhuma fonte de dados respondeu. Tente novamente em alguns minutos.",
  "No results found": "Nenhum resultado encontrado para os filtros selecionados.",

  // Backend specific — GTM-FIX-033 AC5: actionable message
  "Backend indisponível": "Não foi possível processar sua busca. A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente.",
  "Erro ao buscar licitações": "Não foi possível processar sua busca. A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente.",
  "Quota excedida": "Suas buscas do mês acabaram. Faça upgrade para continuar.",

  // Timeout / PNCP specific (from backend detail messages)
  "excedeu o tempo limite": "A busca demorou demais. Tente com menos estados ou um período menor.",
  "PNCP está temporariamente": "O portal PNCP está temporariamente fora do ar. Tente novamente em instantes.",
  "tempo limite de": "A busca demorou demais. Tente com menos estados ou um período menor.",

  // UX FIX: Plan limit errors (date range)
  "período de busca não pode exceder": "keep_original", // Let the full message through
  "excede o limite de": "keep_original", // Let the full message through
  "Período de": "keep_original", // Let the full message through

  // CRIT-005 AC19: Response state mappings
  "empty_failure": "As fontes de dados estão temporariamente indisponíveis. Tente novamente em alguns minutos.",
  "degraded": "Alguns resultados podem estar incompletos. Fontes parcialmente disponíveis.",
  "sources_unavailable": "Não foi possível acessar as fontes de dados. Tente novamente em instantes.",
};

/**
 * Converts a technical error message to a user-friendly Portuguese message.
 * Strips URLs, stack traces, and technical jargon.
 *
 * HOTFIX 2026-02-10: Enhanced to properly extract error messages from API responses,
 * fixing "[object Object]" display bug that was showing to paying users.
 */
export function getUserFriendlyError(error: any): string {
  // HOTFIX: Handle API error responses (Axios/fetch error objects)
  // This fixes the "[object Object]" bug
  let message: string;

  if (typeof error === 'string') {
    message = error;
  } else if (error instanceof Error) {
    message = error.message;
  } else if (error?.response?.data) {
    // Axios error with structured response
    const data = error.response.data;

    // Try to extract message from various formats
    if (data.detail?.message) {
      // FastAPI HTTPException with structured detail
      message = data.detail.message;
    } else if (typeof data.detail === 'string') {
      // FastAPI HTTPException with string detail
      message = data.detail;
    } else if (data.message) {
      // Simple message field
      message = data.message;
    } else if (typeof data === 'string') {
      // Entire data is a string
      message = data;
    } else {
      // Fallback: couldn't extract message from object
      console.error('Could not extract error message from:', data);
      message = "Não foi possível processar sua busca. Tente novamente em instantes.";
    }
  } else if (error?.request && !error?.response) {
    // Network error (request sent but no response)
    message = "Erro de conexão. Verifique sua internet.";
  } else if (error?.message) {
    // Error object with message
    message = error.message;
  } else {
    // Unknown error format
    console.error('Unknown error format:', error);
    message = "Erro desconhecido. Por favor, tente novamente.";
  }

  // Now apply user-friendly mappings to the extracted message
  // Check exact matches first
  if (ERROR_MAP[message]) {
    const mapped = ERROR_MAP[message];
    return mapped === "keep_original" ? message : mapped;
  }

  // Check partial matches
  for (const [key, value] of Object.entries(ERROR_MAP)) {
    if (message.toLowerCase().includes(key.toLowerCase())) {
      // UX FIX: "keep_original" means pass the full message through
      if (value === "keep_original") {
        return message;
      }
      return value;
    }
  }

  // Strip URLs from the message
  const stripped = message.replace(/https?:\/\/[^\s]+/g, '').trim();

  // Check if message has stack traces or technical jargon (TypeError, ReferenceError, etc.)
  const hasTechnicalJargon =
    stripped.includes('Error:') ||
    stripped.includes('TypeError') ||
    stripped.includes('ReferenceError') ||
    stripped.includes('at ') || // stack trace
    stripped.includes('Line ') || // stack trace
    stripped.match(/\w+Error:/); // any XxxError:

  // UX FIX: Only treat as technical if it contains actual technical jargon
  // Allow longer user-friendly messages (up to 200 chars) to pass through
  if (hasTechnicalJargon) {
    return "Algo deu errado. Tente novamente em instantes.";
  }

  // If message is user-friendly (even if long), keep it
  // Example: "O período de busca não pode exceder 7 dias..." (>100 chars but clear)
  if (stripped.length <= 200) {
    return stripped;
  }

  // Message is too long and possibly not user-friendly
  return "Algo deu errado. Tente novamente em instantes.";
}

/**
 * TD-006 AC4: Alias for getUserFriendlyError.
 * Accepts Error, fetch Response-like objects, or string.
 */
export const getErrorMessage = getUserFriendlyError;

/** Default fallback message for unknown errors (TD-006 AC8). */
export const DEFAULT_ERROR_MESSAGE = "Ocorreu um erro inesperado. Tente novamente.";


/**
 * CRIT-008 AC4: HTTP status codes that indicate transient (recoverable) errors.
 * These trigger auto-retry with countdown in the frontend.
 */
export const TRANSIENT_HTTP_CODES = new Set([502, 503, 504]);

/**
 * GTM-UX-003 AC4-AC7: Contextual retry messages by error type.
 * NEVER says "servidor reiniciando" — uses specific messages per error category.
 */
export function getRetryMessage(httpStatus: number | null, rawMessage?: string): string {
  const msg = (rawMessage || '').toLowerCase();

  // AC4: Timeout / PNCP timeout
  if (httpStatus === 504 || msg.includes('timeout') || msg.includes('demorou') || msg.includes('tempo limite')) {
    return 'A consulta está demorando mais que o esperado. Tentando novamente...';
  }

  // AC5: 502/503 — service unavailable
  if (httpStatus === 502 || httpStatus === 503) {
    return 'Serviço temporariamente indisponível. Tentando novamente...';
  }

  // AC6: Network errors
  if (
    msg.includes('fetch failed') ||
    msg.includes('failed to fetch') ||
    msg.includes('networkerror') ||
    msg.includes('network error') ||
    msg.includes('load failed') ||
    msg.includes('econnrefused') ||
    msg.includes('err_connection_refused') ||
    msg.includes('conexão') ||
    msg.includes('conexao')
  ) {
    return 'Sem conexão com o servidor. Verificando...';
  }

  // AC7: Generic transient — never say "reiniciando"
  return 'Serviço temporariamente indisponível. Tentando novamente...';
}

/**
 * CRIT-008 AC4: Classify whether an error is transient (server restart, network blip)
 * vs permanent (bad request, auth failure). Only transient errors get auto-retry.
 */
export function isTransientError(httpStatus: number | null, message?: string): boolean {
  if (httpStatus && TRANSIENT_HTTP_CODES.has(httpStatus)) return true;
  if (!message) return false;
  const msg = message.toLowerCase();
  return (
    msg.includes('fetch failed') ||
    msg.includes('failed to fetch') ||
    msg.includes('networkerror') ||
    msg.includes('network error') ||
    msg.includes('load failed') ||
    msg.includes('econnrefused') ||
    msg.includes('err_connection_refused')
  );
}

/**
 * GTM-PROXY-001 AC4-AC8: Centralized Supabase Auth error translations.
 * Maps English auth errors from Supabase to user-friendly Portuguese messages.
 * Used by login, signup, and any other auth-related flows.
 */
export const AUTH_ERROR_MAP: Record<string, string> = {
  // AC4: Invalid credentials
  "Invalid login credentials": "Email ou senha incorretos",
  // AC5: Duplicate registration
  "User already registered": "Este email já está cadastrado",
  // AC6: Unconfirmed email
  "Email not confirmed": "Confirme seu email antes de fazer login",
  // AC7: Password policy
  "Password should be at least 6 characters": "A senha deve ter pelo menos 6 caracteres",
  // Additional common Supabase auth errors
  "Error sending magic link email": "Este email ainda não está cadastrado. Crie sua conta para começar.",
  "For security purposes, you can only request this after": "Por segurança, aguarde alguns segundos antes de tentar novamente.",
  "Email rate limit exceeded": "Muitas tentativas. Aguarde alguns minutos.",
  "User not found": "Usuário não encontrado. Verifique o email ou crie uma conta.",
  "Signups not allowed for this instance": "Cadastros não permitidos no momento.",
  "Unable to validate email address: invalid format": "Formato de email inválido.",
  // Network errors (shared with ERROR_MAP)
  "fetch failed": "Erro de conexão. Verifique sua internet.",
  "Failed to fetch": "Erro de conexão. Verifique sua internet.",
  "NetworkError": "Erro de conexão. Verifique sua internet.",
  "network error": "Erro de conexão. Verifique sua internet.",
};

/**
 * GTM-PROXY-001 AC8: Translate Supabase auth error to Portuguese.
 * Checks exact match first, then partial match.
 * Returns original message if no translation found.
 */
export function translateAuthError(message: string): string {
  // Exact match
  if (AUTH_ERROR_MAP[message]) {
    return AUTH_ERROR_MAP[message];
  }
  // Partial match
  for (const [key, value] of Object.entries(AUTH_ERROR_MAP)) {
    if (message.toLowerCase().includes(key.toLowerCase())) {
      return value;
    }
  }
  return message;
}

/**
 * CRIT-009 AC11: Maps backend SearchErrorCode values to user-friendly Portuguese messages.
 * These are more specific than getUserFriendlyError() and take precedence when error_code is present.
 */
export const ERROR_CODE_MESSAGES: Record<string, string> = {
  BACKEND_UNAVAILABLE: "Nossos servidores estão sendo atualizados. Tente novamente em alguns instantes.",
  SOURCE_UNAVAILABLE: "Nossas fontes de dados estão temporariamente indisponíveis.",
  ALL_SOURCES_FAILED: "Nenhuma fonte de dados respondeu. Tente novamente em alguns minutos.",
  TIMEOUT: "A busca demorou mais que o esperado. Tente reduzir o número de estados.",
  RATE_LIMIT: "Limite de requisições atingido. Aguarde alguns minutos.",
  QUOTA_EXCEEDED: "Você atingiu o limite de análises deste mês.",
  VALIDATION_ERROR: "Parâmetros de busca inválidos. Verifique os filtros.",
  INTERNAL_ERROR: "Erro interno. Nossa equipe foi notificada.",
};

// =============================================================================
// STAB-006 AC2: Humanized error messages with action suggestions
// =============================================================================

export interface HumanizedError {
  /** User-friendly message (blue/yellow tone, never red) */
  message: string;
  /** Suggested action label for primary button */
  actionLabel: string;
  /** Secondary action label (optional) */
  secondaryActionLabel?: string;
  /** Color tone: 'blue' for informational, 'yellow' for warning */
  tone: "blue" | "yellow";
  /** Whether to suggest scope reduction */
  suggestReduceScope: boolean;
}

/**
 * STAB-006 AC2: Get humanized error with action suggestions.
 * Uses blue/yellow colors ONLY (never red) per UX guidelines.
 */
export function getHumanizedError(
  httpStatus: number | null,
  rawMessage: string | null,
  partialCount?: number,
  totalCount?: number
): HumanizedError {
  const msg = (rawMessage || "").toLowerCase();

  // Timeout / 524
  if (httpStatus === 524 || httpStatus === 504 || msg.includes("timeout") || msg.includes("demorou")) {
    return {
      message: "A busca demorou mais que o esperado. Tente reduzir o numero de estados.",
      actionLabel: "Tentar novamente",
      secondaryActionLabel: "Reduzir escopo",
      tone: "yellow",
      suggestReduceScope: true,
    };
  }

  // Partial failure (some UFs responded)
  if (partialCount != null && totalCount != null && partialCount > 0 && partialCount < totalCount) {
    return {
      message: `Resultados parciais: ${partialCount} de ${totalCount} estados responderam`,
      actionLabel: "Tentar novamente",
      tone: "blue",
      suggestReduceScope: false,
    };
  }

  // Backend down (502/503)
  if (httpStatus === 502 || httpStatus === 503) {
    return {
      message: "Nossos servidores estao se atualizando.",
      actionLabel: "Tentar novamente",
      tone: "blue",
      suggestReduceScope: false,
    };
  }

  // Rate limit
  if (httpStatus === 429) {
    return {
      message: "Muitas consultas simultaneas. Aguarde alguns segundos.",
      actionLabel: "Tentar novamente",
      tone: "yellow",
      suggestReduceScope: false,
    };
  }

  // Network errors
  if (
    msg.includes("fetch failed") ||
    msg.includes("failed to fetch") ||
    msg.includes("networkerror") ||
    msg.includes("network error")
  ) {
    return {
      message: "Erro de conexao. Verifique sua internet e tente novamente.",
      actionLabel: "Tentar novamente",
      tone: "yellow",
      suggestReduceScope: false,
    };
  }

  // Default
  return {
    message: "Algo inesperado aconteceu. Tente novamente.",
    actionLabel: "Tentar novamente",
    tone: "blue",
    suggestReduceScope: false,
  };
}

/**
 * CRIT-009 AC11: Get user-friendly message from error_code, with fallback to generic mapping.
 */
export function getMessageFromErrorCode(errorCode: string | null | undefined): string | null {
  if (!errorCode) return null;
  return ERROR_CODE_MESSAGES[errorCode] || null;
}
