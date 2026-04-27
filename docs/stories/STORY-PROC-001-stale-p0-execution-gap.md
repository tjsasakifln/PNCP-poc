# STORY-PROC-001: Investigar gap de execução — P0 stories Ready há 14+ dias sem ser puxadas

## Status

**Ready (criada e aprovada @po 2026-04-27)**

## Prioridade

🔴 **P0 (governance)** — bloqueia execução de outras P0 técnicas

## Origem

- Inspeção GSC root-cause 2026-04-27 (`docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §10.2)
- Validação @po STORY-INC-001 2026-04-27 — descobriu que 4 stories Ready (incluindo 2 P0) cobrem 100% do "novo P0 incident"

## Tipo

Process / Governance / Meta

## Owner

@pm + @po (decisão organizacional, não engenharia)

## Story

**As a** time SmartLic operando produção com 5 dias de degradação backend,
**I want** entender por que `SEN-BE-001` (P0) e `SEN-BE-008` (P0) estão Status:Ready desde 2026-04-23 sem ser puxadas para implementação,
**so that** a causa raiz organizacional seja endereçada e o padrão não repita (degradação >5d enquanto stories de fix existem mas não saem do backlog).

## Problema

Sessão de root-cause GSC 2026-04-27 produziu **STORY-INC-001 (P0 incident)** propondo fix para outage backend completo. Validação @po revelou:

| Story Ready | Data | Prioridade | Cobertura |
|-------------|------|-----------|-----------|
| `SEN-BE-001-db-statement-timeout` | 2026-04-23 | **P0** | 100% do statement_timeout + ConnectionTerminated |
| `SEN-BE-005-sitemap-contratos-orgao-502` | 2026-04-23 | P1 | sitemap_contratos_orgao 502 |
| `SEN-BE-007-slow-sitemap-endpoints` | 2026-04-23 | P1 | TODOS sitemap endpoints lentos |
| `SEN-BE-008-slow-request-core-routes` | 2026-04-23 | **P0** | /health, /v1/me, /v1/empresa, /v1/orgao stats |

**STORY-INC-001 foi withdrawn** (100% duplicado por essas 4 stories). **Mas elas existem, são P0, e não foram puxadas em 14 dias enquanto o backend degradava.**

Brief raiz §10.2 já perguntava: *"por que SEN-BE-005 ficou Ready 14d?"* — pergunta válida e ainda sem resposta.

## Critérios de Aceite

- [ ] **AC1:** @pm + @po fazem retrospective curta (≤30min) respondendo: por que `SEN-BE-001` (P0) e `SEN-BE-008` (P0) ficaram Ready 14+ dias sem alocação?
  - Hipótese A: capacidade insuficiente (devs alocados em outro epic com mais visibilidade)
  - Hipótese B: blocker técnico oculto (story Ready mas dev tentou e travou — não documentado)
  - Hipótese C: prioridade real != prioridade declarada (P0 escrito, mas time tratou como P2)
  - Hipótese D: story passou despercebida (sem ritual de pull semanal)
- [ ] **AC2:** Output documentado em `docs/process/2026-04-27-stale-p0-postmortem.md` — máximo 200 palavras, sem culpa, focado em causa estrutural
- [ ] **AC3:** Decisão sobre 1 mecanismo de prevenção a implementar:
  - Opção A: ritual semanal de "P0 sweep" (PM percorre todas P0 Ready, valida ainda P0, aloca ou re-prioriza)
  - Opção B: SLA explícito: P0 Ready → atribuído em 24h, in-progress em 72h
  - Opção C: alerta automático (script que monitora `.story.md` Status:Ready P0 + age >5d → notifica PM)
  - Opção D: outra (especificar)
- [ ] **AC4:** Mecanismo escolhido implementado em 7 dias (track via subtask)
- [ ] **AC5:** Re-medição em 30d: contagem de stories P0 Status:Ready com age >7d. Meta: 0.

### Anti-requisitos

- **NÃO** transformar isso em caça-bruxas individual — foco em causa estrutural
- **NÃO** abolir o status `Ready` ou criar burocracia adicional sem ROI claro
- **NÃO** re-priorizar SEN-BE-001/008 para "Pull AGORA" sem antes resolver causa estrutural — caso contrário a próxima P0 stale só vai aparecer em 14d de novo

## Tasks / Subtasks

- [ ] Task 1 — Retrospective curta (AC: 1, 2)
- [ ] Task 2 — Decisão de mecanismo (AC: 3)
- [ ] Task 3 — Implementar mecanismo (AC: 4)
- [ ] Task 4 — Re-medição (AC: 5)

## Referência

- Brief raiz: `docs/sessions/2026-04/2026-04-27-gsc-rootcause-brief-for-sm.md` §"P0 INCIDENTE VIVO" + §10.2
- Story withdrawn evidence: `docs/stories/STORY-INC-001-backend-db-pool-exhaustion-2026-04-27.md` §"Verdict @po"
- Stories afetadas: `docs/stories/SEN-BE-{001,005,007,008}*.md`

## Riscos

- **R1 (Médio):** Retrospective pode revelar conflito interno de priorização que requer decisão de fundador — escalar se chegar nesse ponto, não tentar resolver na story
- **R2 (Baixo):** Mecanismo proposto pode ser ignorado em 2 semanas sem accountability — definir KPI mensurável (AC5)

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-27 | @po (Sarah) | Story criada após validação STORY-INC-001 evidenciar gap organizacional (4 stories Ready 14d cobrindo 100% do "novo incident"). Status: Ready imediato (não precisa Draft — escopo é meta-process, não código). |
