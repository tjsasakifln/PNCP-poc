# Memory Keeper — Overlay SmartLic

Overlay para `memory-keeper` do aiox-kaizen-v2 integrado ao synapse-engine.cjs existente.

## Coexistência com synapse existente

**NÃO substituir** `.claude/hooks/synapse-engine.cjs` — ele já faz:
- Daily sensing (captura eventos de sessão)
- Session digest (via `precompact-session-digest.cjs`)
- Armazenamento em `.synapse/`

Kaizen-v2 **adiciona** camada semântica:
- Classifica o que é pattern vs noise
- Aplica Ebbinghaus decay
- Injeta top-5 active patterns ao SessionStart (via squads-briefing.cjs)
- Promove/demove patterns conforme reinforcement signals

## Encoding checklist (antes de salvar pattern)

Um pattern NÃO deve ser capturado sem passar pelos 5 critérios:

1. **Verified?** O pattern foi empiricamente validado? (teste, incidente, PR merged)
2. **Non-obvious?** Surpreende quem lê o código? Se é óbvio, não precisa memória.
3. **Reusable?** Acontece em >1 story/sessão? Single-incident = noise.
4. **Actionable?** Sugere ação concreta ("use X em vez de Y"), não observação passiva.
5. **Empirical?** Baseado em dado/incident, não em especulação.

Se falhar em QUALQUER critério: **NÃO** capture. Deixe o synapse-engine logar cru sem promover a pattern.

## Promote pipeline

```
synapse raw event → [kaizen classifier Haiku]
  ├── qualify as pattern? → [encoding check] → .synapse/patterns/<id>.yaml (strength=1)
  └── noise → skip (stay in raw log)

existing pattern mentioned in new session →
  → reinforcement +1 (max 10)

pattern not mentioned in N days →
  → decay R(t) = exp(-t/S_strength)
  → R < 0.2 → move to .synapse/archive/YYYY-MM/
```

## SessionStart briefing integration

O hook `.claude/hooks/squads-briefing.cjs` injeta top-5 patterns com R(t) > 0.5 no `additionalContext`:

```
<squads-aiox-available>
  Active patterns (top 5):
  1. [CI_DRIFT_POST_407] main tem ~150 failures em clusters...
  2. [CACHE_WARMING_DEPRECATION_2026_04_18] warming jobs removidos...
  ...
</squads-aiox-available>
```

Budget TOTAL do hook: 2048 bytes. Patterns individuais: ~150 bytes cada (5 patterns ≈ 750 bytes, + metadata).

## Conflict resolution

Se pattern novo contradiz pattern existente:
1. Consultar evidência ambos (commits, PRs, Sentry events)
2. Marcar o mais antigo como `superseded_by: <new_id>`
3. Registrar lição em `.synapse/lessons/YYYY-MM-DD.md`

## Anti-patterns vetados

- Capturar fatos óbvios do código ("existem testes em backend/tests/")
- Capturar detalhes ephemerals ("em 2026-04-20 eu estava na branch X")
- Capturar políticas já documentadas em CLAUDE.md ("sempre use type hints")
- Capturar decisões one-off ("para esta story, usamos Y")

## Promoting a pattern to CLAUDE.md

Se pattern atinge strength=8 E aparece em ≥3 stories, considerar promover a CLAUDE.md. Isso requer:
- Delegate a @pm ou @architect para review
- Propor mudança via PR
- Remover do .synapse/patterns/ (ou manter como backup)

## Patterns known to track (seed)

Ver `config/smartlic-overlay.yaml` §`known_patterns_to_track` para 5 patterns iniciais que o kaizen deve validar.

## Reporting cadence

- **Weekly (domingo 20h)**: gera `.synapse/reports/YYYY-WW.md` com:
  - Patterns ativos (strength + R(t))
  - Patterns archived na semana
  - Patterns promoted para CLAUDE.md
  - Gaps detectados (áreas com baixa coverage)
  - Recomendações de stories

- **Real-time**: se pattern crítico falha validação (ex: "zero-failure" violado), trigger imediato:
  - Sentry capture_message
  - Delegate a @devops para investigação
