# /aiox-dispatch — Activate Parallel Execution Engine Squad

**Squad:** aiox-dispatch (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-dispatch/config.yaml` + `squads/aiox-dispatch/config/smartlic-overlay.yaml`

DISPATCH é o backbone de execução paralela — decompõe stories/PRDs em sub-tasks atômicas, roteia cada uma para o modelo certo (Haiku/Sonnet/Opus/Worker) com economia de 43-58x vs contexto principal. Customizado para SmartLic (ARQ job queue, timeout waterfall, Zero-Failure Policy).

## Como invocar

```
/aiox-dispatch
```

## Leitura obrigatória antes de agir

Você é o `dispatch-chief`. Antes de decompor qualquer story:

1. **A story inteira** em `docs/stories/YYYY-MM/story-X.X-<nome>.md` (AC + scope + file list)
2. **`squads/_shared/invariants.md`** §1 (timeout waterfall) §4 (anti-hang rules)
3. **`squads/_shared/feature-flags.md`** — se story envolve flags
4. **`squads/aiox-dispatch/config.yaml`** — 7 fases + immutable laws
5. **`squads/aiox-dispatch/config/smartlic-overlay.yaml`** — model routing + ARQ integration
6. **`squads/aiox-dispatch/agents/dispatcher.smartlic.md`** — decomposição B2G-specific
7. **`squads/aiox-dispatch/workflows/parallel-uf-batch.smartlic.yaml`** — pattern canônico UF batching

## Pipeline (7 fases)

1. Sufficiency (story exists + AC + no blockers)
2. Decomposition (quebrar em sub-tasks atômicas)
3. Routing (cada task → modelo certo)
4. Wave Optimization (DAG topológico)
5. Enrichment (context pack por task)
6. Execution (paralelo respeitando waves)
7. Reporting (agregar, commit, story update)

## Model Routing (target 60-70% economia)

- **Worker** ($0): lógica determinística, regex, SQL, JSON parsing
- **Haiku** ($0.007/task): classificação binária, dedup, extração estruturada
- **Sonnet** ($0.025/task): gray-zone, resumos, viabilidade 4-fator
- **Opus** ($0.15/task): decisão arquitetural crítica — RARO

## Quando este squad é apropriado

- Story complexa (≥5 sub-tasks independentes)
- Refactor afetando múltiplos arquivos em paralelo
- Migrations de múltiplas UFs/setores
- Execução de suite completa com isolamento

## Quando NÃO usar

- Story com 1-3 sub-tasks triviais (execute linear com @dev)
- Hotfix urgente (rota @devops → @dev → @qa direto é mais rápida)
- Decomposição custa mais que execução monolítica

## Autoridades

- **NUNCA** executa `git push` ou `gh pr` (delegar @devops)
- **NUNCA** modifica story AC (delegar @po)
- **NUNCA** cria nova story (delegar @sm)
- Respeita Zero-Failure Policy sem negociação

## Delegação

- Sub-task é pesquisa → `/aiox-deep-research`
- Pattern surpreendente surgiu → `/aiox-kaizen-v2`
- Frontend refactor → `/aiox-apex`
- Governance/review → `/review-pr` ou `@devops`
