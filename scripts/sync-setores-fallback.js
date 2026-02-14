#!/usr/bin/env node

/**
 * Sync Setores Fallback Script
 *
 * Synchronizes hardcoded sector lists in the frontend with the backend's
 * sector definitions (sectors_data.yaml via /setores endpoint).
 *
 * Targets:
 *   1. useSearchFilters.ts  → SETORES_FALLBACK (id, name, description)
 *   2. signup/page.tsx      → SECTORS (id, name) + { id: "outro", name: "Outro" }
 *
 * Usage:
 *   node scripts/sync-setores-fallback.js [options]
 *
 * Options:
 *   --dry-run          Show what would be changed without modifying files
 *   --backend-url URL  Custom backend URL (default: http://localhost:8000)
 *
 * Requirements:
 *   - Backend must be running with /setores endpoint
 *
 * STORY-170 AC15 + STORY-249 AC4
 */

const fs = require('fs').promises;
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
const backendUrlIndex = args.indexOf('--backend-url');
const BACKEND_URL = backendUrlIndex !== -1 && args[backendUrlIndex + 1]
  ? args[backendUrlIndex + 1]
  : 'http://localhost:8000';

// Target file paths
const SEARCH_FILTERS_PATH = path.join(__dirname, '../frontend/app/buscar/hooks/useSearchFilters.ts');
const SIGNUP_PAGE_PATH = path.join(__dirname, '../frontend/app/signup/page.tsx');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * Fetch sectors from backend API
 */
async function fetchBackendSetores() {
  log('\n  Fetching sectors from backend...', 'cyan');
  log(`   URL: ${BACKEND_URL}/setores\n`, 'cyan');

  try {
    const response = await fetch(`${BACKEND_URL}/setores`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.setores || !Array.isArray(data.setores)) {
      throw new Error('Invalid response format: missing "setores" array');
    }

    log(`   Successfully fetched ${data.setores.length} sectors`, 'green');
    return data.setores;
  } catch (error) {
    log(`   Failed to fetch sectors: ${error.message}`, 'red');
    log('\n   Make sure the backend is running:', 'yellow');
    log('   cd backend && uvicorn main:app --reload', 'yellow');
    throw error;
  }
}

/**
 * Validate sector data structure
 */
function validateSetores(setores) {
  log('\n   Validating sector data...', 'cyan');

  const errors = [];

  setores.forEach((setor, index) => {
    if (!setor.id || typeof setor.id !== 'string') {
      errors.push(`Sector ${index}: missing or invalid "id"`);
    }
    if (!setor.name || typeof setor.name !== 'string') {
      errors.push(`Sector ${index}: missing or invalid "name"`);
    }
    if (!setor.description || typeof setor.description !== 'string') {
      errors.push(`Sector ${index}: missing or invalid "description"`);
    }
  });

  if (errors.length > 0) {
    log('   Validation failed:', 'red');
    errors.forEach(err => log(`   - ${err}`, 'red'));
    throw new Error('Invalid sector data structure');
  }

  log(`   All ${setores.length} sectors validated successfully\n`, 'green');
}

/**
 * Compare current and new sector lists (by ID)
 */
function compareSetores(label, currentCode, newIds) {
  log(`\n   Sector comparison [${label}]:`, 'cyan');

  const currentMatches = currentCode.match(/id: "([^"]+)"/g) || [];
  const currentIds = currentMatches.map(m => m.match(/"([^"]+)"/)[1]);

  const added = newIds.filter(id => !currentIds.includes(id));
  const removed = currentIds.filter(id => !newIds.includes(id));
  const unchanged = currentIds.filter(id => newIds.includes(id));

  log(`   Total sectors: ${newIds.length}`, 'bright');

  if (added.length > 0) {
    log(`   + Added: ${added.join(', ')}`, 'green');
  }

  if (removed.length > 0) {
    log(`   - Removed: ${removed.join(', ')}`, 'red');
  }

  if (unchanged.length > 0) {
    log(`   = Unchanged: ${unchanged.length} sectors`, 'cyan');
  }

  if (added.length === 0 && removed.length === 0) {
    log(`   No changes detected`, 'yellow');
  }

  console.log();
  return { added, removed };
}

// ─── Target 1: useSearchFilters.ts SETORES_FALLBACK ──────────────────────────

function generateFallbackCode(setores) {
  const entries = setores.map(setor => {
    return `  { id: "${setor.id}", name: "${setor.name}", description: "${setor.description}" },`;
  }).join('\n');

  return `// Fallback sectors list — synced with backend/sectors_data.yaml (STORY-249)
const SETORES_FALLBACK: Setor[] = [
${entries}
];`;
}

async function updateSearchFilters(setores) {
  log('   [1/2] Updating useSearchFilters.ts SETORES_FALLBACK...', 'cyan');

  const content = await fs.readFile(SEARCH_FILTERS_PATH, 'utf-8');

  const fallbackRegex = /\/\/ Fallback sectors list[^\n]*\nconst SETORES_FALLBACK: Setor\[\] = \[[^\]]+\];/s;

  if (!fallbackRegex.test(content)) {
    throw new Error('Could not find SETORES_FALLBACK constant in useSearchFilters.ts');
  }

  // Compare before applying
  const currentMatch = content.match(fallbackRegex);
  if (currentMatch) {
    compareSetores('useSearchFilters.ts', currentMatch[0], setores.map(s => s.id));
  }

  const newCode = generateFallbackCode(setores);
  const updatedContent = content.replace(fallbackRegex, newCode);

  if (isDryRun) {
    log('   DRY RUN - useSearchFilters.ts would become:', 'yellow');
    log('   ' + '-'.repeat(50), 'yellow');
    log(newCode, 'bright');
    log('   ' + '-'.repeat(50), 'yellow');
  } else {
    await fs.writeFile(SEARCH_FILTERS_PATH, updatedContent, 'utf-8');
    log(`   Updated: ${SEARCH_FILTERS_PATH}`, 'green');
  }
}

// ─── Target 2: signup/page.tsx SECTORS ────────────────────────────────────────

function generateSignupCode(setores) {
  const entries = setores.map(setor => {
    return `  { id: "${setor.id}", name: "${setor.name}" },`;
  }).join('\n');

  return `// Available sectors — synced with backend/sectors_data.yaml (STORY-249)
const SECTORS = [
${entries}
  { id: "outro", name: "Outro" },
];`;
}

async function updateSignupPage(setores) {
  log('   [2/2] Updating signup/page.tsx SECTORS...', 'cyan');

  const content = await fs.readFile(SIGNUP_PAGE_PATH, 'utf-8');

  const sectorsRegex = /\/\/ Available sectors[^\n]*\nconst SECTORS = \[[^\]]+\];/s;

  if (!sectorsRegex.test(content)) {
    throw new Error('Could not find SECTORS constant in signup/page.tsx');
  }

  // Compare before applying
  const currentMatch = content.match(sectorsRegex);
  if (currentMatch) {
    const idsWithOutro = [...setores.map(s => s.id), 'outro'];
    compareSetores('signup/page.tsx', currentMatch[0], idsWithOutro);
  }

  const newCode = generateSignupCode(setores);
  const updatedContent = content.replace(sectorsRegex, newCode);

  if (isDryRun) {
    log('   DRY RUN - signup/page.tsx would become:', 'yellow');
    log('   ' + '-'.repeat(50), 'yellow');
    log(newCode, 'bright');
    log('   ' + '-'.repeat(50), 'yellow');
  } else {
    await fs.writeFile(SIGNUP_PAGE_PATH, updatedContent, 'utf-8');
    log(`   Updated: ${SIGNUP_PAGE_PATH}`, 'green');
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  log('\n' + '='.repeat(60), 'bright');
  log('  Sync Setores Fallback Script', 'bright');
  log('  STORY-249 AC4: Sync useSearchFilters.ts + signup/page.tsx', 'cyan');
  log('='.repeat(60) + '\n', 'bright');

  if (isDryRun) {
    log('   Running in DRY RUN mode\n', 'yellow');
  }

  try {
    // Step 1: Fetch from backend
    const setores = await fetchBackendSetores();

    // Step 2: Validate data
    validateSetores(setores);

    // Step 3: Update both targets
    await updateSearchFilters(setores);
    await updateSignupPage(setores);

    // Success summary
    log('\n' + '='.repeat(60), 'green');
    log('  Synchronization complete!', 'green');
    log('='.repeat(60) + '\n', 'green');

    if (!isDryRun) {
      log('   Next steps:', 'cyan');
      log('   1. Review changes in useSearchFilters.ts and signup/page.tsx', 'cyan');
      log('   2. Test the frontend with: npm run dev', 'cyan');
      log('   3. Commit the changes if everything looks good\n', 'cyan');
    }

    process.exit(0);
  } catch (error) {
    log('\n' + '='.repeat(60), 'red');
    log('  Synchronization failed', 'red');
    log('='.repeat(60) + '\n', 'red');
    process.exit(1);
  }
}

// Run the script
main();
