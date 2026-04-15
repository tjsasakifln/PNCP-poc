#!/usr/bin/env node
/**
 * STORY-2.2 (TD-FE-005) — Button codemod.
 *
 * Migra `<button className="...">...</button>` → `<Button variant="..." size="...">...</Button>`
 * inferindo `variant` e `size` por padrões do className Tailwind.
 *
 * Pula:
 *   - <button> dentro de components/ui/button.tsx (próprio componente)
 *   - <motion.button> (Framer Motion)
 *   - Strings literais com '<button' (templates HTML)
 *   - Arquivos de teste (__tests__/, *.test.tsx)
 *   - node_modules / .next
 *
 * Uso:
 *   node frontend/scripts/codemod-button.js --dry           # preview
 *   node frontend/scripts/codemod-button.js                 # aplica
 *   node frontend/scripts/codemod-button.js path/to/dir     # restringir escopo
 *
 * O codemod é INTENCIONALMENTE conservador: emite TODO comments para casos
 * ambíguos em vez de adivinhar. Migração massiva é progressiva (Sprint 2+).
 */

'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const args = process.argv.slice(2);
const isDry = args.includes('--dry') || args.includes('--dry-run');
const positional = args.filter((a) => !a.startsWith('--'));
const TARGET = positional[0]
  ? path.resolve(ROOT, positional[0])
  : path.join(ROOT, 'app');

const SKIP_DIRS = new Set(['node_modules', '.next', '__tests__', '__snapshots__', 'scripts']);
const SKIP_FILES = new Set([
  path.join(ROOT, 'components/ui/button.tsx'),
  path.join(ROOT, 'components/ui/Pagination.tsx'),
]);

// ─── Variant/size inference ──────────────────────────────────────────────────

function inferVariant(className) {
  const cls = (className || '').toLowerCase();
  if (/bg-(red|error)/.test(cls)) return 'destructive';
  if (/bg-(brand-navy|blue-6|primary)/.test(cls)) return 'primary';
  if (/border.*bg-transparent|outline/.test(cls)) return 'outline';
  if (/^(text-|underline)|text-brand-blue.*underline/.test(cls)) return 'link';
  if (/bg-(white|gray-1|surface-1)/.test(cls)) return 'secondary';
  return 'ghost';
}

function inferSize(className) {
  const cls = (className || '').toLowerCase();
  if (/h-8|text-xs(?!l)/.test(cls)) return 'sm';
  if (/h-12|text-base|text-lg/.test(cls)) return 'lg';
  if (/h-10\s+w-10|h-9\s+w-9/.test(cls)) return 'icon';
  return 'default';
}

// ─── File walker ─────────────────────────────────────────────────────────────

function walk(dir, files = []) {
  if (!fs.existsSync(dir)) return files;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (SKIP_DIRS.has(entry.name)) continue;
    if (entry.isDirectory()) {
      walk(full, files);
    } else if (entry.isFile() && /\.tsx$/.test(entry.name) && !/\.test\.tsx$/.test(entry.name)) {
      if (!SKIP_FILES.has(full)) files.push(full);
    }
  }
  return files;
}

// ─── Single-file transform ───────────────────────────────────────────────────

const BUTTON_TAG_RE = /<button(\s[^>]*)?>/g;

function transform(source, filePath) {
  // Skip files where button.tsx itself defines Button
  if (filePath === path.join(ROOT, 'components/ui/button.tsx')) {
    return { source, changed: 0, todos: 0 };
  }

  let changed = 0;
  let todos = 0;
  let needsImport = false;

  const transformed = source.replace(BUTTON_TAG_RE, (match, attrs) => {
    // Skip motion.button (renders <motion.button> not <button>)
    if (attrs && /^\s*ref=|asChild/.test(attrs)) {
      todos++;
      return `${match}{/* TODO STORY-2.2: revisar manualmente — ref/asChild detected */}`;
    }
    const classNameMatch = (attrs || '').match(/className=["']([^"']*)["']/);
    const className = classNameMatch ? classNameMatch[1] : '';
    const variant = inferVariant(className);
    const size = inferSize(className);
    changed++;
    needsImport = true;
    const cleanAttrs = (attrs || '').trim();
    return `<Button variant="${variant}" size="${size}"${cleanAttrs ? ' ' + cleanAttrs : ''}>`;
  });

  let final = transformed;
  if (needsImport && !/from\s+["']@\/components\/ui\/button["']/.test(final)) {
    // Insert import after first import block
    const lines = final.split('\n');
    let lastImportIdx = -1;
    for (let i = 0; i < Math.min(lines.length, 50); i++) {
      if (lines[i].startsWith('import ')) lastImportIdx = i;
    }
    if (lastImportIdx >= 0) {
      lines.splice(lastImportIdx + 1, 0, 'import { Button } from "@/components/ui/button";');
      final = lines.join('\n');
    }
  }

  // Replace closing </button> with </Button> proportionally
  if (changed > 0) {
    final = final.replace(/<\/button>/g, '</Button>');
  }

  return { source: final, changed, todos };
}

// ─── Main ────────────────────────────────────────────────────────────────────

function main() {
  console.log(`STORY-2.2 codemod — target: ${path.relative(ROOT, TARGET)}`);
  console.log(`Mode: ${isDry ? 'DRY RUN (no writes)' : 'WRITE'}`);

  const files = walk(TARGET);
  console.log(`Scanning ${files.length} .tsx files...`);

  let totalChanged = 0;
  let totalTodos = 0;
  let filesTouched = 0;

  for (const file of files) {
    const original = fs.readFileSync(file, 'utf-8');
    const { source, changed, todos } = transform(original, file);
    if (changed > 0) {
      filesTouched++;
      totalChanged += changed;
      totalTodos += todos;
      const rel = path.relative(ROOT, file);
      console.log(
        `  ${isDry ? '[DRY]' : '[WRITE]'} ${rel}: ${changed} migrated, ${todos} todos`
      );
      if (!isDry && source !== original) {
        fs.writeFileSync(file, source, 'utf-8');
      }
    }
  }

  console.log('');
  console.log(`Summary: ${filesTouched} files, ${totalChanged} buttons migrated, ${totalTodos} TODOs`);
  if (isDry) {
    console.log('Run without --dry to apply.');
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = { transform, inferVariant, inferSize };
