/**
 * STORY-SEO-006: WebVitalsReporter hooks web-vitals callbacks and dispatches
 * GA4 `web_vitals` events via `window.gtag` (silently no-oping when absent).
 *
 * Note: jest.config has `resetMocks: true`, so the mock implementations are
 * wiped between tests. We re-install them in beforeEach to capture handlers.
 */

import React from "react";
import { render } from "@testing-library/react";
import type { Metric } from "web-vitals";
import * as webVitals from "web-vitals";

jest.mock("web-vitals", () => ({
  onCLS: jest.fn(),
  onINP: jest.fn(),
  onLCP: jest.fn(),
  onTTFB: jest.fn(),
  onFCP: jest.fn(),
}));

import { WebVitalsReporter } from "@/app/components/WebVitalsReporter";

type MetricName = "CLS" | "INP" | "LCP" | "TTFB" | "FCP";
const handlers: { [K in MetricName]?: (m: Metric) => void } = {};

function installMocks() {
  for (const key of Object.keys(handlers)) delete handlers[key as MetricName];
  const capture =
    (key: MetricName) =>
    (cb: (m: Metric) => void): void => {
      handlers[key] = cb;
    };
  (webVitals.onCLS as jest.Mock).mockImplementation(capture("CLS"));
  (webVitals.onINP as jest.Mock).mockImplementation(capture("INP"));
  (webVitals.onLCP as jest.Mock).mockImplementation(capture("LCP"));
  (webVitals.onTTFB as jest.Mock).mockImplementation(capture("TTFB"));
  (webVitals.onFCP as jest.Mock).mockImplementation(capture("FCP"));
}

function makeMetric(
  name: Metric["name"],
  value: number,
  delta = value,
  rating: Metric["rating"] = "good"
): Metric {
  return {
    name,
    value,
    delta,
    rating,
    id: `${name}-1`,
    navigationType: "navigate",
    entries: [],
  } as unknown as Metric;
}

describe("WebVitalsReporter (STORY-SEO-006)", () => {
  let gtagSpy: jest.Mock;

  beforeEach(() => {
    installMocks();
    gtagSpy = jest.fn();
    (window as unknown as { gtag?: typeof gtagSpy }).gtag = gtagSpy;
  });

  afterEach(() => {
    delete (window as unknown as { gtag?: unknown }).gtag;
  });

  it("registers callbacks for all five web-vitals metrics on mount", () => {
    render(<WebVitalsReporter />);
    expect(handlers.CLS).toBeDefined();
    expect(handlers.INP).toBeDefined();
    expect(handlers.LCP).toBeDefined();
    expect(handlers.TTFB).toBeDefined();
    expect(handlers.FCP).toBeDefined();
  });

  it("dispatches a GA4 event with rounded integer value for LCP", () => {
    render(<WebVitalsReporter />);
    handlers.LCP!(makeMetric("LCP", 2547.83));

    expect(gtagSpy).toHaveBeenCalledTimes(1);
    const [command, name, params] = gtagSpy.mock.calls[0];
    expect(command).toBe("event");
    expect(name).toBe("web_vitals");
    expect(params).toMatchObject({
      event_category: "Web Vitals",
      event_label: "LCP",
      value: 2548,
      non_interaction: true,
      metric_id: "LCP-1",
      metric_value: 2547.83,
      metric_rating: "good",
    });
  });

  it("scales CLS by 1000 before rounding (GA4 integer aggregation constraint)", () => {
    render(<WebVitalsReporter />);
    handlers.CLS!(makeMetric("CLS", 0.073, 0.012));

    const [, , params] = gtagSpy.mock.calls[0];
    expect(params.value).toBe(73); // 0.073 * 1000 rounded
    expect(params.metric_value).toBe(0.073); // raw float preserved
  });

  it("preserves metric_delta in the dispatched params", () => {
    render(<WebVitalsReporter />);
    handlers.INP!(makeMetric("INP", 150, 22));

    const [, , params] = gtagSpy.mock.calls[0];
    expect(params.metric_delta).toBe(22);
  });

  it("silently no-ops when window.gtag is missing (consent denied / ad-blocker)", () => {
    delete (window as unknown as { gtag?: unknown }).gtag;
    render(<WebVitalsReporter />);

    expect(() => handlers.LCP!(makeMetric("LCP", 1234))).not.toThrow();
  });

  it("renders nothing (null component)", () => {
    const { container } = render(<WebVitalsReporter />);
    expect(container.firstChild).toBeNull();
  });
});
