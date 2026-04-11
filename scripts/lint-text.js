#!/usr/bin/env node
/**
 * lint-text.js — SmartLic Editorial Linter
 *
 * STORY-436 AC2 (v2): Verifica arquivos de conteúdo em busca de:
 *   1. Termos proibidos (padrões de LLM / burocrês)
 *   2. Markdown exposto visível no HTML renderizado
 *   3. Erros comuns de acentuação em português
 *
 * Escopo: docs/editorial/, frontend/content/ (incluindo templates/)
 * Para TypeScript: extrai string literals — não ignora mais linhas const/let/var.
 * Exit 1 se qualquer violação for encontrada.
 *
 * Uso:
 *   node scripts/lint-text.js
 *   node scripts/lint-text.js --verbose
 */

const fs = require('fs');
const path = require('path');

// ─── Configuração ─────────────────────────────────────────────────────────────

const CONTENT_DIRS = [
  path.join(__dirname, '..', 'docs', 'editorial'),
  path.join(__dirname, '..', 'frontend', 'content'),
];

const EXTENSIONS = ['.md', '.mdx', '.txt', '.tsx', '.ts', '.jsx', '.js'];

const IGNORE_PATTERNS = [
  'estilo-guia.md',                       // guia referencia termos proibidos como exemplos
  'checklist-publicacao.md',
  'guia-observatorio.md',
  'indice-municipal-descricao.ts',        // validador runtime — contém labels dos termos proibidos como código
  'node_modules',
  '.test.',
  '__tests__',
  '.spec.',
  'lint-text.js',                         // o próprio script
];

// ─── Termos Proibidos ─────────────────────────────────────────────────────────

const PROHIBITED_TERMS = [
  // Frases de hedge de LLM
  { term: /é\s+importante\s+(notar|ressaltar|destacar)/gi, suggestion: 'Afirme diretamente ou omita.' },
  { term: /vale\s+ressaltar/gi,                            suggestion: 'Afirme diretamente ou omita.' },
  { term: /fica\s+evidente\s+que/gi,                       suggestion: 'Cite o dado que evidencia.' },
  { term: /no\s+contexto\s+atual/gi,                       suggestion: 'Especifique: "em março de 2026".' },
  { term: /de\s+forma\s+significativa/gi,                  suggestion: 'Dê o número: "alta de 34%".' },
  { term: /de\s+maneira\s+abrangente/gi,                   suggestion: 'Elimine ou reescreva com especificidade.' },
  { term: /de\s+forma\s+expressiva/gi,                     suggestion: 'Dê o número.' },
  { term: /ao\s+longo\s+do\s+tempo/gi,                     suggestion: 'Especifique o período: "nos últimos 12 meses".' },
  { term: /é\s+fundamental/gi,                             suggestion: 'Omita ou reescreva como afirmação.' },
  { term: /\bem\s+suma\b/gi,                               suggestion: 'Vá direto à conclusão.' },
  { term: /\bem\s+resumo\b/gi,                             suggestion: 'Vá direto à conclusão.' },
  { term: /cabe\s+mencionar/gi,                            suggestion: 'Mencione diretamente.' },
  { term: /tendo\s+em\s+vista/gi,                          suggestion: 'Use "Como", "Porque" ou "Dado que".' },
  { term: /no\s+que\s+diz\s+respeito\s+a/gi,               suggestion: 'Use "Sobre" ou "Em".' },
  { term: /apresentou\s+um\s+aumento/gi,                   suggestion: '"[Sujeito] cresceu X%".' },
  { term: /verificou-se\s+que/gi,                          suggestion: '"[Dado] mostra que".' },
  { term: /\bnotável\s+crescimento\b/gi,                   suggestion: 'Use "crescimento de X%".' },
  { term: /evidencia-se/gi,                                suggestion: 'Omita ou cite o dado.' },
  { term: /conforme\s+mencionado/gi,                       suggestion: 'Omita ou repita o fato brevemente.' },
  // Adjetivos vagos de LLM
  { term: /\brobusto\b/gi,                                 suggestion: 'Use dado concreto: "com 40 mil+ registros".' },
  { term: /\bdinâmico\b/gi,                                suggestion: 'Especifique o que muda e quando.' },
  { term: /\babranger\b/gi,                                suggestion: 'Especifique o escopo com números.' },
  // Frases burocráticas extras
  { term: /\bdestaque-se\b/gi,                             suggestion: 'Afirme diretamente.' },
  { term: /\bfica\s+claro\s+que\b/gi,                      suggestion: 'Cite o dado que evidencia.' },
  { term: /\bno\s+que\s+tange\b/gi,                        suggestion: 'Use "Sobre" ou "Em".' },
  { term: /\bem\s+linhas\s+gerais\b/gi,                    suggestion: 'Omita — seja específico.' },
  { term: /\bde\s+modo\s+geral\b/gi,                       suggestion: 'Omita — seja específico.' },
  { term: /\bpode-se\s+observar\b/gi,                      suggestion: 'Afirme diretamente.' },
  { term: /\bé\s+possível\s+notar\b/gi,                    suggestion: 'Afirme diretamente.' },
];

// ─── Markdown Exposto ─────────────────────────────────────────────────────────

// Padrões que produziriam markdown visível no HTML se não processados
const MARKDOWN_ARTIFACTS = [
  { term: /\*\*[^*]+\*\*/g,  suggestion: 'Markdown **negrito** exposto — use <strong> ou texto simples.' },
  { term: /\*[^*\s][^*]*\*/g, suggestion: 'Markdown *itálico* exposto — use <em> ou texto simples.' },
  { term: /^#{1,6}\s/gm,      suggestion: 'Markdown # cabeçalho em template — use JSX diretamente.' },
  { term: /^[-*]\s[^\n]+/gm,  suggestion: 'Markdown lista com - ou * — use array/JSX diretamente.' },
  { term: /_{2}[^_]+_{2}/g,   suggestion: 'Markdown __negrito__ exposto.' },
];

// ─── Erros Comuns de Acentuação ───────────────────────────────────────────────

// Palavras frequentes sem acento (só verificadas em arquivos de conteúdo, não templates TS)
const ACCENT_ERRORS = [
  { term: /\bmunicipio\b/gi,   suggestion: 'Corrija para "município" (com acento).' },
  { term: /\blicitacao\b/gi,   suggestion: 'Corrija para "licitação" (com acento).' },
  { term: /\blicitacoes\b/gi,  suggestion: 'Corrija para "licitações" (com acento).' },
  { term: /\bpublico\b/gi,     suggestion: 'Corrija para "público" (com acento), se adjetivo.' },
  { term: /\borgao\b/gi,       suggestion: 'Corrija para "órgão" (com acento).' },
  { term: /\bsecao\b/gi,       suggestion: 'Corrija para "seção" (com acento).' },
  { term: /\banalise\b/gi,     suggestion: 'Corrija para "análise" (com acento).' },
  { term: /\bperiodo\b/gi,     suggestion: 'Corrija para "período" (com acento).' },
  { term: /\bnumero\b/gi,      suggestion: 'Corrija para "número" (com acento).' },
  { term: /\bindice\b/gi,      suggestion: 'Corrija para "índice" (com acento).' },
  { term: /\bpagina\b/gi,      suggestion: 'Corrija para "página" (com acento).' },
  { term: /\bdados publicos\b/gi, suggestion: 'Corrija para "dados públicos" (com acento em público).' },
];

// ─── Extração de String Literals (TypeScript/JavaScript) ──────────────────────

/**
 * Para arquivos .ts/.tsx/.js/.jsx: extrai apenas o conteúdo de strings literais.
 * Ignora imports, comentários, type declarations, interface bodies, regex literals.
 * Retorna array de { content, lineStart } para contexto de linha.
 */
function extractStringLiterals(content) {
  const results = [];
  const lines = content.split('\n');

  // Regex para capturar string literals (single, double, template)
  // Não captura: imports, comentários // e /* */
  const stringRe = /(['"`])((?:[^\\]|\\.)*?)\1/g;

  for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
    const line = lines[lineIdx];
    const trimmed = line.trim();

    // Ignorar linhas que são puramente código (não têm string user-visible)
    if (
      trimmed.startsWith('import ') ||
      trimmed.startsWith('export type ') ||
      trimmed.startsWith('export interface ') ||
      trimmed.startsWith('interface ') ||
      trimmed.startsWith('type ') ||
      trimmed.startsWith('//') ||
      trimmed.startsWith('/*') ||
      trimmed.startsWith('*') ||
      trimmed.startsWith('}: ') ||
      trimmed === '};' ||
      trimmed === '}' ||
      trimmed.match(/^[a-zA-Z_$][a-zA-Z0-9_$]*\s*[?!]?:\s*\w/)  // type field: type
    ) continue;

    // Extrair strings da linha
    let m;
    stringRe.lastIndex = 0;
    while ((m = stringRe.exec(line)) !== null) {
      const strContent = m[2];
      // Filtrar strings curtas (<10 chars), que provavelmente são identificadores/keys
      if (strContent.length < 10) continue;
      // Filtrar strings que parecem URLs, caminhos ou códigos
      if (/^https?:\/\/|^\/[a-z]|^\d+$/.test(strContent)) continue;
      results.push({ content: strContent, lineIdx });
    }
  }

  return results;
}

// ─── Linting ──────────────────────────────────────────────────────────────────

function shouldIgnore(filePath) {
  const basename = path.basename(filePath);
  return IGNORE_PATTERNS.some((pattern) => basename === pattern || filePath.includes(pattern));
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
  const ext = path.extname(filePath);
  const isTypeScript = ['.ts', '.tsx', '.js', '.jsx'].includes(ext);
  const violations = [];

  if (isTypeScript) {
    // Para TypeScript: verificar apenas dentro de string literals
    const strings = extractStringLiterals(content);
    for (const { content: str, lineIdx } of strings) {
      const checkTerms = [...PROHIBITED_TERMS, ...MARKDOWN_ARTIFACTS, ...ACCENT_ERRORS];
      for (const { term, suggestion } of checkTerms) {
        term.lastIndex = 0;
        const match = term.exec(str);
        if (match) {
          violations.push({
            line: lineIdx + 1,
            col: match.index + 1,
            found: match[0],
            suggestion,
            context: str.slice(0, 120),
          });
        }
      }
    }
  } else {
    // Para Markdown/texto: verificar linha a linha
    const lines = content.split('\n');
    for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
      const line = lines[lineIdx];
      const trimmed = line.trim();

      // Pular: cabeçalhos de tabela Markdown, linhas de código cercado, comentários
      if (trimmed.startsWith('|') || trimmed.startsWith('```') || trimmed.startsWith('<!--')) continue;
      // Pular: exemplos de termos proibidos marcados com backtick inline
      if (/`[^`]+`/.test(trimmed) && trimmed.length < 80) continue;

      const checkTerms = [...PROHIBITED_TERMS, ...ACCENT_ERRORS];
      for (const { term, suggestion } of checkTerms) {
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
    console.log(`\x1b[32m✓ Nenhum termo proibido encontrado. Conteúdo aprovado pelo lint automático.\x1b[0m`);
    process.exit(0);
  }
}

main();
