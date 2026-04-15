/**
 * STORY-2.4: Helper que consolida sinais existentes do useSearchSSE em um
 * único `connectionState` legível pelo banner de UI.
 *
 * Estados:
 * - 'idle'         — busca não iniciada (search loading=false)
 * - 'connected'    — SSE recebendo eventos normalmente
 * - 'reconnecting' — drop detectado, aguardando próximo retry (1-5 tentativas)
 * - 'failed'       — todas tentativas esgotadas, sem polling fallback
 * - 'polling'      — fallback ativo (atualizações via /api/search-status a cada 3s)
 */

export type SseConnectionState =
  | 'idle'
  | 'connected'
  | 'reconnecting'
  | 'failed'
  | 'polling';

export interface SseConnectionInputs {
  /** Busca em andamento (loading). False ⇒ idle. */
  active: boolean;
  /** SSE conectado e recebendo eventos. */
  isConnected: boolean;
  /** Reconnect em andamento (entre disconnect e próximo connect). */
  isReconnecting: boolean;
  /** SSE finalizou (todas tentativas esgotadas). */
  sseDisconnected: boolean;
  /** SSE falhou e polling fallback foi ativado. */
  pollingActive?: boolean;
  /** SSE sem evento por 120s. */
  inactivityTimeout?: boolean;
}

export function deriveSseConnectionState(input: SseConnectionInputs): SseConnectionState {
  if (!input.active) return 'idle';
  if (input.pollingActive) return 'polling';
  if (input.sseDisconnected || input.inactivityTimeout) return 'failed';
  if (input.isReconnecting) return 'reconnecting';
  if (input.isConnected) return 'connected';
  return 'idle';
}

export const SSE_MAX_RETRIES_DEFAULT = 5;
