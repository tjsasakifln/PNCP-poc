/**
 * Text utilities for converting markdown source into plain text.
 *
 * Primary use case: feeding `answer`/`definition`/`body` fields into
 * schema.org JSON-LD (QAPage, FAQPage, Article) where markdown markers
 * would leak to search engines and AI Overviews as literal characters.
 *
 * This is intentionally NOT a full markdown-to-text converter — it only
 * strips the inline decorations and block markers used in SmartLic's
 * static content (bold, italic, headings, lists, inline code, links).
 */

/**
 * Strip markdown syntax, leaving plain text suitable for JSON-LD output
 * and meta description fallbacks.
 *
 * Transformations (in order):
 * - Bold (`**x**` / `__x__`) → `x`
 * - Italic (`*x*` / `_x_`)   → `x`
 * - Inline code (`` `x` ``)  → `x`
 * - Links (`[text](url)`)    → `text`
 * - Images (`![alt](url)`)   → `alt`
 * - Headings (`# `, `## `, …) → removed leading markers
 * - Bullet list markers (`- `, `* `, `+ `) → removed
 * - Numbered list markers (`1. `, `2. `) → removed
 * - Blockquote marker (`> `) → removed
 * - Table pipes/separators → spaces
 * - Collapses multiple consecutive whitespace into a single space
 */
export function stripMarkdown(md: string): string {
  if (!md) return '';

  let text = md;

  // Images: ![alt](url) → alt
  text = text.replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1');
  // Links: [text](url) → text
  text = text.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1');
  // Bold: **x** or __x__ → x
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/__([^_]+)__/g, '$1');
  // Italic: *x* or _x_ → x (avoid **...**, already handled)
  text = text.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '$1');
  text = text.replace(/(?<!_)_([^_\n]+)_(?!_)/g, '$1');
  // Inline code: `x` → x
  text = text.replace(/`([^`]+)`/g, '$1');
  // Strikethrough: ~~x~~ → x
  text = text.replace(/~~([^~]+)~~/g, '$1');

  // Block markers (start of line)
  text = text.replace(/^\s{0,3}#{1,6}\s+/gm, '');   // headings
  text = text.replace(/^\s*[-*+]\s+/gm, '');         // bullet lists
  text = text.replace(/^\s*\d+\.\s+/gm, '');         // numbered lists
  text = text.replace(/^\s*>\s?/gm, '');             // blockquotes
  // Table separator row (---|---|) — strip BEFORE collapsing pipes
  text = text.replace(/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/gm, '');
  // Table pipes → spaces (only when clearly table rows)
  text = text.replace(/\s*\|\s*/g, ' ');

  // Collapse whitespace
  text = text.replace(/\r\n?/g, '\n');
  text = text.replace(/\s+/g, ' ').trim();

  return text;
}
