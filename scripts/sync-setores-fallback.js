#!/usr/bin/env node

/**
 * Sync Setores Fallback Script
 *
 * This script synchronizes the hardcoded fallback sector list in the frontend
 * with the backend's sector definitions. It should be run monthly or whenever
 * new sectors are added to the backend.
 *
 * Usage:
 *   node scripts/sync-setores-fallback.js [options]
 *
 * Options:
 *   --dry-run    Show what would be changed without modifying files
 *   --backend-url URL   Custom backend URL (default: http://localhost:8000)
 *
 * Requirements:
 *   - Backend must be running
 *   - Backend must have /setores endpoint
 *
 * STORY-170 AC15: Fallback Hardcoded de Setores
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

const FRONTEND_PAGE_PATH = path.join(__dirname, '../frontend/app/buscar/page.tsx');

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
  log('\n📡 Fetching sectors from backend...', 'cyan');
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

    log(`✅ Successfully fetched ${data.setores.length} sectors`, 'green');
    return data.setores;
  } catch (error) {
    log(`❌ Failed to fetch sectors: ${error.message}`, 'red');
    log('\n💡 Make sure the backend is running:', 'yellow');
    log('   cd backend && uvicorn main:app --reload', 'yellow');
    throw error;
  }
}

/**
 * Generate TypeScript code for SETORES_FALLBACK constant
 */
function generateFallbackCode(setores) {
  const entries = setores.map(setor => {
    return `    { id: "${setor.id}", name: "${setor.name}", description: "${setor.description}" },`;
  }).join('\n');

  return `  // Hardcoded fallback list of sectors
  const SETORES_FALLBACK: Setor[] = [
${entries}
  ];`;
}

/**
 * Update the frontend page with new fallback data
 */
async function updateFrontendPage(setores) {
  log('\n📝 Reading frontend page...', 'cyan');

  try {
    let content = await fs.readFile(FRONTEND_PAGE_PATH, 'utf-8');

    // Find the SETORES_FALLBACK constant
    const fallbackRegex = /\/\/ Hardcoded fallback list of sectors\s+const SETORES_FALLBACK: Setor\[\] = \[[^\]]+\];/s;

    if (!fallbackRegex.test(content)) {
      throw new Error('Could not find SETORES_FALLBACK constant in page.tsx');
    }

    const newFallbackCode = generateFallbackCode(setores);
    const updatedContent = content.replace(fallbackRegex, newFallbackCode);

    if (isDryRun) {
      log('\n🔍 DRY RUN MODE - Changes that would be made:', 'yellow');
      log('─'.repeat(60), 'yellow');
      log(newFallbackCode, 'bright');
      log('─'.repeat(60), 'yellow');
      log('\n✅ Dry run complete. No files were modified.', 'green');
      log('   Run without --dry-run to apply changes.\n', 'cyan');
    } else {
      await fs.writeFile(FRONTEND_PAGE_PATH, updatedContent, 'utf-8');
      log('✅ Successfully updated frontend page', 'green');
      log(`   File: ${FRONTEND_PAGE_PATH}\n`, 'cyan');
    }

    return true;
  } catch (error) {
    log(`❌ Failed to update frontend: ${error.message}`, 'red');
    throw error;
  }
}

/**
 * Compare current and new sector lists
 */
function compareSetores(currentCode, newSetores) {
  log('\n📊 Sector comparison:', 'cyan');

  // Extract current sectors from code
  const currentMatches = currentCode.match(/{ id: "([^"]+)"/g) || [];
  const currentIds = currentMatches.map(m => m.match(/"([^"]+)"/)[1]);

  const newIds = newSetores.map(s => s.id);

  const added = newIds.filter(id => !currentIds.includes(id));
  const removed = currentIds.filter(id => !newIds.includes(id));
  const unchanged = currentIds.filter(id => newIds.includes(id));

  log(`   Total sectors: ${newIds.length}`, 'bright');

  if (added.length > 0) {
    log(`   ✨ Added: ${added.join(', ')}`, 'green');
  }

  if (removed.length > 0) {
    log(`   🗑️  Removed: ${removed.join(', ')}`, 'red');
  }

  if (unchanged.length > 0) {
    log(`   ✓ Unchanged: ${unchanged.length} sectors`, 'cyan');
  }

  if (added.length === 0 && removed.length === 0) {
    log(`   ℹ️  No changes detected`, 'yellow');
  }

  console.log();
}

/**
 * Validate sector data structure
 */
function validateSetores(setores) {
  log('\n🔍 Validating sector data...', 'cyan');

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
    log('❌ Validation failed:', 'red');
    errors.forEach(err => log(`   • ${err}`, 'red'));
    throw new Error('Invalid sector data structure');
  }

  log(`✅ All ${setores.length} sectors validated successfully\n`, 'green');
}

/**
 * Main execution
 */
async function main() {
  log('\n' + '='.repeat(60), 'bright');
  log('  Sync Setores Fallback Script', 'bright');
  log('  STORY-170 AC15: Monthly sector synchronization', 'cyan');
  log('='.repeat(60) + '\n', 'bright');

  if (isDryRun) {
    log('🔍 Running in DRY RUN mode\n', 'yellow');
  }

  try {
    // Step 1: Fetch from backend
    const setores = await fetchBackendSetores();

    // Step 2: Validate data
    validateSetores(setores);

    // Step 3: Read current content for comparison
    const currentContent = await fs.readFile(FRONTEND_PAGE_PATH, 'utf-8');
    const currentFallback = currentContent.match(/\/\/ Hardcoded fallback list of sectors[\s\S]+?const SETORES_FALLBACK: Setor\[\] = \[[^\]]+\];/);

    if (currentFallback) {
      compareSetores(currentFallback[0], setores);
    }

    // Step 4: Update frontend
    await updateFrontendPage(setores);

    // Success summary
    log('='.repeat(60), 'green');
    log('  ✅ Synchronization complete!', 'green');
    log('='.repeat(60) + '\n', 'green');

    if (!isDryRun) {
      log('📝 Next steps:', 'cyan');
      log('   1. Review the changes in page.tsx', 'cyan');
      log('   2. Test the frontend with: npm run dev', 'cyan');
      log('   3. Commit the changes if everything looks good\n', 'cyan');
    }

    process.exit(0);
  } catch (error) {
    log('\n' + '='.repeat(60), 'red');
    log('  ❌ Synchronization failed', 'red');
    log('='.repeat(60) + '\n', 'red');
    process.exit(1);
  }
}

// Run the script
main();
