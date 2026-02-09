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

  // HTTP status errors
  "503": "Serviço temporariamente indisponível. Tente em alguns minutos.",
  "502": "O portal PNCP está temporariamente indisponível. Tente novamente em instantes.",
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

  // Backend specific
  "Backend indisponível": "Não foi possível processar sua busca. Tente novamente em instantes.",
  "Erro ao buscar licitações": "Não foi possível processar sua busca. Tente novamente em instantes.",
  "Quota excedida": "Suas buscas do mês acabaram. Faça upgrade para continuar.",

  // Timeout / PNCP specific (from backend detail messages)
  "excedeu o tempo limite": "A busca demorou demais. Tente com menos estados ou um período menor.",
  "PNCP está temporariamente": "O portal PNCP está temporariamente fora do ar. Tente novamente em instantes.",
  "tempo limite de": "A busca demorou demais. Tente com menos estados ou um período menor.",
};

/**
 * Converts a technical error message to a user-friendly Portuguese message.
 * Strips URLs, stack traces, and technical jargon.
 */
export function getUserFriendlyError(error: string | Error): string {
  const message = error instanceof Error ? error.message : error;

  // Check exact matches first
  if (ERROR_MAP[message]) return ERROR_MAP[message];

  // Check partial matches
  for (const [key, value] of Object.entries(ERROR_MAP)) {
    if (message.toLowerCase().includes(key.toLowerCase())) {
      return value;
    }
  }

  // Strip URLs from the message
  const stripped = message.replace(/https?:\/\/[^\s]+/g, '').trim();

  // If the stripped message is still too technical, return generic
  if (stripped.includes('Error') || stripped.includes('error') || stripped.includes('failed') || stripped.length > 100) {
    return "Algo deu errado. Tente novamente em instantes.";
  }

  return stripped || "Algo deu errado. Tente novamente em instantes.";
}
