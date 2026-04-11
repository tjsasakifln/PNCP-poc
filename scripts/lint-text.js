#!/usr/bin/env node
/**
 * lint-text.js — SmartLic Editorial Linter
 *
 * STORY-436 AC2: Verifica arquivos de conteúdo em busca de termos proibidos
 * que revelam geração automática de texto (padrões de LLM).
 *
 * Escopo: docs/editorial/ e frontend/content/
 * Exit 1 se qualquer termo proibido for encontrado.
 *
 * Uso:
 *   node scripts/lint-text.js
 *   node scripts/lint-text.js --verbose
 *   node scripts/lint-text.js --fix-suggestions
 */

const fs = require('fs');
const path = require('path');
const glob = require('fs');

// ─── Configuração ────────────────────────────────────────────────────────────

const CONTENT_DIRS = [
  path.join(__dirname, '..', 'docs', 'editorial'),
  path.join(__dirname, '..', 'frontend', 'content'),
];

// Extensões de arquivo para verificar
const EXTENSIONS = ['.md', '.mdx', '.txt', '.tsx', '.ts', '.jsx', '.js'];

// Arquivos/padrões para ignorar
const IGNORE_PATTERNS = [
  'estilo-guia.md',          // próprio guia pode referenciar termos proibidos
  'node_modules',
  '.test.',
  '__tests__',
  '*.spec.',
];

// ─── Termos Proibidos ─────────────────────────────────────────────────────────

const PROHIBITED_TERMS = [
  // Frases de hedge de LLM
  { term: /é\s+importante\s+(notar|ressaltar|destacar)/gi, suggestion: 'Afirme diretamente ou omita.' },
  { term: /vale\s+ressaltar/gi, suggestion: 'Afirme diretamente ou omita.' },
  { term: /fica\s+evidente\s+que/gi, suggestion: 'Cite o dado que evidencia.' },
  { term: /no\s+contexto\s+atual/gi, suggestion: 'Especifique: "em março de 2026".' },
  { term: /de\s+forma\s+significativa/gi, suggestion: 'Dê o número: "alta de 34%".' },
  { term: /de\s+maneira\s+abrangente/gi, suggestion: 'Elimine ou reescreva com especificidade.' },
  { term: /de\s+forma\s+expressiva/gi, suggestion: 'Dê o número.' },
  { term: /ao\s+longo\s+do\s+tempo/gi, suggestion: 'Especifique o período: "nos últimos 12 meses".' },
  { term: /é\s+fundamental/gi, suggestion: 'Omita ou reescreva como afirmação.' },
  { term: /\bem\s+suma\b/gi, suggestion: 'Vá direto à conclusão.' },
  { term: /\bem\s+resumo\b/gi, suggestion: 'Vá direto à conclusão.' },
  { term: /cabe\s+mencionar/gi, suggestion: 'Mencione diretamente.' },
  { term: /tendo\s+em\s+vista/gi, suggestion: 'Use "Como", "Porque" ou "Dado que".' },
  { term: /no\s+que\s+diz\s+respeito\s+a/gi, suggestion: 'Use "Sobre" ou "Em".' },
  { term: /apresentou\s+um\s+aumento/gi, suggestion: '"[Sujeito] cresceu X%".' },
  { term: /verificou-se\s+que/gi, suggestion: '"[Dado] mostra que".' },
  { term: /\bnotável\s+crescimento\b/gi, suggestion: 'Use "crescimento de X%".' },
  { term: /evidencia-se/gi, suggestion: 'Omita ou cite o dado.' },
  { term: /conforme\s+mencionado/gi, suggestion: 'Omita ou repita o fato brevemente.' },
  // Adjetivos vagos de LLM
  { term: /\brobusto\b/gi, suggestion: 'Use dado concreto: "com 40 mil+ registros".' },
  { term: /\bdinâmico\b/gi, suggestion: 'Especifique o que muda e quando.' },
  { term: /\babranger\b/gi, suggestion: 'Especifique o escopo com números.' },
];

// ─── Funções auxiliares ───────────────────────────────────────────────────────

function shouldIgnore(filePath) {
  const basename = path.basename(filePath);
  return IGNORE_PATTERNS.some((pattern) => {
    if (typeof pattern === 'string') return basename === pattern || filePath.includes(pattern);
    return pattern.test(filePath);
  });
}

function getFilesRecursive(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (shouldIgnore(fullPath)) continue;
    if (entry.isDirectory()) {
      files.push(...getFilesRecursive(fullPath));
    } else if (entry.isFile() && EXTENSIONS.includes(path.extname(entry.name))) {
      files.push(fullPath);
    }
  }
  return files;
}

function lintFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const violations = [];

  for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
    const line = lines[lineIdx];
    // Skip code blocks, comments, variable declarations
    const trimmed = line.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('*')) continue;
    if (trimmed.startsWith('const ') || trimmed.startsWith('let ') || trimmed.startsWith('var ')) continue;
    if (trimmed.startsWith('|') || trimmed.startsWith('`')) continue; // table rows and code spans

    for (const { term, suggestion } of PROHIBITED_TERMS) {
      term.lastIndex = 0;
      const match = term.exec(line);
      if (match) {
        violations.push({
          line: lineIdx + 1,
          col: match.index + 1,
          found: match[0],
          suggestion,
          context: line.trim().slice(0, 100),
        });
      }
    }
  }

  return violations;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const verbose = process.argv.includes('--verbose');
  let totalViolations = 0;
  let totalFiles = 0;
  let filesWithViolations = 0;

  for (const dir of CONTENT_DIRS) {
    const files = getFilesRecursive(dir);
    for (const filePath of files) {
      totalFiles++;
      const violations = lintFile(filePath);
      if (violations.length > 0) {
        filesWithViolations++;
        totalViolations += violations.length;
        const relPath = path.relative(process.cwd(), filePath);
        console.error(`\n\x1b[31m✗\x1b[0m ${relPath} — ${violations.length} violação(ões):`);
        for (const v of violations) {
          console.error(`  Linha ${v.line}:${v.col}  \x1b[33m"${v.found}"\x1b[0m`);
          console.error(`  → ${v.suggestion}`);
          if (verbose) console.error(`  Contexto: ${v.context}`);
        }
      } else if (verbose) {
        const relPath = path.relative(process.cwd(), filePath);
        console.log(`\x1b[32m✓\x1b[0m ${relPath}`);
      }
    }
  }

  console.log(`\nVerificados ${totalFiles} arquivo(s).`);

  if (totalViolations > 0) {
    console.error(`\x1b[31m✗ ${totalViolations} violação(ões) em ${filesWithViolations} arquivo(s). Corrija antes de publicar.\x1b[0m`);
    process.exit(1);
  } else {
    console.log(`\x1b[32m✓ Nenhum termo proibido encontrado.\x1b[0m`);
    process.exit(0);
  }
}

main();
