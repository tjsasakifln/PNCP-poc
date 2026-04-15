/**
 * STORY-2.2 — Button codemod tests (unit).
 *
 * Covers:
 *  - Variant inference from Tailwind classes (AC1)
 *  - Size inference (AC1)
 *  - Skip rules (AC1)
 *  - ESLint forbid-elements rule installed (AC2)
 *  - Codemod script + ESLint config presence (AC4)
 */
import * as fs from 'fs';
import * as path from 'path';

const REPO_ROOT = path.resolve(__dirname, '../..');
const FE = path.join(REPO_ROOT, 'frontend');

// eslint-disable-next-line @typescript-eslint/no-var-requires
const codemod = require(path.join(FE, 'scripts/codemod-button.js'));

describe('STORY-2.2 — codemod inferVariant (AC1)', () => {
  it('detecta destructive em bg-red', () => {
    expect(codemod.inferVariant('bg-red-500 text-white px-4')).toBe('destructive');
  });

  it('detecta primary em bg-brand-navy', () => {
    expect(codemod.inferVariant('bg-brand-navy text-white')).toBe('primary');
  });

  it('detecta outline em border + bg-transparent', () => {
    expect(codemod.inferVariant('border bg-transparent text-blue-600')).toBe('outline');
  });

  it('detecta secondary em bg-gray', () => {
    expect(codemod.inferVariant('bg-gray-100 text-gray-700')).toBe('secondary');
  });

  it('default fallback é ghost', () => {
    expect(codemod.inferVariant('p-2 m-1')).toBe('ghost');
  });
});

describe('STORY-2.2 — codemod inferSize (AC1)', () => {
  it('detecta sm em h-8', () => {
    expect(codemod.inferSize('h-8 px-3')).toBe('sm');
  });

  it('detecta lg em h-12', () => {
    expect(codemod.inferSize('h-12 text-base')).toBe('lg');
  });

  it('detecta icon em h-10 w-10', () => {
    expect(codemod.inferSize('h-10 w-10 rounded-full')).toBe('icon');
  });

  it('default size é default', () => {
    expect(codemod.inferSize('px-4 py-2')).toBe('default');
  });
});

describe('STORY-2.2 — codemod transform (AC1)', () => {
  it('migra <button className=...> para <Button variant=... size=...>', () => {
    const input = `import React from 'react';
export function X() {
  return <button className="bg-brand-navy h-12">Click</button>;
}`;
    const { source, changed } = codemod.transform(input, '/fake/path.tsx');
    expect(changed).toBe(1);
    expect(source).toContain('<Button variant="primary" size="lg"');
    expect(source).toContain('</Button>');
    expect(source).toContain('@/components/ui/button');
  });

  it('preserva attrs originais', () => {
    const input = `<button className="bg-red-500" onClick={fn} type="submit">X</button>`;
    const { source } = codemod.transform(input, '/fake.tsx');
    expect(source).toContain('onClick={fn}');
    expect(source).toContain('type="submit"');
    expect(source).toContain('variant="destructive"');
  });

  it('não dobra import quando @/components/ui/button já presente', () => {
    const input = `import React from 'react';
import { Button } from "@/components/ui/button";
export function X() { return <button className="h-8">x</button>; }`;
    const { source } = codemod.transform(input, '/fake.tsx');
    const importCount = (source.match(/from\s+["']@\/components\/ui\/button["']/g) || []).length;
    expect(importCount).toBe(1);
  });

  it('emite TODO em casos ambíguos (asChild)', () => {
    const input = `<button asChild className="x">y</button>`;
    const { todos } = codemod.transform(input, '/fake.tsx');
    expect(todos).toBeGreaterThan(0);
  });

  it('skip button.tsx próprio', () => {
    const input = `<button>x</button>`;
    const result = codemod.transform(input, path.join(FE, 'components/ui/button.tsx'));
    expect(result.changed).toBe(0);
  });
});

describe('STORY-2.2 — ESLint rule (AC2)', () => {
  it('.eslintrc.json tem react/forbid-elements para <button>', () => {
    const cfg = JSON.parse(fs.readFileSync(path.join(FE, '.eslintrc.json'), 'utf-8'));
    const overrides = cfg.overrides || [];
    const found = overrides.some((o: { rules?: Record<string, unknown> }) => {
      const rule = o.rules?.['react/forbid-elements'];
      if (!Array.isArray(rule)) return false;
      const config = rule[1] as { forbid?: Array<{ element: string }> };
      return config.forbid?.some((f) => f.element === 'button');
    });
    expect(found).toBe(true);
  });

  it('.eslintrc.json exclui o próprio button.tsx do bloqueio', () => {
    const cfg = JSON.parse(fs.readFileSync(path.join(FE, '.eslintrc.json'), 'utf-8'));
    const overrides = cfg.overrides || [];
    const buttonOverride = overrides.find((o: { rules?: Record<string, unknown> }) =>
      o.rules?.['react/forbid-elements']
    );
    expect(buttonOverride?.excludedFiles).toContain('components/ui/button.tsx');
  });
});

describe('STORY-2.2 — Codemod artifact (AC4)', () => {
  it('script existe', () => {
    expect(fs.existsSync(path.join(FE, 'scripts/codemod-button.js'))).toBe(true);
  });

  it('script tem documentação STORY-2.2', () => {
    const src = fs.readFileSync(path.join(FE, 'scripts/codemod-button.js'), 'utf-8');
    expect(src).toContain('STORY-2.2');
    expect(src).toContain('TD-FE-005');
  });
});
