/**
 * Shared MockEventSource for SSE testing.
 *
 * Replaces 6+ duplicated EventSource mocks across test files with a single,
 * W3C-compatible implementation that supports named events, lastEventId,
 * and convenient helper methods.
 *
 * Installed globally in jest.setup.js. Individual tests access instances via
 * `MockEventSource.instances` and use helper methods to simulate SSE events.
 *
 * @example
 * ```typescript
 * import { MockEventSource } from '../utils/mock-event-source';
 *
 * // After a hook creates new EventSource(url):
 * const es = MockEventSource.instances[0];
 * es.simulateOpen();
 * es.simulateMessage({ stage: 'uf_status', detail: { uf: 'SP' } }, { id: '1' });
 * es.simulateError();
 * ```
 */

/** ReadyState constants matching W3C EventSource spec. */
export const CONNECTING = 0;
export const OPEN = 1;
export const CLOSED = 2;

type EventHandler = (event: any) => void;

export class MockEventSource {
  /** All instances created since last reset, ordered by creation time. */
  static instances: MockEventSource[] = [];

  /** Clear all tracked instances. Called in global beforeEach via jest.setup.js. */
  static reset(): void {
    MockEventSource.instances = [];
  }

  readonly url: string;
  readyState: number = CONNECTING;

  onopen: EventHandler | null = null;
  onmessage: EventHandler | null = null;
  onerror: EventHandler | null = null;

  /** Set automatically when simulateMessage includes an `id` option. */
  lastEventId: string = '';

  /** Spyable close — sets readyState=CLOSED (handlers preserved per W3C spec). */
  close: jest.Mock;

  /** Spyable addEventListener — actually registers listeners for named events. */
  addEventListener: jest.Mock;

  /** Spyable removeEventListener — actually removes listeners. */
  removeEventListener: jest.Mock;

  private _listeners: Map<string, Set<EventHandler>> = new Map();

  constructor(url: string) {
    this.url = url;

    this.close = jest.fn(() => {
      this.readyState = CLOSED;
    });

    this.addEventListener = jest.fn((type: string, listener: EventHandler) => {
      if (!this._listeners.has(type)) {
        this._listeners.set(type, new Set());
      }
      this._listeners.get(type)!.add(listener);
    });

    this.removeEventListener = jest.fn((type: string, listener: EventHandler) => {
      this._listeners.get(type)?.delete(listener);
    });

    MockEventSource.instances.push(this);
  }

  // ---------------------------------------------------------------------------
  // Helper methods for tests
  // ---------------------------------------------------------------------------

  /** Set readyState=OPEN and invoke onopen handler. */
  simulateOpen(): void {
    this.readyState = OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }

  /**
   * Simulate an SSE message event.
   *
   * @param data - String or object (auto-stringified if object)
   * @param options.id - Sets lastEventId and includes in the MessageEvent
   * @param options.event - If provided, dispatches to addEventListener listeners
   *   for that event type instead of calling onmessage
   */
  simulateMessage(
    data: string | object,
    options?: { id?: string; event?: string },
  ): void {
    const messageData = typeof data === 'string' ? data : JSON.stringify(data);

    if (options?.id) {
      this.lastEventId = options.id;
    }

    const messageEvent = {
      data: messageData,
      lastEventId: options?.id ?? '',
      origin: '',
      ports: [] as any[],
      source: null,
      type: options?.event ?? 'message',
    };

    if (options?.event) {
      // Dispatch to addEventListener listeners for named events
      const listeners = this._listeners.get(options.event);
      if (listeners) {
        listeners.forEach((listener) => listener(messageEvent));
      }
    } else {
      // Dispatch to onmessage handler (default unnamed event)
      if (this.onmessage) {
        this.onmessage(messageEvent as any);
      }
    }
  }

  /** Simulate an SSE connection error. Invokes onerror handler. */
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}
