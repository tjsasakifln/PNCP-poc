/**
 * Shared Constants - Central Export
 *
 * Re-exports all shared constants for easier imports throughout the app.
 *
 * @example
 * ```tsx
 * // Before (multiple imports):
 * import { UF_NAMES } from '@/lib/constants/uf-names';
 * import { STOPWORDS_PT } from '@/lib/constants/stopwords';
 *
 * // After (single import):
 * import { UF_NAMES, STOPWORDS_PT } from '@/lib/constants';
 * ```
 */

// UF (Brazilian states) constants
export {
  UF_NAMES,
  UFS,
  type UF,
} from "./uf-names";

// Portuguese stopwords for term validation
export {
  STOPWORDS_PT,
  stripAccents,
  isStopword,
} from "./stopwords";
