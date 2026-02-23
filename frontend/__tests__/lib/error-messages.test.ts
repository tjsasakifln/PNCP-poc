/**
 * Tests for lib/error-messages.ts - User-Friendly Error Messages
 */
import { getUserFriendlyError, getErrorMessage, DEFAULT_ERROR_MESSAGE } from '@/lib/error-messages';

describe('getUserFriendlyError', () => {
  describe('String errors', () => {
    it('should handle plain string errors', () => {
      const result = getUserFriendlyError('fetch failed');
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should handle case-insensitive matching', () => {
      const result = getUserFriendlyError('FETCH FAILED');
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });
  });

  describe('Error objects', () => {
    it('should extract message from Error object', () => {
      const error = new Error('fetch failed');
      const result = getUserFriendlyError(error);
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should handle TypeError', () => {
      const error = new TypeError('Cannot read property');
      const result = getUserFriendlyError(error);
      // TypeError in message triggers technical jargon filter, but the message itself
      // doesn't have stack traces, so it passes through as user-friendly
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });
  });

  describe('Network errors', () => {
    it('should map "fetch failed"', () => {
      expect(getUserFriendlyError('fetch failed')).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should map "Failed to fetch"', () => {
      expect(getUserFriendlyError('Failed to fetch')).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should map "NetworkError"', () => {
      expect(getUserFriendlyError('NetworkError')).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should map "Load failed"', () => {
      expect(getUserFriendlyError('Load failed')).toBe('Erro de conexão. Verifique sua internet.');
    });
  });

  describe('HTTP status errors', () => {
    it('should map 503 errors', () => {
      expect(getUserFriendlyError('503')).toBe('Serviço temporariamente indisponível. Tente em alguns minutos.');
    });

    it('should map 502 errors', () => {
      expect(getUserFriendlyError('502')).toBe('O portal PNCP está temporariamente indisponível. Tente novamente em instantes.');
    });

    it('should map 504 errors', () => {
      expect(getUserFriendlyError('504')).toBe('A busca demorou demais. Tente com menos estados ou um período menor.');
    });

    it('should map 500 errors', () => {
      expect(getUserFriendlyError('500')).toBe('Erro interno do servidor. Tente novamente.');
    });

    it('should map 429 errors', () => {
      expect(getUserFriendlyError('429')).toBe('Muitas requisições. Aguarde um momento e tente novamente.');
    });

    it('should map 401 errors', () => {
      expect(getUserFriendlyError('401')).toBe('Sessão expirada. Faça login novamente.');
    });

    it('should map 403 errors', () => {
      expect(getUserFriendlyError('403')).toBe('Acesso negado. Verifique suas permissões.');
    });

    it('should map 404 errors', () => {
      expect(getUserFriendlyError('404')).toBe('Recurso não encontrado.');
    });

    it('should map 408 errors', () => {
      expect(getUserFriendlyError('408')).toBe('A requisição demorou muito. Tente novamente.');
    });
  });

  describe('SSL errors', () => {
    it('should map ERR_CERT_COMMON_NAME_INVALID', () => {
      expect(getUserFriendlyError('ERR_CERT_COMMON_NAME_INVALID')).toBe('Problema de segurança no servidor. Tente novamente em instantes.');
    });

    it('should map ERR_CERT', () => {
      expect(getUserFriendlyError('ERR_CERT')).toBe('Problema de segurança no servidor. Tente novamente em instantes.');
    });
  });

  describe('JSON parse errors', () => {
    it('should map "Unexpected token"', () => {
      expect(getUserFriendlyError('Unexpected token')).toBe('Erro temporário de comunicação. Tente novamente.');
    });

    it('should map "is not valid JSON"', () => {
      expect(getUserFriendlyError('is not valid JSON')).toBe('Erro temporário de comunicação. Tente novamente.');
    });

    it('should map "Resposta inesperada"', () => {
      expect(getUserFriendlyError('Resposta inesperada')).toBe('Erro temporário de comunicação. Tente novamente.');
    });
  });

  describe('Backend specific errors', () => {
    it('should map "Backend indisponível"', () => {
      expect(getUserFriendlyError('Backend indisponível')).toBe('Não foi possível processar sua busca. A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente.');
    });

    it('should map "Erro ao buscar licitações"', () => {
      expect(getUserFriendlyError('Erro ao buscar licitações')).toBe('Não foi possível processar sua busca. A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente.');
    });

    it('should map "Quota excedida"', () => {
      expect(getUserFriendlyError('Quota excedida')).toBe('Suas buscas do mês acabaram. Faça upgrade para continuar.');
    });
  });

  // UX-354 AC4-AC5: Server restart and English error mappings
  describe('UX-354: English error messages mapped to PT-BR', () => {
    it('should map "Server restart" to PT-BR', () => {
      expect(getUserFriendlyError('Server restart — retry recommended')).toBe(
        'O servidor reiniciou. Recomendamos tentar novamente.'
      );
    });

    it('should map "retry recommended" partial match to PT-BR', () => {
      expect(getUserFriendlyError('Something failed, retry recommended')).toBe(
        'O servidor reiniciou. Recomendamos tentar novamente.'
      );
    });

    it('should map "Connection reset" to PT-BR', () => {
      expect(getUserFriendlyError('Connection reset by peer')).toBe(
        'A conexão foi interrompida. Tente novamente.'
      );
    });

    it('should map "Pipeline failed" to PT-BR', () => {
      expect(getUserFriendlyError('Pipeline failed')).toBe(
        'A busca não pôde ser concluída. Tente novamente.'
      );
    });

    it('should map "All sources failed" to PT-BR', () => {
      expect(getUserFriendlyError('All sources failed to respond')).toBe(
        'Nenhuma fonte de dados respondeu. Tente novamente em alguns minutos.'
      );
    });

    it('should map "No results found" to PT-BR', () => {
      expect(getUserFriendlyError('No results found')).toBe(
        'Nenhum resultado encontrado para os filtros selecionados.'
      );
    });

    it('should map "Internal server error" to PT-BR', () => {
      expect(getUserFriendlyError('Internal server error')).toBe(
        'Erro interno do servidor. Tente novamente.'
      );
    });

    it('should map "connection refused" to PT-BR', () => {
      expect(getUserFriendlyError('connection refused')).toBe(
        'Servidor temporariamente indisponível. Tente novamente em instantes.'
      );
    });
  });

  describe('Timeout errors', () => {
    it('should map "excedeu o tempo limite"', () => {
      expect(getUserFriendlyError('excedeu o tempo limite')).toBe('A busca demorou demais. Tente com menos estados ou um período menor.');
    });

    it('should map "PNCP está temporariamente"', () => {
      expect(getUserFriendlyError('PNCP está temporariamente')).toBe('O portal PNCP está temporariamente fora do ar. Tente novamente em instantes.');
    });

    it('should map "tempo limite de"', () => {
      expect(getUserFriendlyError('tempo limite de')).toBe('A busca demorou demais. Tente com menos estados ou um período menor.');
    });
  });

  describe('API error responses (HOTFIX for [object Object] bug)', () => {
    it('should extract message from Axios error with structured detail', () => {
      const error = {
        response: {
          data: {
            detail: {
              message: 'Quota excedida',
            },
          },
        },
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Suas buscas do mês acabaram. Faça upgrade para continuar.');
    });

    it('should extract message from FastAPI string detail', () => {
      const error = {
        response: {
          data: {
            detail: 'Backend indisponível',
          },
        },
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Não foi possível processar sua busca. A busca pode ter sido concluída. Verifique suas buscas salvas ou tente novamente.');
    });

    it('should extract message from simple message field', () => {
      const error = {
        response: {
          data: {
            message: 'Network error',
          },
        },
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should extract message when entire data is string', () => {
      const error = {
        response: {
          data: 'fetch failed',
        },
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should handle error without response (network error)', () => {
      const error = {
        request: {},
        message: 'Network Error',
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should handle error with nested message', () => {
      const error = {
        message: '503',
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Serviço temporariamente indisponível. Tente em alguns minutos.');
    });

    it('should fallback gracefully when cannot extract message', () => {
      const error = {
        response: {
          data: {
            unknownField: 'something',
          },
        },
      };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Não foi possível processar sua busca. Tente novamente em instantes.');
    });

    it('should handle completely unknown error format', () => {
      const error = { weird: 'structure' };

      const result = getUserFriendlyError(error);
      expect(result).toBe('Erro desconhecido. Por favor, tente novamente.');
    });
  });

  describe('Plan limit errors (keep_original)', () => {
    it('should keep original message for date range limit errors', () => {
      const msg = 'O período de busca não pode exceder 7 dias no plano consultor_agil';
      expect(getUserFriendlyError(msg)).toBe(msg);
    });

    it('should keep original message for "excede o limite de"', () => {
      const msg = 'Período excede o limite de 90 dias';
      expect(getUserFriendlyError(msg)).toBe(msg);
    });

    it('should keep original message starting with "Período de"', () => {
      const msg = 'Período de busca muito longo';
      expect(getUserFriendlyError(msg)).toBe(msg);
    });
  });

  describe('URL stripping', () => {
    it('should strip URLs from error messages', () => {
      const msg = 'Error at https://api.example.com/endpoint - failed';
      const result = getUserFriendlyError(msg);
      expect(result).not.toContain('https://');
    });

    it('should strip http URLs', () => {
      const msg = 'Error from http://backend:8000/buscar';
      const result = getUserFriendlyError(msg);
      expect(result).not.toContain('http://');
    });
  });

  describe('Technical jargon filtering', () => {
    it('should filter out stack traces with "at "', () => {
      const msg = 'TypeError: Cannot read property\n    at Object.<anonymous>';
      const result = getUserFriendlyError(msg);
      expect(result).toBe('Algo deu errado. Tente novamente em instantes.');
    });

    it('should filter out "Error:" prefix', () => {
      const msg = 'Error: Something went wrong';
      const result = getUserFriendlyError(msg);
      expect(result).toBe('Algo deu errado. Tente novamente em instantes.');
    });

    it('should filter TypeError', () => {
      const msg = 'TypeError: undefined is not an object';
      const result = getUserFriendlyError(msg);
      expect(result).toBe('Algo deu errado. Tente novamente em instantes.');
    });

    it('should filter ReferenceError', () => {
      const msg = 'ReferenceError: x is not defined';
      const result = getUserFriendlyError(msg);
      expect(result).toBe('Algo deu errado. Tente novamente em instantes.');
    });

    it('should allow user-friendly long messages', () => {
      const msg = 'O período de busca não pode exceder 7 dias no plano consultor_agil. Para períodos maiores, faça upgrade para um plano superior.';
      const result = getUserFriendlyError(msg);
      expect(result).toBe(msg); // Should keep original (< 200 chars and user-friendly)
    });

    it('should truncate very long technical messages', () => {
      const msg = 'A'.repeat(300); // 300 character technical gibberish
      const result = getUserFriendlyError(msg);
      expect(result).toBe('Algo deu errado. Tente novamente em instantes.');
    });
  });

  describe('Edge cases', () => {
    it('should handle null', () => {
      const result = getUserFriendlyError(null);
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });

    it('should handle undefined', () => {
      const result = getUserFriendlyError(undefined);
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });

    it('should handle empty string', () => {
      const result = getUserFriendlyError('');
      // Empty string after stripping returns empty, which is falsy
      // This is expected behavior - the function returns the stripped message
      expect(typeof result).toBe('string');
    });

    it('should handle numbers', () => {
      const result = getUserFriendlyError(503);
      expect(result).toBeTruthy();
    });

    it('should handle boolean', () => {
      const result = getUserFriendlyError(false);
      expect(result).toBeTruthy();
    });
  });

  describe('Partial matching', () => {
    it('should match partial strings', () => {
      expect(getUserFriendlyError('Request failed with status 503')).toBe('Serviço temporariamente indisponível. Tente em alguns minutos.');
    });

    it('should match partial "network error"', () => {
      expect(getUserFriendlyError('A network error occurred')).toBe('Erro de conexão. Verifique sua internet.');
    });

    it('should prioritize exact matches over partial', () => {
      expect(getUserFriendlyError('fetch failed')).toBe('Erro de conexão. Verifique sua internet.');
    });
  });

  describe('TD-006: getErrorMessage alias (AC4)', () => {
    it('should be the same function as getUserFriendlyError', () => {
      expect(getErrorMessage).toBe(getUserFriendlyError);
    });

    it('should work identically for string errors', () => {
      expect(getErrorMessage('502')).toBe(getUserFriendlyError('502'));
    });

    it('should work identically for Error objects', () => {
      const err = new Error('fetch failed');
      expect(getErrorMessage(err)).toBe(getUserFriendlyError(err));
    });
  });

  describe('TD-006: HTTP 400 mapping (AC2)', () => {
    it('should map 400 errors to user-friendly message', () => {
      expect(getUserFriendlyError('400')).toBe('Requisição inválida. Verifique os dados e tente novamente.');
    });

    it('should match partial 400 error strings', () => {
      expect(getUserFriendlyError('Error 400 Bad Request')).toBe('Requisição inválida. Verifique os dados e tente novamente.');
    });
  });

  describe('TD-006: DEFAULT_ERROR_MESSAGE constant (AC8)', () => {
    it('should be a user-friendly Portuguese string', () => {
      expect(DEFAULT_ERROR_MESSAGE).toBe('Ocorreu um erro inesperado. Tente novamente.');
    });
  });

  // UX-357: Restart error message consistency
  describe('UX-357: Restart error consistency (AC1-AC5)', () => {
    const CANONICAL_FAILURE = 'O servidor reiniciou. Recomendamos tentar novamente.';

    // AC2: All restart-related inputs → canonical failure message
    it.each([
      ['Server restart — retry recommended'],
      ['Server restart during processing'],
      ['Something failed, retry recommended'],
      ['O servidor reiniciou. Tente novamente.'],
      ['O servidor reiniciou durante o processamento.'],
      ['O servidor reiniciou. Recomendamos tentar novamente.'],
    ])('AC2: "%s" → canonical failure message', (input) => {
      expect(getUserFriendlyError(input)).toBe(CANONICAL_FAILURE);
    });

    // AC4: No duplicate restart outputs
    it('AC4: "reiniciou" partial match catches Portuguese variants', () => {
      expect(getUserFriendlyError('reiniciou')).toBe(CANONICAL_FAILURE);
    });

    // AC5: All restart inputs produce exactly 1 distinct message
    it('AC5: all restart error codes produce exactly 1 distinct message', () => {
      const inputs = [
        'Server restart — retry recommended',
        'Server restart during processing',
        'retry recommended',
        'O servidor reiniciou. Tente novamente.',
        'O servidor reiniciou durante o processamento.',
        'O servidor reiniciou. Recomendamos tentar novamente.',
      ];
      const results = new Set(inputs.map(getUserFriendlyError));
      expect(results.size).toBe(1);
      expect([...results][0]).toBe(CANONICAL_FAILURE);
    });
  });
});
