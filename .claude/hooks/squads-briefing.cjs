#!/usr/bin/env node
'use strict';
//
// SessionStart hook — injects a compact catalog of aiox-* squads (<2KB)
// into the session context. Silent-fails if squads/ is absent.
//
// Budget: additionalContext must stay <= 2048 bytes.

const fs = require('fs');
const path = require('path');

const MAX_BYTES = 2048;
const SQUADS_DIR = path.join(process.cwd(), 'squads');

function readStdin() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => {
      try { resolve(JSON.parse(data)); } catch (_) { resolve({}); }
    });
    process.stdin.on('error', () => resolve({}));
  });
}

function extractOneLiner(yamlContent) {
  // Try multi-line block scalar first: `description: >` or `description: |` followed by content on next non-empty line
  const lines = yamlContent.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(/^\s*description:\s*([>|][-+]?)\s*$/);
    if (m) {
      for (let j = i + 1; j < lines.length && j < i + 6; j++) {
        const trimmed = lines[j].trim();
        if (trimmed && !trimmed.startsWith('#')) {
          return trimmed.replace(/["']/g, '').slice(0, 120);
        }
      }
    }
  }
  // Try inline description
  const descMatch = yamlContent.match(/^\s*description:\s*["']?([^>|"'\n].*?)["']?\s*$/m);
  if (descMatch) return descMatch[1].replace(/["']/g, '').slice(0, 120);
  // Fallback to title
  const titleMatch = yamlContent.match(/^\s*title:\s*["']?(.+?)["']?\s*$/m);
  if (titleMatch) return titleMatch[1].replace(/["']/g, '').slice(0, 120);
  return '';
}

function extractName(yamlContent, squadDir) {
  const m = yamlContent.match(/^\s*(name|display_name):\s*["']?(.+?)["']?\s*$/m);
  if (m) return m[2].replace(/["']/g, '');
  return path.basename(squadDir);
}

function readSquadInfo(squadPath) {
  const squadYaml = path.join(squadPath, 'squad.yaml');
  const configYaml = path.join(squadPath, 'config.yaml');
  let yamlPath = null;
  if (fs.existsSync(squadYaml)) yamlPath = squadYaml;
  else if (fs.existsSync(configYaml)) yamlPath = configYaml;
  if (!yamlPath) return null;
  try {
    const content = fs.readFileSync(yamlPath, 'utf8');
    return {
      id: path.basename(squadPath),
      name: extractName(content, squadPath),
      oneline: extractOneLiner(content),
    };
  } catch (_) {
    return null;
  }
}

function listAioxSquads() {
  if (!fs.existsSync(SQUADS_DIR)) return [];
  try {
    const entries = fs.readdirSync(SQUADS_DIR, { withFileTypes: true });
    return entries
      .filter(e => e.isDirectory() && e.name.startsWith('aiox-'))
      .map(e => readSquadInfo(path.join(SQUADS_DIR, e.name)))
      .filter(Boolean);
  } catch (_) {
    return [];
  }
}

function buildBriefing(squads) {
  if (squads.length === 0) return null;
  const header = '<squads-aiox-available>\nSmartLic tem squads aiox-* customizados (vendored de SynkraAI/aiox-squads). Invoque via /<nome> ou deixe o smart-router rotear automaticamente.\n';
  const lines = squads.map(s => `- ${s.id}: ${s.oneline || s.name}`.slice(0, 180));
  const body = lines.join('\n');
  const footer = '\nVer squads/_shared/ para contexto B2G comum (glossário, schema Supabase, invariants).\n</squads-aiox-available>';
  let full = header + body + footer;
  // Truncate body if over budget
  while (Buffer.byteLength(full, 'utf8') > MAX_BYTES && lines.length > 0) {
    lines.pop();
    full = header + lines.join('\n') + '\n  [...truncated for budget...]' + footer;
  }
  return full;
}

async function main() {
  await readStdin(); // input ignored
  const squads = listAioxSquads();
  const briefing = buildBriefing(squads);
  if (!briefing) return;
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: briefing,
    },
  }));
}

const timer = setTimeout(() => process.exit(0), 2000);
timer.unref();
main().then(() => process.exit(0)).catch(() => process.exit(0));
