/**
 * STORY-274 AC4: API proxy for Prometheus /metrics endpoint.
 *
 * Fetches raw Prometheus text exposition format from the backend
 * and returns it as JSON-parsed metrics for the admin dashboard.
 *
 * Backend endpoint: GET /metrics (Prometheus ASGI app, root-mounted)
 * Auth: Optional Bearer token via METRICS_TOKEN env var.
 */

import { NextRequest, NextResponse } from "next/server";
import { sanitizeNetworkError } from "../../../../lib/proxy-error-handler";

/** Parse Prometheus text exposition format into structured metrics. */
function parsePrometheusText(text: string): Record<string, PrometheusMetric> {
  const metrics: Record<string, PrometheusMetric> = {};
  const lines = text.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      // Parse HELP and TYPE comments
      if (trimmed.startsWith("# HELP ")) {
        const rest = trimmed.slice(7);
        const spaceIdx = rest.indexOf(" ");
        if (spaceIdx > 0) {
          const name = rest.slice(0, spaceIdx);
          const help = rest.slice(spaceIdx + 1);
          if (!metrics[name]) {
            metrics[name] = { name, help: "", type: "", samples: [] };
          }
          metrics[name].help = help;
        }
      } else if (trimmed.startsWith("# TYPE ")) {
        const rest = trimmed.slice(7);
        const spaceIdx = rest.indexOf(" ");
        if (spaceIdx > 0) {
          const name = rest.slice(0, spaceIdx);
          const type = rest.slice(spaceIdx + 1);
          if (!metrics[name]) {
            metrics[name] = { name, help: "", type: "", samples: [] };
          }
          metrics[name].type = type;
        }
      }
      continue;
    }

    // Parse metric sample line: metric_name{labels} value
    const match = trimmed.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+(.+)$/);
    if (match) {
      const [, sampleName, labelsStr, valueStr] = match;
      const value = parseFloat(valueStr);

      // Find parent metric name (strip _total, _bucket, _sum, _count suffixes)
      let parentName = sampleName;
      for (const suffix of ["_total", "_bucket", "_sum", "_count", "_created"]) {
        if (parentName.endsWith(suffix)) {
          const candidate = parentName.slice(0, -suffix.length);
          if (metrics[candidate]) {
            parentName = candidate;
            break;
          }
        }
      }

      if (!metrics[parentName]) {
        metrics[parentName] = { name: parentName, help: "", type: "", samples: [] };
      }

      const labels: Record<string, string> = {};
      if (labelsStr) {
        const labelContent = labelsStr.slice(1, -1); // Remove { }
        const labelParts = labelContent.match(/([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"/g);
        if (labelParts) {
          for (const part of labelParts) {
            const eqIdx = part.indexOf("=");
            const key = part.slice(0, eqIdx);
            const val = part.slice(eqIdx + 2, -1); // Remove ="..."
            labels[key] = val;
          }
        }
      }

      metrics[parentName].samples.push({
        name: sampleName,
        labels,
        value: isNaN(value) ? 0 : value,
      });
    }
  }

  return metrics;
}

interface PrometheusMetric {
  name: string;
  help: string;
  type: string;
  samples: Array<{
    name: string;
    labels: Record<string, string>;
    value: number;
  }>;
}

export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  // Require admin auth (forwarded to check on the frontend side via session)
  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json(
      { message: "Autenticacao necessaria" },
      { status: 401 }
    );
  }

  try {
    // Build headers for backend /metrics endpoint
    const headers: Record<string, string> = {};

    // If METRICS_TOKEN is set, use it for backend auth
    const metricsToken = process.env.METRICS_TOKEN;
    if (metricsToken) {
      headers["Authorization"] = `Bearer ${metricsToken}`;
    }

    const response = await fetch(`${backendUrl}/metrics`, { headers });

    if (!response.ok) {
      // ISSUE-056: distinguish "token missing" from "token wrong" for easier diagnosis
      if (response.status === 401) {
        const metricsTokenSet = !!process.env.METRICS_TOKEN;
        const errorMsg = metricsTokenSet
          ? "Backend metrics indisponivel: METRICS_TOKEN configurado no frontend mas rejeitado pelo backend. Verifique se o valor coincide com a variavel METRICS_TOKEN no servico backend (railway variables --service bidiq-backend)."
          : "Backend metrics indisponivel: METRICS_TOKEN nao configurado no frontend. Configure a variavel de ambiente METRICS_TOKEN no Railway (servico frontend) com o mesmo valor do backend.";
        return NextResponse.json(
          { error: errorMsg, raw: null, metrics: null },
          { status: 503 }
        );
      }
      return NextResponse.json(
        { error: `Backend returned ${response.status}`, raw: null, metrics: null },
        { status: response.status }
      );
    }

    const rawText = await response.text();

    // Parse Prometheus text format into structured data
    const metrics = parsePrometheusText(rawText);

    // Extract key metrics for the dashboard
    const dashboard = extractDashboardMetrics(metrics);

    return NextResponse.json({
      raw_available: true,
      metrics_count: Object.keys(metrics).length,
      dashboard,
      metrics,
    });
  } catch (error) {
    console.error("Error fetching /metrics:", error);
    return sanitizeNetworkError(error);
  }
}

/** Extract key dashboard metrics from parsed Prometheus data. */
function extractDashboardMetrics(metrics: Record<string, PrometheusMetric>) {
  const getSum = (name: string): number => {
    const m = metrics[name];
    if (!m) return 0;
    // For counters with _total suffix, sum all _total samples
    const totalSamples = m.samples.filter((s) => s.name.endsWith("_total") || s.name === name);
    return totalSamples.reduce((sum, s) => sum + s.value, 0);
  };

  const getGaugeValue = (name: string, labels?: Record<string, string>): number => {
    const m = metrics[name];
    if (!m) return 0;
    if (labels) {
      const sample = m.samples.find((s) =>
        Object.entries(labels).every(([k, v]) => s.labels[k] === v)
      );
      return sample?.value ?? 0;
    }
    return m.samples[0]?.value ?? 0;
  };

  const getHistogramAvg = (name: string): number => {
    const m = metrics[name];
    if (!m) return 0;
    const sumSample = m.samples.find((s) => s.name === `${name}_sum`);
    const countSample = m.samples.find((s) => s.name === `${name}_count`);
    if (!sumSample || !countSample || countSample.value === 0) return 0;
    return sumSample.value / countSample.value;
  };

  const getLabeledSamples = (name: string): Array<{ labels: Record<string, string>; value: number }> => {
    const m = metrics[name];
    if (!m) return [];
    return m.samples
      .filter((s) => s.name.endsWith("_total") || s.name === name)
      .map((s) => ({ labels: s.labels, value: s.value }));
  };

  // Cache metrics
  const cacheHits = getSum("smartlic_cache_hits");
  const cacheMisses = getSum("smartlic_cache_misses");
  const cacheTotal = cacheHits + cacheMisses;
  const cacheHitRate = cacheTotal > 0 ? cacheHits / cacheTotal : 0;

  // Search metrics
  const totalSearches = getSum("smartlic_searches");
  const avgSearchDuration = getHistogramAvg("smartlic_search_duration_seconds");
  const activeSearches = getGaugeValue("smartlic_active_searches");

  // Error metrics
  const totalApiErrors = getSum("smartlic_api_errors");
  const totalSearchErrors = getSum("smartlic_search_error_type");

  // LLM metrics
  const totalLlmCalls = getSum("smartlic_llm_calls");
  const avgLlmDuration = getHistogramAvg("smartlic_llm_call_duration_seconds");
  const totalLlmTokens = getSum("smartlic_llm_tokens");

  // Circuit breaker
  const cbPncp = getGaugeValue("smartlic_circuit_breaker_degraded", { source: "pncp" });
  const cbPcp = getGaugeValue("smartlic_circuit_breaker_degraded", { source: "portal_compras" });
  const cbComprasGov = getGaugeValue("smartlic_circuit_breaker_degraded", { source: "compras_gov" });

  // SSE
  const sseErrors = getSum("smartlic_sse_connection_errors");

  // Rate limiting
  const rateLimitExceeded = getSum("smartlic_rate_limit_exceeded");

  // Filter decisions
  const filterDecisions = getLabeledSamples("smartlic_filter_decisions");

  // Fetch durations by source
  const fetchDurations: Record<string, number> = {};
  const fetchMetric = metrics["smartlic_fetch_duration_seconds"];
  if (fetchMetric) {
    const sources = new Set(fetchMetric.samples.map((s) => s.labels.source).filter(Boolean));
    for (const source of sources) {
      const sumSample = fetchMetric.samples.find(
        (s) => s.name === "smartlic_fetch_duration_seconds_sum" && s.labels.source === source
      );
      const countSample = fetchMetric.samples.find(
        (s) => s.name === "smartlic_fetch_duration_seconds_count" && s.labels.source === source
      );
      if (sumSample && countSample && countSample.value > 0) {
        fetchDurations[source] = sumSample.value / countSample.value;
      }
    }
  }

  // API errors by source
  const apiErrorsBySource = getLabeledSamples("smartlic_api_errors");

  // STORY-312 AC11: CTA conversion metrics
  const ctaShown = getLabeledSamples("smartlic_cta_shown");
  const ctaClicked = getLabeledSamples("smartlic_cta_clicked");
  const ctaDismissed = getLabeledSamples("smartlic_cta_dismissed");

  // Build per-variant breakdown
  const ctaVariants: Array<{ variant: string; shown: number; clicked: number; dismissed: number; ctr: number }> = [];
  const allVariants = new Set([
    ...ctaShown.map((s) => s.labels.variant),
    ...ctaClicked.map((s) => s.labels.variant),
    ...ctaDismissed.map((s) => s.labels.variant),
  ]);

  for (const v of allVariants) {
    if (!v) continue;
    const shown = ctaShown.find((s) => s.labels.variant === v)?.value ?? 0;
    const clicked = ctaClicked.find((s) => s.labels.variant === v)?.value ?? 0;
    const dismissed = ctaDismissed.find((s) => s.labels.variant === v)?.value ?? 0;
    const ctr = shown > 0 ? Math.round((clicked / shown) * 1000) / 10 : 0;
    ctaVariants.push({ variant: v, shown, clicked, dismissed, ctr });
  }

  // Sort by CTR descending
  ctaVariants.sort((a, b) => b.ctr - a.ctr);

  return {
    search: {
      total: totalSearches,
      active: activeSearches,
      avg_duration_s: Math.round(avgSearchDuration * 100) / 100,
    },
    cache: {
      hits: cacheHits,
      misses: cacheMisses,
      hit_rate: Math.round(cacheHitRate * 1000) / 10,
    },
    errors: {
      api_total: totalApiErrors,
      search_total: totalSearchErrors,
      sse_total: sseErrors,
      rate_limit_total: rateLimitExceeded,
      by_source: apiErrorsBySource,
    },
    llm: {
      total_calls: totalLlmCalls,
      avg_duration_s: Math.round(avgLlmDuration * 1000) / 1000,
      total_tokens: totalLlmTokens,
    },
    circuit_breaker: {
      pncp: cbPncp === 1 ? "DEGRADED" : "HEALTHY",
      portal_compras: cbPcp === 1 ? "DEGRADED" : "HEALTHY",
      compras_gov: cbComprasGov === 1 ? "DEGRADED" : "HEALTHY",
    },
    fetch_durations: fetchDurations,
    filter_decisions: filterDecisions,
    cta_conversion: ctaVariants,
  };
}
