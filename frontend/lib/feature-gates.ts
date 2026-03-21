/**
 * DEBT-FE-012: Feature gate configuration.
 *
 * Pages listed here show a ComingSoonPage instead of the actual page content.
 * Remove a feature from this set to enable it.
 *
 * SHIP-002 AC9: Alertas and Mensagens are feature-gated.
 */

export const GATED_FEATURES = new Set([
  "alertas",
  "mensagens",
]);

export function isFeatureGated(feature: string): boolean {
  return GATED_FEATURES.has(feature);
}
