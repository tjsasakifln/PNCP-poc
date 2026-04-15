/**
 * STORY-2.9 — Setores sync automation tests (script flag + workflow).
 */
import * as fs from 'fs';
import * as path from 'path';

const REPO_ROOT = path.resolve(__dirname, '../..');

describe('STORY-2.9 — Frontend usa /api/setores (AC1)', () => {
  it('useSearchSectorData faz fetch direto de /api/setores', () => {
    const src = fs.readFileSync(
      path.join(REPO_ROOT, 'frontend/app/buscar/hooks/filters/useSearchSectorData.ts'),
      'utf-8'
    );
    expect(src).toContain('/api/setores');
  });

  it('proxy /api/setores existe e aponta para backend /v1/setores', () => {
    const src = fs.readFileSync(
      path.join(REPO_ROOT, 'frontend/app/api/setores/route.ts'),
      'utf-8'
    );
    expect(src).toContain('/v1/setores');
  });

  it('fallback hardcoded preservado em sectorData.ts', () => {
    const src = fs.readFileSync(
      path.join(REPO_ROOT, 'frontend/app/buscar/hooks/filters/sectorData.ts'),
      'utf-8'
    );
    expect(src).toMatch(/SETORES_FALLBACK/);
  });
});

describe('STORY-2.9 — script --check flag (AC3)', () => {
  const SCRIPT = path.join(REPO_ROOT, 'scripts/sync-setores-fallback.js');

  it('script existe', () => {
    expect(fs.existsSync(SCRIPT)).toBe(true);
  });

  it('aceita flag --check (CI mode)', () => {
    const src = fs.readFileSync(SCRIPT, 'utf-8');
    expect(src).toContain("--check");
    expect(src).toContain('isCheckMode');
  });

  it('--check mode chama checkDrift', () => {
    const src = fs.readFileSync(SCRIPT, 'utf-8');
    expect(src).toContain('checkDrift');
    expect(src).toContain('STORY-2.9 AC2+AC3');
  });

  it('--check mode emite JSON estruturado para CI', () => {
    const src = fs.readFileSync(SCRIPT, 'utf-8');
    expect(src).toContain('DRIFT CHECK RESULT');
    expect(src).toContain('JSON.stringify(result');
  });

  it('--check mode lê BACKEND_URL do env quando flag ausente', () => {
    const src = fs.readFileSync(SCRIPT, 'utf-8');
    expect(src).toContain('process.env.BACKEND_URL');
  });
});

describe('STORY-2.9 — GitHub Action mensal (AC2)', () => {
  const WORKFLOW = path.join(REPO_ROOT, '.github/workflows/setores-sync-check.yml');

  it('workflow file existe', () => {
    expect(fs.existsSync(WORKFLOW)).toBe(true);
  });

  it('workflow tem cron mensal', () => {
    const src = fs.readFileSync(WORKFLOW, 'utf-8');
    expect(src).toMatch(/cron:\s*['"]0 9 1 \* \*['"]/);
  });

  it('workflow chama o script com --check', () => {
    const src = fs.readFileSync(WORKFLOW, 'utf-8');
    expect(src).toContain('node scripts/sync-setores-fallback.js --check');
  });

  it('workflow tem job de abrir issue em failure', () => {
    const src = fs.readFileSync(WORKFLOW, 'utf-8');
    expect(src).toContain('Open issue on drift');
    expect(src).toContain('issues: write');
    expect(src).toContain('STORY-2.9');
  });

  it('workflow permite trigger manual via workflow_dispatch', () => {
    const src = fs.readFileSync(WORKFLOW, 'utf-8');
    expect(src).toContain('workflow_dispatch');
  });
});
