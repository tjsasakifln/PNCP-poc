/**
 * Portuguese Stopwords for Term Validation
 *
 * Common Portuguese words that are typically filtered out from search queries
 * to improve search precision and prevent false matches.
 *
 * Categories:
 * - Articles: o, a, os, as, um, uma, etc.
 * - Prepositions: de, em, por, para, com, etc.
 * - Conjunctions: e, ou, mas, etc.
 * - Common adverbs: não, muito, já, etc.
 * - High-frequency verbs: ser, ter, estar, ir, etc.
 *
 * Used by term validation logic to filter out meaningless single-word queries.
 */

export const STOPWORDS_PT = new Set([
  // Articles
  "o", "a", "os", "as", "um", "uma", "uns", "umas",

  // Prepositions
  "de", "do", "da", "dos", "das",
  "em", "no", "na", "nos", "nas",
  "por", "pelo", "pela", "pelos", "pelas",
  "para", "pra", "pro",
  "com", "sem", "sob", "sobre", "entre",
  "ate", "desde", "apos", "perante", "contra", "ante",
  "ao", "aos", "num", "numa", "nuns", "numas",

  // Conjunctions
  "e", "ou", "mas", "porem", "que", "se", "como",
  "quando", "porque", "pois", "nem", "tanto", "quanto",
  "logo", "portanto",

  // Common adverbs
  "nao", "mais", "muito", "tambem", "ja", "ainda", "so", "apenas",

  // High-frequency verbs (infinitive form)
  "ser", "ter", "estar", "ir", "vir", "fazer", "dar", "ver",

  // Common verb forms
  "ha", "foi", "sao", "era", "sera",
]);

/**
 * Utility function: Strip accents from Portuguese text
 *
 * Converts "não" → "nao", "está" → "esta", etc.
 * Used for accent-insensitive stopword matching.
 */
export function stripAccents(text: string): string {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

/**
 * Check if a word is a Portuguese stopword (case and accent insensitive)
 *
 * @example
 * isStopword("não")   // true (normalized to "nao")
 * isStopword("NÃO")   // true (case insensitive)
 * isStopword("obra")  // false
 */
export function isStopword(word: string): boolean {
  return STOPWORDS_PT.has(stripAccents(word.toLowerCase()));
}
