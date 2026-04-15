#!/usr/bin/env node
/**
 * STORY-4.3 (TD-FE-004) — Hex color audit script.
 *
 * Scans `app/` and `components/` for hex literals and arbitrary Tailwind
 * values, emits a CSV + JSON report summarising remaining work.
 *
 * Usage:
 *   node frontend/scripts/audit-hex.js [--out=./docs/tech-debt/hex-audit]
 *
 * Output:
 *   <out>.json  — machine-readable list
 *   <out>.csv   — human spreadsheet (path, line, kind, match, context)
 */

'use strict';

const fs = require('fs');
const path = require('path');

const HEX_LITERAL_RE = /#[0-9a-fA-F]{3,8}\b/g;
const TAILWIND_ARBITRARY_RE = /\b(bg|text|border|ring|fill|stroke|from|to|via|outline|decoration|placeholder|caret|accent|shadow|divide)-\[#[0-9a-fA-F]{3,8}\]/g;

const INCLUDE_DIRS = ['app', 'components', 'hooks', 'lib'];
const EXCLUDE_DIRS = new Set(['node_modules', '.next', 'coverage', 'test-results', 'e2e-tests']);
// OG image routes genuinely need hex literals — @vercel/og doesn't parse CSS vars.
const ALLOWLIST_PATTERNS = [
  /app\/api\/og\//,
  /\.test\.(ts|tsx)$/,
  /__tests__\//,
  /tailwind\.config\.ts$/,
  /sentry\..*\.config\.ts$/,
];

function isAllowed(filePath) {
  return ALLOWLIST_PATTERNS.some((re) => re.test(filePath));
}

function walk(dir, out) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (EXCLUDE_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, out);
    } else if (entry.isFile() && /\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      out.push(full);
    }
  }
}

function scanFile(filePath, results) {
  const normalised = filePath.replace(/\\/g, '/');
  if (isAllowed(normalised)) return;
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split(/\r?\n/);
  for (let idx = 0; idx < lines.length; idx++) {
    const line = lines[idx];
    for (const match of line.matchAll(TAILWIND_ARBITRARY_RE)) {
      results.push({
        file: normalised,
        line: idx + 1,
        kind: 'arbitrary_class',
        match: match[0],
        context: line.trim().slice(0, 200),
      });
    }
    for (const match of line.matchAll(HEX_LITERAL_RE)) {
      // Skip lines already covered by arbitrary class matches to avoid double-counting.
      if (TAILWIND_ARBITRARY_RE.test(line)) {
        TAILWIND_ARBITRARY_RE.lastIndex = 0;
        continue;
      }
      results.push({
        file: normalised,
        line: idx + 1,
        kind: 'hex_literal',
        match: match[0],
        context: line.trim().slice(0, 200),
      });
    }
  }
}

function toCsv(rows) {
  const header = ['file', 'line', 'kind', 'match', 'context'];
  const escape = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const body = rows.map((r) => header.map((k) => escape(r[k])).join(','));
  return [header.join(','), ...body].join('\n');
}

function main() {
  const args = process.argv.slice(2);
  const outArg = args.find((a) => a.startsWith('--out='));
  const out = outArg ? outArg.slice('--out='.length) : './docs/tech-debt/hex-audit';
  const outDir = path.dirname(out);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  const repoRoot = path.resolve(__dirname, '..');
  const files = [];
  for (const dirName of INCLUDE_DIRS) {
    const abs = path.join(repoRoot, dirName);
    if (fs.existsSync(abs)) walk(abs, files);
  }

  const results = [];
  for (const f of files) scanFile(f, results);

  results.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line);

  fs.writeFileSync(`${out}.json`, JSON.stringify(results, null, 2), 'utf8');
  fs.writeFileSync(`${out}.csv`, toCsv(results), 'utf8');

  const byFile = new Map();
  for (const r of results) byFile.set(r.file, (byFile.get(r.file) || 0) + 1);
  const topFiles = [...byFile.entries()].sort((a, b) => b[1] - a[1]).slice(0, 20);

  console.log('STORY-4.3 Hex Audit');
  console.log('-------------------');
  console.log(`Total findings  : ${results.length}`);
  console.log(`Files with hits : ${byFile.size}`);
  console.log(`Output (JSON)   : ${out}.json`);
  console.log(`Output (CSV)    : ${out}.csv`);
  console.log('');
  console.log('Top 20 files:');
  for (const [file, count] of topFiles) {
    console.log(`  ${String(count).padStart(4)}  ${file}`);
  }
}

main();
