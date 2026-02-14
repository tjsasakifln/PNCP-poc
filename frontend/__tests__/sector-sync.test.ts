/**
 * STORY-249 AC5: Test that frontend SETORES_FALLBACK matches backend sectors_data.yaml
 *
 * This test reads the backend YAML source of truth and compares it against
 * the frontend hardcoded fallback list to ensure they stay in sync.
 * Uses file parsing to avoid importing modules with side effects (Supabase).
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

interface BackendSector {
  name: string;
  description: string;
  max_contract_value?: number;
  keywords?: string[];
}

interface SectorsYaml {
  sectors: Record<string, BackendSector>;
}

// Parse sectors from TypeScript source files (avoids import side-effects)
function parseSectorsFromFile(filePath: string, varName: string): { id: string; name: string; description?: string }[] {
  const content = fs.readFileSync(filePath, 'utf-8');

  // Match the array block: const VAR_NAME = [ ... ];  or const VAR_NAME: Type[] = [ ... ];
  const arrayRegex = new RegExp(`(?:const\\s+${varName}[^=]*=\\s*\\[)([^\\]]+)\\]`, 's');
  const match = content.match(arrayRegex);
  if (!match) throw new Error(`Could not find ${varName} in ${filePath}`);

  const arrayBody = match[1];

  // Extract each { id: "...", name: "...", description: "..." } entry
  const entryRegex = /\{\s*id:\s*"([^"]+)",\s*name:\s*"([^"]+)"(?:,\s*description:\s*"([^"]*)")?\s*\}/g;
  const sectors: { id: string; name: string; description?: string }[] = [];
  let entryMatch;
  while ((entryMatch = entryRegex.exec(arrayBody)) !== null) {
    sectors.push({
      id: entryMatch[1],
      name: entryMatch[2],
      ...(entryMatch[3] !== undefined ? { description: entryMatch[3] } : {}),
    });
  }

  return sectors;
}

describe('Sector Sync (STORY-249)', () => {
  let backendSectors: { id: string; name: string; description: string }[];
  let fallbackSectors: { id: string; name: string; description?: string }[];

  beforeAll(() => {
    // Load backend source of truth
    const yamlPath = path.join(__dirname, '../../backend/sectors_data.yaml');
    const yamlContent = fs.readFileSync(yamlPath, 'utf-8');
    const parsed = yaml.load(yamlContent) as SectorsYaml;

    backendSectors = Object.entries(parsed.sectors).map(([id, data]) => ({
      id,
      name: data.name,
      description: data.description,
    }));

    // Parse frontend fallback from source
    const filtersPath = path.join(__dirname, '../app/buscar/hooks/useSearchFilters.ts');
    fallbackSectors = parseSectorsFromFile(filtersPath, 'SETORES_FALLBACK');
  });

  test('AC5: SETORES_FALLBACK has same number of sectors as backend', () => {
    expect(fallbackSectors.length).toBe(backendSectors.length);
  });

  test('AC5: SETORES_FALLBACK IDs match backend exactly (same order)', () => {
    const fallbackIds = fallbackSectors.map(s => s.id);
    const backendIds = backendSectors.map(s => s.id);
    expect(fallbackIds).toEqual(backendIds);
  });

  test('AC5: SETORES_FALLBACK names match backend exactly', () => {
    for (const backendSector of backendSectors) {
      const fallbackSector = fallbackSectors.find(s => s.id === backendSector.id);
      expect(fallbackSector).toBeDefined();
      expect(fallbackSector!.name).toBe(backendSector.name);
    }
  });

  test('AC5: SETORES_FALLBACK descriptions match backend exactly', () => {
    for (const backendSector of backendSectors) {
      const fallbackSector = fallbackSectors.find(s => s.id === backendSector.id);
      expect(fallbackSector).toBeDefined();
      expect(fallbackSector!.description).toBe(backendSector.description);
    }
  });

  test('AC3: No invented IDs exist in the fallback', () => {
    const inventedIds = ['alimentacao', 'equipamentos', 'limpeza', 'seguranca', 'escritorio', 'construcao', 'servicos'];
    const fallbackIds = fallbackSectors.map(s => s.id);

    for (const invented of inventedIds) {
      expect(fallbackIds).not.toContain(invented);
    }
  });

  test('AC2: signup SECTORS has backend sectors + outro', () => {
    const signupPath = path.join(__dirname, '../app/signup/page.tsx');
    const signupSectors = parseSectorsFromFile(signupPath, 'SECTORS');
    const signupIds = signupSectors.map(s => s.id);

    const expectedIds = [...backendSectors.map(s => s.id), 'outro'];
    expect(signupIds).toEqual(expectedIds);
  });
});
