/**
 * STORY-3.2 (EPIC-TD-2026Q2 / TD-FE-001): Minimal type stubs for untyped
 * third-party globals and SDKs we attach at runtime.
 *
 * Keeps the production code free of `any` casts when interacting with
 * Mixpanel (loaded via script tag at runtime) and Shepherd.js (assigned
 * to `window` by the npm package side-effect).
 */

declare global {
  interface MixpanelClient {
    track(event: string, properties?: Record<string, unknown>): void;
    identify?(distinctId: string): void;
    people?: {
      set(properties: Record<string, unknown>): void;
    };
  }

  interface ShepherdGlobal {
    Tour: new (options?: Record<string, unknown>) => {
      addStep(step: Record<string, unknown>): void;
      start(): void;
      complete(): void;
      cancel(): void;
      next(): void;
      back(): void;
      on(event: string, handler: (...args: unknown[]) => void): void;
    };
  }

  interface Window {
    mixpanel?: MixpanelClient;
  }
}

export {};
