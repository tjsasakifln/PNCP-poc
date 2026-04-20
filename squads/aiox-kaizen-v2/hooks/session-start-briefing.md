# SessionStart Briefing — Integração com `.claude/hooks/squads-briefing.cjs`

O aiox-kaizen-v2 NÃO implementa seu próprio hook SessionStart. O hook canônico do SmartLic é:

**`.claude/hooks/squads-briefing.cjs`** (criado em `squads-integration`)

Este hook:
1. Lê `squads/aiox-*/squad.yaml` — catálogo de squads disponíveis
2. (Opcional) Lê `.synapse/patterns/*.yaml` top-5 com R(t) > 0.5
3. Envelopa em `additionalContext` XML-tagged
4. **Hard budget: 2048 bytes**

## Anatomia do payload

```xml
<squads-aiox-available>
  SmartLic tem 6 squads aiox disponíveis para auto-invocação via /comando ou hook:
  - aiox-apex: frontend intelligence (Next 16 + SSE + Tailwind)
  - aiox-deep-research: pesquisa B2G multi-fonte (PNCP/PCP/ComprasGov/DataLake)
  - aiox-dispatch: paralelização determinística de stories complexas
  - aiox-kaizen-v2: memória + learning loop Ebbinghaus
  - aiox-seo: supplier_contracts inbound orgânico
  - aiox-legal-analyst: Lei 14.133 + jurisprudência licitatória

  Active patterns (top 5, kaizen):
  1. [CI_DRIFT_POST_407] main ~150 failures clusterizados; STORY-BTS-011 sweep (R=0.85)
  2. [CACHE_WARMING_DEPRECATION] warming jobs removidos; DataLake <100ms (R=0.72)
  3. [BUNDLE_SIZE_RECAL] cap 1.75MB; target -600KB STORY-5.14 (R=0.65)
  ...
</squads-aiox-available>
```

## Responsabilidade do kaizen

1. Manter `.synapse/patterns/<id>.yaml` atualizado (strength + last_mentioned)
2. Computar R(t) atual quando o hook lê (não pre-computar — data staleness)
3. Ordenar por R(t) descendente e retornar top-5

## Pattern file format

```yaml
# .synapse/patterns/<id>.yaml
id: "CI_DRIFT_POST_407"
created_at: "2026-04-20T10:00:00Z"
last_mentioned_at: "2026-04-20T17:30:00Z"
strength: 3
short_description: "main ~150 failures clusterizados; STORY-BTS-011 sweep"
full_description: |
  Pós PR #407 (2026-04-15), CI em main acumulou ~150 test failures distribuídos
  em 8-10 clusters. NÃO são flaky — são regressões genuínas de múltiplas stories
  mergeadas sem validação completa. STORY-BTS-011 é o sweep em andamento.
  PR #424 pré-clearou 4 clusters.
sources:
  - "Memory: project_ci_drift_post_407.md"
  - "PR: #424"
  - "Story: docs/stories/BTS-011"
supersedes: []
superseded_by: null
promoted_to_claude_md: false
```

## Timing — hook performance

- Hook DEVE completar em <500ms (SessionStart não pode bloquear)
- Se pattern file está unreadable: silent skip (não falhar SessionStart)
- Se nenhum pattern existe: retornar apenas catálogo de squads

## Fallback sem kaizen

Se `.synapse/patterns/` não existir ou estiver vazio, o hook retorna apenas:

```xml
<squads-aiox-available>
  SmartLic tem 6 squads aiox disponíveis: aiox-apex, aiox-deep-research,
  aiox-dispatch, aiox-kaizen-v2, aiox-seo, aiox-legal-analyst.
  Invoque via /aiox-<nome> ou deixe o smart-router rotear automaticamente.
</squads-aiox-available>
```

Isso garante que o hook funciona desde o dia 1, mesmo sem kaizen ter acumulado patterns.
