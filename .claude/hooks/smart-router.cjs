#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROUTES = [
  // === Squads aiox (SynkraAI/aiox-squads registry) — MUST come before generic architect/qa/marketing ===
  { patterns: [/\bLei\s?14\.?133\b/i, /\bjurisprud[êe]ncia\b.*\blicita[çc][ãa]o\b/i, /\b(impugna[çc][ãa]o|habilita[çc][ãa]o)\b.*\b(edital|licita[çc][ãa]o)\b/i, /\bacórd[ãa]o\s+(TCU|TCE)\b/i],
    skill: 'aiox-legal-analyst', label: 'SQUAD LEGAL-ANALYST' },
  { patterns: [/\b(SSE|EventSource)\b/, /\b(componente|refactor|performance).*frontend.*(buscar|pipeline|dashboard)\b/i, /\bShepherd\b/i, /\banima[çc][ãa]o.*(buscar|pipeline|onboarding)\b/i, /\bfrontend.*(architecture|arquitetura)\b/i],
    skill: 'aiox-apex', label: 'SQUAD APEX' },
  { patterns: [/\bsupplier_contracts\b/i, /\bSEO\b.*\b(org[âa]nico|blog|observat[óo]rio|sitemap)\b/i, /\binbound org[âa]nico\b/i, /\bprogrammatic\s+SEO\b/i],
    skill: 'aiox-seo', label: 'SQUAD SEO' },
  { patterns: [/\b(pesquisa|an[áa]lise)\b.*\b(multi.?fonte|setorial.*B2G)\b/i, /\bdeep research\b/i, /\banalisar mercado\b.*\blicita[çc][ãa]o\b/i, /\bs[íi]ntese.*evid[êe]ncia\b/i, /\bPICO\b/],
    skill: 'aiox-deep-research', label: 'SQUAD DEEP-RESEARCH' },
  { patterns: [/\bparaleliz(ar|a[çc][ãa]o)\b.*\b(UF|batch|agentes?|story)\b/i, /\bdispatch\b.*\bagentes?\b/i, /\bdecomp[õo]r\s+story\b/i, /\bwave.*execu[çc][ãa]o\b/i],
    skill: 'aiox-dispatch', label: 'SQUAD DISPATCH' },
  { patterns: [/\bkaizen\b/i, /\bmemo?ria.*(sess[ãa]o|longo prazo|ecossistema)\b/i, /\baprendizado cont[íi]nuo\b/i, /\bdaily sensing\b/i, /\bEbbinghaus\b/i],
    skill: 'aiox-kaizen-v2', label: 'SQUAD KAIZEN-V2' },

  // Desenvolvimento
  { patterns: [/\bbug\b/i, /\berro\b/i, /\bquebrou\b/i, /\bfix\b/i, /\bnão funciona\b/i, /\bproblema\b/i, /\bfalha\b/i],
    skill: 'squad-creator', args: 'bidiq-hotfix', label: 'BUG/HOTFIX' },
  { patterns: [/\bfeature\b/i, /\bfuncionalidade\b/i, /\bimplementar\b/i, /\bimplementação\b/i, /\bimplementando\b/i, /\badicionar\b/i, /\bdesenvolver\b/i, /nova.*feature/i, /\bnova.*funcionalidade\b/i, /\bYOLO\b/],
    skill: 'squad-creator', args: 'bidiq-feature-e2e', label: 'FEATURE' },
  { patterns: [/\bintegrar api\b/i, /\bnovo cliente\b/i, /\bfonte de dados\b/i, /\bintegração\b.*\bapi\b/i],
    skill: 'squad-creator', args: 'bidiq-api-integration', label: 'API INTEGRATION' },
  { patterns: [/\bperformance\b/i, /\blento\b/i, /\btimeout\b/i, /\botimizar\b/i, /\blatência\b/i],
    skill: 'squad-creator', args: 'bidiq-performance-audit', label: 'PERFORMANCE' },
  { patterns: [/próxima issue/i, /o que fazer/i, /próximo passo/i, /\bprioridade\b/i, /\bbacklog\b/i],
    skill: 'pick-next-issue', label: 'NEXT ISSUE' },
  { patterns: [/\brevisar pr\b/i, /\bfazer merge\b/i, /\bvalidar pr\b/i, /\bgovernance pr\b/i, /\breview.*pr\b/i],
    skill: 'review-pr', label: 'PR REVIEW' },
  { patterns: [/\broadmap\b/i, /\bauditar\b/i, /está atrasado/i, /\bstatus geral\b/i, /\bsincronizar\b/i],
    skill: 'audit-roadmap', label: 'ROADMAP AUDIT' },
  { patterns: [/\bbanco de dados\b/i, /\bschema\b/i, /\bmigrações?\b/i, /\bsupabase\b.*\bestrutura\b/i, /\bRLS\b/, /\bquery\b/i],
    skill: 'data-engineer', label: 'DATA ENGINEER' },
  { patterns: [/\bcriar\s+testes?\b/i, /\bescrev[ae]r?\s+testes?\b/i, /\bgerar\s+testes?\b/i, /\brodar\s+testes?\b/i, /\bexecutar\s+testes?\b/i, /\btestes?\s+falhando\b/i, /\btestes?\s+quebrando\b/i, /\bcobertura\s+de\s+testes?\b/i, /\bcobertura\b.*\btestes?\b/i, /\bsuite.*testes?\b/i, /\bQA\b/, /\bvalidação.*qualidade\b/i, /\btest\s+coverage\b/i, /\btest\s+suite\b/i],
    skill: 'qa', label: 'QA' },
  { patterns: [/\barquitetura\b/i, /\bimpacto.*mudança\b/i, /\bADR\b/, /\bdesign.*sistema\b/i, /\btrade-off\b/i],
    skill: 'architect', label: 'ARCHITECT' },

  // Inteligência B2G
  { patterns: [/\bCNPJ\b/i, /\bedi.*histórico\b/i, /\banalisar.*CNPJ\b/i],
    skill: 'intel-busca', label: 'INTEL-BUSCA' },
  { patterns: [/\bpreço\b.*\bbenchmark\b/i, /\bvalor estimado\b/i, /\bmargem\b/i, /\bP50\b/, /\bP90\b/],
    skill: 'pricing-b2g', label: 'PRICING B2G' },
  { patterns: [/\bparticip.*edital\b/i, /\bgo-no-go\b/i, /\bdossiê\b/i, /\bchecklist.*habilitação\b/i],
    skill: 'war-room-b2g', label: 'WAR ROOM B2G' },
  { patterns: [/\bmonitorar editais\b/i, /\bradar\b.*\beditais\b/i, /\bnovos editais\b/i, /\balertas.*editais\b/i],
    skill: 'radar-b2g', label: 'RADAR B2G' },
  { patterns: [/\brelatório executivo\b/i, /\banálise profunda\b/i],
    skill: 'report-b2g', label: 'REPORT B2G' },
  { patterns: [/\bmapear concorrentes\b/i, /\bfornecedores\b.*\bplayers\b/i, /\bmarket share\b/i],
    skill: 'intel-b2g', label: 'INTEL B2G' },
  { patterns: [/\bqualificar leads\b/i, /\bscoring\b/i, /\bpriorizar prospects\b/i],
    skill: 'qualify-b2g', label: 'QUALIFY B2G' },
  { patterns: [/\bcadência\b/i, /\bprospecção\b/i, /\bsequência.*abordagem\b/i, /\bfollow-up sistemático\b/i],
    skill: 'cadencia-b2g', label: 'CADENCIA B2G' },
  { patterns: [/\bpipeline comercial\b/i, /\bfunil\b/i, /\bforecast\b/i, /\bestágios.*venda\b/i],
    skill: 'pipeline-b2g', label: 'PIPELINE B2G' },
  { patterns: [/\bproposta comercial\b/i, /\bapresentação\b/i, /\bdeck\b/i],
    skill: 'proposta-b2g', label: 'PROPOSTA B2G' },
  { patterns: [/\breter cliente\b/i, /\bupsell\b/i, /\bchurn\b/i, /\bhealth score\b/i, /\brenovação\b/i],
    skill: 'retention-b2g', label: 'RETENTION B2G' },

  // Advisory Boards
  { patterns: [/\bcopy\b/i, /\btexto\b.*\blanding\b/i, /\bemail marketing\b/i, /\bUX writing\b/i],
    skill: 'copymasters', label: 'COPYMASTERS' },
  { patterns: [/\bcold email\b/i, /\bcold outreach\b/i, /\bSDR\b/, /\babordagem inicial\b/i],
    skill: 'outreach', label: 'OUTREACH' },
  { patterns: [/\brevenue\b/i, /\bmonetização\b/i, /\bunit economics\b/i, /\bmodelo de negócio\b/i],
    skill: 'turbocash', label: 'TURBOCASH' },
  { patterns: [/\bdecisão técnica\b/i, /\bCTO\b/, /\bmarketing\b.*\bcrescimento\b/i, /\bGTM\b/],
    skill: 'conselho', label: 'CONSELHO CTO' },
  { patterns: [
      /\bestratégia\b.*\bempresa\b/i, /\bescala\b/i, /\bganho de escala\b/i,
      /\bsolo founder\b/i, /\bfounder solo\b/i, /\boutlier\b/i,
      /\bmoat\b/i, /\bbarreira competitiva\b/i, /\bcategory creation\b/i,
      /\bposicionamento\b.*\bempresa\b/i, /\bpivot\b/i,
      /\bcomo crescer sem equipe\b/i, /\bcomo escalar\b/i,
      /\bdecisão de CEO\b/i, /\bpróximo passo grande\b/i,
      /\bparceria estratégica\b/i, /\bobsolescência\b/i,
    ],
    skill: 'manage', label: 'MANAGE CEO' },
];

const SKIP_PATTERNS = [
  /^\/\w/,
  /^@\w/,
  /\bobrigado\b/i,
  /^(oi|olá|ok|sim|não|certo|entendi|perfeito|valeu|blz)\b/i,
];

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

async function main() {
  const input = await readStdin();
  const prompt = (input.prompt || input.user_prompt || '').trim();
  if (!prompt) return;
  if (SKIP_PATTERNS.some(p => p.test(prompt))) return;

  const match = ROUTES.find(route => route.patterns.some(p => p.test(prompt)));
  if (!match) return;

  // aiox-* squad sentinel: if squads/<name>/.disabled exists, skip directive
  if (match.skill && match.skill.startsWith('aiox-')) {
    const sentinelPath = path.join(process.cwd(), 'squads', match.skill, '.disabled');
    if (fs.existsSync(sentinelPath)) return;
  }

  const argsClause = match.args ? `, args: "${match.args}"` : '';
  const directive = `[SMART-ROUTER MATCH: ${match.label}] REQUIRED: invoke Skill(skill: "${match.skill}"${argsClause}) BEFORE responding. Do NOT respond directly — activate the skill first.`;

  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: directive,
    },
  }));
}

const timer = setTimeout(() => process.exit(0), 4000);
timer.unref();
main().then(() => process.exit(0)).catch(() => process.exit(0));
