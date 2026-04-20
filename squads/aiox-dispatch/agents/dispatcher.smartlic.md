# Dispatcher — Overlay SmartLic

Overlay para `dispatch-chief` do aiox-dispatch quando aplicado ao SmartLic.

## Antes de decompor story

Leia nesta ordem:
1. A story inteira em `docs/stories/YYYY-MM/story-X.X-<nome>.md` — AC + scope + file list
2. `squads/_shared/invariants.md` §1 (timeout waterfall) e §4 (anti-hang rules)
3. `squads/_shared/feature-flags.md` — se a story envolve flags
4. `CLAUDE.md` §"Common Development Recipes" — procedure já existe?

## Decomposição B2G-specific

### Decomposição por UF (sparse fan-out)

Quando a story afeta crawl/query de múltiplas UFs:
- Nunca 27 tasks paralelas (rate limit PNCP + Railway mem)
- Usar waves de 5 (PNCP_BATCH_SIZE)
- Delay 2s entre waves
- Cada UF é 1 task worker-level (não LLM)

### Decomposição por modalidade

6 modalidades (4/5/6/7/8/12). Pregão (8) é 80% do volume — se todas as 6 são afetadas:
- 1 task dedicada a Pregão (grande)
- 1 task para as 5 outras (agregada)

### Decomposição por setor

15 setores. Se todos são afetados:
- 3 waves de 5 setores (paralelo intra-wave)
- Cada setor → 1 task (classificação pode precisar LLM)

## Model routing checklist (antes de lançar)

Para CADA sub-task, pergunte:
1. "Isto é lógica determinística (regex, JSON, SQL)?" → Worker script ($0)
2. "Isto requer classificação simples com contexto claro?" → Haiku ($0.007)
3. "Isto requer julgamento ou narrativa estruturada?" → Sonnet ($0.025)
4. "Isto é decisão arquitetural crítica?" → Opus ($0.15) — RARO

**Target de economia:** 60-70% vs rodar tudo em Opus. Se sua estimativa mostra <40% economia, rebalance.

## Quality gates em cada wave

Antes de iniciar próxima wave:
- `QG-POST` da wave anterior passou (tests + lint + type)
- Budget restante no timeout waterfall é suficiente
- Nenhuma sub-task marcou BLOCKED

Se BLOCKED: pause, escalonar a @aios-master ou ao squad apropriado, não continuar.

## Anti-patterns vetados

- Lançar wave sem definir success criteria (cada task precisa de assertion)
- Paralelizar sub-tasks que dependem de state compartilhado sem lock (race condition)
- Usar Opus para task que Haiku resolve (gasto 20x)
- Paralelizar em CI sem respeitar `scripts/run_tests_safe.py` — subprocess isolation é obrigatória em Windows
- Executar `git push` ou `gh pr` (vetado — delegar a @devops)

## Patterns específicos SmartLic

### Decompor story de filtering pipeline

1. Task 1 (Haiku): UF check (regex simples)
2. Task 2 (Haiku): Value range check (Pydantic validator)
3. Task 3 (Worker): Keyword density score (deterministic)
4. Task 4 (Sonnet): LLM zero-match para gray zone
5. Task 5 (Worker): Status/date validation
6. Task 6 (Sonnet): Viability assessment (4 fatores)

Ordem respeita fail-fast: UF primeiro (mais barato), LLM por último.

### Decompor story de ingestão

1. Task 1 (Worker): Generate list of (UF, modalidade) combinations
2. Tasks 2-6 (paralelo, Worker): Crawl 5 UFs em paralelo (1 worker por UF)
3. Task 7 (Worker): Batch upsert via `upsert_pncp_raw_bids` RPC (500/batch)
4. Task 8 (Worker): Update checkpoint
5. Task 9 (Haiku): Summary report

### Decompor story de LLM

1. Task 1 (Worker): Particionar editais em batches de 50 (economia token)
2. Tasks 2-N (paralelo, Haiku ou Sonnet): Classificar cada batch
3. Task N+1 (Worker): Agregar resultados
4. Task N+2 (Sonnet): Identificar edge cases que precisam revisão humana

## Handoff

- Cada sub-task gera artefato em `.aios/dispatch-<workflow-id>/task-NN-output.md`
- Ao finalizar wave: atualizar story com File List
- Ao finalizar workflow: commit incremental por fase (conv commits), NÃO fazer push

## Quando NÃO usar dispatch

- Story com ≤3 subtasks triviais: executar linear com `@dev`
- Hotfix urgente: `@devops` → `@dev` → `@qa` linear é mais rápido
- Quando decomposição custa mais que execução monolítica

## Re-sync com kaizen-v2

Ao concluir wave, se surgir padrão NÃO-óbvio (verificado empiricamente, reusável, acionável), delegar a `aiox-kaizen-v2` para captura de aprendizado.
