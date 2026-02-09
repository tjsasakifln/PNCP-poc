const fs = require('fs');
const path = require('path');

/**
 * Automated SVG Accessibility Fixer
 * STORY: Fix 122 SVGs without aria-labels
 *
 * Rules:
 * 1. If SVG is decorative (inside button, next to text) → aria-hidden="true"
 * 2. If SVG is informative (standalone icon) → aria-label="[description]" + role="img"
 */

const decorativePatterns = [
  'className="w-4 h-4 ml-2"',        // Trailing button icons
  'className="w-4 h-4 mr-2"',        // Leading button icons
  'className="w-5 h-5 ml-2"',        // Larger trailing icons
  'className="w-3.5 h-3.5"',         // Small decorative
  'animate-spin',                     // Loading spinners
  'rotate-180',                       // Chevrons (toggles)
];

const svgDescriptions = {
  // Arrow icons
  'M13 7l5 5m0 0l-5 5m5-5H6': 'Avançar',
  'M19 9l-7 7-7-7': 'Expandir seção',
  'M5 15l7-7 7 7': 'Recolher seção',

  // Warning/Info icons
  'M12 9v2m0 4h.01': 'Aviso',
  'M13 16h-1v-4h-1m1-4h.01': 'Informação',

  // Check/X icons
  'M5 13l4 4L19 7': 'Confirmado',
  'M6 18L18 6M6 6l12 12': 'Fechar',

  // User/Account icons
  'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z': 'Usuário',

  // Search icon
  'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z': 'Pesquisar',

  // Calendar icon
  'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z': 'Calendário',
};

function isDecorativeSVG(line, nextLines) {
  // Check if SVG has decorative patterns
  for (const pattern of decorativePatterns) {
    if (line.includes(pattern)) return true;
  }

  // Check if SVG is inside a button (next lines contain button text)
  const context = nextLines.slice(0, 5).join(' ');
  if (context.includes('</button>') || context.includes('<button')) {
    return true;
  }

  return false;
}

function getSVGDescription(pathD) {
  for (const [path, description] of Object.entries(svgDescriptions)) {
    if (pathD && pathD.includes(path)) {
      return description;
    }
  }
  return null;
}

function fixSVGsInFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  let modified = false;
  const changes = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Skip if already has aria attributes
    if (line.includes('<svg') &&
        !line.includes('aria-label') &&
        !line.includes('aria-hidden') &&
        !line.includes('role=')) {

      const nextLines = lines.slice(i + 1, i + 10);
      const isDecorative = isDecorativeSVG(line, nextLines);

      // Find the path element to get description
      let pathD = '';
      for (const nextLine of nextLines) {
        if (nextLine.includes(' d="')) {
          const match = nextLine.match(/d="([^"]+)"/);
          if (match) pathD = match[1];
          break;
        }
      }

      if (isDecorative) {
        // Add aria-hidden="true"
        lines[i] = line.replace('<svg', '<svg\n              aria-hidden="true"');
        changes.push(`Line ${i + 1}: Added aria-hidden="true" (decorative)`);
      } else {
        // Add aria-label + role="img"
        const description = getSVGDescription(pathD) || 'Ícone';
        lines[i] = line.replace('<svg',
          `<svg\n              role="img"\n              aria-label="${description}"`);
        changes.push(`Line ${i + 1}: Added aria-label="${description}" + role="img" (informative)`);
      }

      modified = true;
    }
  }

  if (modified) {
    fs.writeFileSync(filePath, lines.join('\n'), 'utf8');
    return changes;
  }

  return null;
}

// Process all files
const filesToFix = [
  // Frente 1: Landing Pages (PRIORITY)
  'frontend/app/components/landing/HeroSection.tsx',
  'frontend/app/components/landing/BeforeAfter.tsx',
  'frontend/app/components/landing/DataSourcesSection.tsx',
  'frontend/app/components/landing/SectorsGrid.tsx',
  'frontend/app/components/landing/OpportunityCost.tsx',
  'frontend/app/components/ComparisonTable.tsx',
  'frontend/app/components/ValuePropSection.tsx',

  // Frente 2: Filters
  'frontend/app/components/EsferaFilter.tsx',
  'frontend/app/components/MunicipioFilter.tsx',
  'frontend/app/components/OrgaoFilter.tsx',
  'frontend/app/components/OrdenacaoSelect.tsx',
  'frontend/app/components/PaginacaoSelect.tsx',
  'frontend/app/components/CustomDateInput.tsx',
  'frontend/app/components/CustomSelect.tsx',

  // Frente 3: UI Components
  'frontend/app/components/LicitacaoCard.tsx',
  'frontend/app/components/StatusBadge.tsx',
  'frontend/app/components/QuotaBadge.tsx',
  'frontend/app/components/PlanBadge.tsx',
  'frontend/app/components/MessageBadge.tsx',
  'frontend/app/components/Countdown.tsx',
  'frontend/app/components/LoadingProgress.tsx',
  'frontend/app/components/SavedSearchesDropdown.tsx',

  // Frente 4: Main Pages
  'frontend/app/buscar/page.tsx',
  'frontend/app/dashboard/page.tsx',
  'frontend/app/dashboard-old.tsx',
  'frontend/app/conta/page.tsx',
  'frontend/app/historico/page.tsx',
  'frontend/app/mensagens/page.tsx',
  'frontend/app/planos/page.tsx',

  // Frente 5: Secondary Pages + Infrastructure
  'frontend/app/login/page.tsx',
  'frontend/app/signup/page.tsx',
  'frontend/app/features/page.tsx',
  'frontend/app/pricing/page.tsx',
  'frontend/app/admin/page.tsx',
  'frontend/app/error.tsx',
  'frontend/app/components/Footer.tsx',
  'frontend/app/components/InstitutionalSidebar.tsx',
  'frontend/app/components/LicitacoesPreview.tsx',
  'frontend/app/components/UpgradeModal.tsx',
];

console.log('🚀 SVG Accessibility Fixer - Starting...\n');
console.log(`📋 Files to process: ${filesToFix.length}\n`);

let totalChanges = 0;
const processedFiles = [];

for (const file of filesToFix) {
  const filePath = path.join(__dirname, file);

  if (!fs.existsSync(filePath)) {
    console.log(`⚠️  SKIP: ${file} (not found)`);
    continue;
  }

  const changes = fixSVGsInFile(filePath);

  if (changes) {
    console.log(`✅ ${file}`);
    changes.forEach(c => console.log(`   ${c}`));
    console.log('');
    totalChanges += changes.length;
    processedFiles.push(file);
  } else {
    console.log(`✓  ${file} (no changes needed)`);
  }
}

console.log('\n' + '='.repeat(60));
console.log(`🎯 Summary:`);
console.log(`   Files processed: ${processedFiles.length}/${filesToFix.length}`);
console.log(`   Total SVGs fixed: ${totalChanges}`);
console.log('='.repeat(60));

if (totalChanges > 0) {
  console.log('\n📝 Next steps:');
  console.log('   1. Review changes: git diff');
  console.log('   2. Test build: cd frontend && npm run build');
  console.log('   3. Validate: node find-svgs-without-aria.js');
  console.log('   4. Commit: git add . && git commit -m "fix(a11y): add aria attributes to 122 SVGs"');
}
