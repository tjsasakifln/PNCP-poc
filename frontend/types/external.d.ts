/**
 * STORY-3.2 (EPIC-TD-2026Q2 / TD-FE-001): Minimal type stubs for untyped
 * third-party globals and SDKs we attach at runtime.
 *
 * Keeps the production code free of `any` casts when interacting with
 * Mixpanel (loaded via script tag at runtime).
 */

declare global {
  interface MixpanelClient {
    track(event: string, properties?: Record<string, unknown>): void;
    identify?(distinctId: string): void;
    people?: {
      set(properties: Record<string, unknown>): void;
    };
  }

  interface Window {
    mixpanel?: MixpanelClient;
  }
}

export {};
