# Epic: Pre-GTM Technical Surgery — SmartLic v3

**Epic ID:** DEBT-v3
**Date:** 2026-03-31
**Owner:** @pm (Morgan)
**Status:** PLANNING
**Supersedes:** `epic-technical-debt-v2.md` (v2.0 — facades/monitoring sem eliminacao real)

---

## Filosofia

**Cirurgia, nao inventario.**

O v2 gastou ~200h criando facades, monitoring e subpackages sem reduzir complexidade real. O v3 faz o oposto: 3 sprints focados em **deletar codigo, eliminar riscos e melhorar conversao** — e nada mais.

**Criterio de "bom o suficiente":** SmartLic e um POC pre-revenue em beta. Perfeicao e inimiga de shipping. Quando S1-S3 passam, o debito restante e aceitavel para este estagio. Nao havera v4.

**Regras anti-loop:**
1. Meta = deletar, nao mover. Cada AC mede reducao, nao reorganizacao.
2. Itens LOW que nao afetam usuario ou seguranca: eliminados do backlog.
3. Proibido rodar brownfield discovery v4.
4. Feature freeze durante S3.

---

## Escopo

### Incluido (3 sprints, ~115h, R$17.250)

| Sprint | Foco | Horas | Entrega |
|--------|------|-------|---------|
| S1: Seguranca | DB SECURITY DEFINER + retention | 15h | 0 funcoes vulneraveis, 5 tabelas com cleanup |
| S2: Conversao | UX que converte trials em pagantes | 40h | LCP <2.5s, 0 buscas stuck, error UX humanizado |
| S3: Simplificacao | Deletar codigo — reducao real de LOC | 60h | Backend LOC reduz >=15% (medido por cloc) |

### Excluido (deliberadamente)

- **77h de "polish backlog"** (24 itens LOW) — eliminados. Se importassem, nao seriam LOW.
- **SIGSEGV investigation** (24h) — blocked por cryptography upstream. Nao investir ate >200 buscas/dia.
- **Migration squash** (24h) — cosmetico. 106 files nao afetam runtime.
- **Feature flag governance** (8h) — flags cresceram de 29→45 no v2 "governando". Parar de governar, deletar as que nao sao usadas.
- **Monorepo tooling** (8h) — premature para 1 dev.
- **Qualquer reorganizacao que nao reduza LOC total.**

**Total eliminado: ~329h de trabalho que nao move a agulha do GTM.**

---

## Criterios de Sucesso

| Metrica | Baseline | Meta | Como medir |
|---------|----------|------|------------|
| Funcoes SECURITY DEFINER sem SET search_path | 10 | 0 | `grep -c` nas migrations |
| Tabelas com retention automatica | 0 | 5+ | `SELECT * FROM cron.job` |
| Landing LCP mobile 4G | ~3.5s | <2.5s | Lighthouse CI |
| Buscas "stuck" sem feedback >45s | ~10% | 0% | Prometheus `smartlic_sse_stall_total` |
| Error messages tecnicos visiveis ao usuario | Sim (524, retry counter) | 0 | Manual QA |
| Backend LOC total (excl. tests) | ~50K+ | Reducao >=15% | `cloc backend/ --exclude-dir=tests,venv` |
| Modulos >1000 LOC | 10+ | <=3 | `wc -l` |
| Testes backend | 7656+ pass | 7656+ pass, 0 novos fail | `run_tests_safe.py` |
| Testes frontend | 5733+ pass | 5733+ pass, 0 novos fail | `npm test` |

---

## Sprint S1: Seguranca (15h — 2-3 dias)

**Squad:** @data-engineer (lead) + @dev (implementacao) + @qa (validacao)
**Story:** [DEBT-v3-S1](story-debt-v3-S1-seguranca.md)

**O que faz:**
- Corrige SET search_path em TODAS as funcoes SECURITY DEFINER (DB-001, DB-022, DB-021)
- Cria pg_cron retention para 5 tabelas sem cleanup (DB-008, DB-023, DB-010)
- Remove 2 indexes redundantes (DB-014, DB-015)
- Renomeia 4 triggers com prefixo legacy (DB-011)
- Adiciona composite indexes que faltam (DB-019)

**ACs mensuráveis:**
- `grep -rn "SECURITY DEFINER" supabase/migrations/ | grep -v "SET search_path"` retorna 0
- `SELECT count(*) FROM cron.job WHERE command LIKE '%DELETE%'` >= 5
- Migration unica, idemponent, testada em staging

**Nao faz:** Squash de migrations, reorganizacao de schema, nada cosmetico.

---

## Sprint S2: Conversao (40h — 1 semana)

**Squad:** @dev (lead backend) + @ux-design-expert (lead frontend) + @qa (validacao)
**Story:** [DEBT-v3-S2](story-debt-v3-S2-conversao.md)

**O que faz:**

### Backend (10h)
- SYS-014: Prometheus counters para custo LLM (`smartlic_llm_api_cost_dollars`, `smartlic_llm_tokens_total`) — 6h
- FE-001/CROSS-001: Novos SSE events durante filtering/LLM phase (progress nao fica stuck em 78%) — 4h

### Frontend (30h)
- FE-001: UI "demorando mais que o esperado" aos 45s com opcao de resultados parciais — 6h
- FE-006: Auto-retry silencioso (2 tentativas), banner calmo so apos esgotar — 6h
- FE-007: BannerStack max 2 visiveis, auto-collapse informacional apos 5s — 4h
- FE-033: Landing page RSC — converter 10/13 componentes para Server Components — 10h
- FE-030: Mobile search — collapse descricao para returning users — 4h

**ACs mensuraveis:**
- Lighthouse LCP landing mobile 4G < 2.5s (3 runs, mediana)
- Busca de 27 UFs nao mostra "stuck" — progress atualiza a cada 15s minimo
- Error 524/timeout: usuario ve "Estamos buscando, pode demorar..." — sem codigos HTTP, sem retry counter
- BannerStack: nunca mais de 2 banners visiveis simultaneamente
- Mobile 375px: resultados visiveis sem scroll apos submissao

**Nao faz:** useSearchOrchestration decomp, auth guard unification, directory consolidation — nao afetam conversao.

---

## Sprint S3: Simplificacao (60h — 2 semanas)

**Squad:** @architect (decisoes) + @dev (lead) + @qa (regressao zero)
**Story:** [DEBT-v3-S3](story-debt-v3-S3-simplificacao.md)

**O que faz — DELETAR, nao reorganizar:**

### Eliminacoes diretas (~20h de reducao pura)
- SYS-017: Deletar 4 clients experimentais nao usados (portal_transparencia, querido_diario, licitaja, sanctions) — ~2000 LOC removidos
- SYS-007: Deletar sync PNCP client (legacy) — manter so async — ~800 LOC removidos
- SYS-016: Deletar backward-compat shims em main.py — ~60 LOC removidos
- SYS-018: Deletar dual-hash transition em auth.py — ~50 LOC removidos
- SYS-019: Deletar search_cache.py re-export na root — ~120 LOC removidos
- SYS-009: Deletar root filter_*.py duplicados — ~300 LOC removidos
- Feature flags: Deletar flags sem uso ativo (auditoria via grep, meta: 45→<20) — LOC varia

### Decomposicoes que REDUZEM (nao movem) — (~40h)
- SYS-001: filter/pipeline.py (1883 LOC) — extrair, simplificar, **meta: package total de 6422→<4000 LOC**
- SYS-003: cron_jobs.py (2251 LOC) — extrair em modulos, **deletar codigo morto, meta: total <1500 LOC**
- SYS-004: job_queue.py (2229 LOC) — separar concerns, **meta: total <1500 LOC**

**ACs mensuraveis:**
- `cloc backend/ --exclude-dir=tests,venv,__pycache__` mostra reducao >=15% vs baseline medido no inicio do sprint
- Nenhum modulo individual >1000 LOC (exceto consolidation.py que fica para P2 futuro se necessario)
- `python scripts/run_tests_safe.py --parallel 4` → 0 novos failures
- `grep -r "from portal_transparencia\|from querido_diario\|from licitaja\|from sanctions" backend/` → 0 resultados
- Feature flags ativas < 20 (medido por grep no config.py)

**Nao faz:** Cache decomp (funcional, complexo mas estavel), consolidation.py (1394 LOC, toleravel), schema reorganization.

---

## Timeline

```
Dia 1-3     S1: Seguranca (15h)
            @data-engineer lidera, @dev executa migration, @qa valida

Dia 4-8     S2: Conversao (40h)
            @dev + @ux-design-expert em paralelo (backend SSE + frontend UX)
            @qa valida cada AC ao final

Dia 9-18    S3: Simplificacao (60h)
            @architect decide o que deletar vs manter
            @dev executa em batches: eliminacoes diretas primeiro, decomposicoes depois
            @qa roda suite completa apos cada batch
            Feature freeze durante S3

Dia 19      GTM launch
```

**Total: 18 dias uteis (~3.5 semanas), 115h, R$17.250**

---

## Squad Configuration

```yaml
squad: debt-v3-surgery
mode: sequential-sprints
agents:
  - role: lead-s1
    agent: "@data-engineer"
    scope: S1 (seguranca DB)
  - role: lead-s2-backend
    agent: "@dev"
    scope: S2 backend (SSE, Prometheus)
  - role: lead-s2-frontend
    agent: "@ux-design-expert"
    scope: S2 frontend (LCP, banners, mobile)
  - role: lead-s3-decisions
    agent: "@architect"
    scope: S3 (decide o que deletar)
  - role: lead-s3-execution
    agent: "@dev"
    scope: S3 (executa delecoes e decomposicoes)
  - role: quality-gate
    agent: "@qa"
    scope: Todos os sprints (validacao de ACs, regressao zero)
  - role: orchestrator
    agent: "@pm"
    scope: Tracking, blockers, GTM readiness

rules:
  - "Cada AC deve ser binario (passa/falha) e medivel por CLI"
  - "Nenhuma story pode criar mais codigo do que deleta (exceto testes)"
  - "QA roda suite completa entre sprints"
  - "Feature freeze durante S3"
  - "Se S1+S2 passam e S3 esta em progresso, GTM pode iniciar em paralelo"
```

---

## Risk Register

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| S3 decomposicao causa regressao | Media | Alto | Batches pequenos, suite completa entre cada batch |
| Deletar sync PNCP client quebra fallback | Baixa | Alto | Verificar que async client cobre 100% dos paths antes de deletar |
| Feature flags deletadas ainda em uso | Media | Medio | Grep exhaustivo + 1 semana em staging antes de deploy |
| S2 LCP target nao atingido | Baixa | Medio | 2.5s e conservador; RSC conversion sozinha deve atingir |
| GTM launch encontra bug de seguranca | Baixa | Critico | S1 first — seguranca resolvida antes de tudo |

---

## O que NAO esta neste epic (e por que)

| Item | Horas | Por que excluido |
|------|-------|-----------------|
| SIGSEGV investigation | 24h | Blocked upstream, irrelevante ate >200 buscas/dia |
| Migration squash | 24h | Cosmetico, nao afeta runtime |
| Cache decomposition | 24h | Estavel e funcional, complexo mas nao quebrado |
| useSearchOrchestration decomp | 16h | Nao afeta UX do usuario |
| Auth guard unification | 8h | Funcional, divergencia e DX nao UX |
| Component directory consolidation | 12h | Cosmetico |
| Feature flag governance framework | 8h | v2 tentou e flags cresceram. Deletar > governar |
| 24 itens LOW/P3 | 77h | Nao afetam usuario, seguranca ou conversao |
| Brownfield discovery v4 | ~30h | Proibido. Parar de medir, comecar a cortar |

**Total excluido: ~329h de trabalho que nao move GTM.**

---

## Pos-GTM

Apos lancamento comercial e primeiros clientes pagantes, reavaliar com base em dados reais:
- Se conversao trial→pago < 5%: investir em UX (items excluidos de FE)
- Se latencia reclamada: investir em cache/performance (SYS-005, SYS-006)
- Se >200 buscas/dia: investir em SIGSEGV/scaling (SYS-002, CROSS-006)
- Se equipe cresce: investir em DX (monorepo, squash, directory consolidation)

**Decisoes baseadas em dados de clientes reais, nao em assessment teorico.**

---

## Stories

| ID | Sprint | Titulo | Horas | Lead |
|----|--------|--------|-------|------|
| [DEBT-v3-S1](story-debt-v3-S1-seguranca.md) | S1 | Seguranca DB: SECURITY DEFINER + Retention | 15h | @data-engineer |
| [DEBT-v3-S2](story-debt-v3-S2-conversao.md) | S2 | UX de Conversao: LCP + Search Progress + Error UX | 40h | @dev + @ux-design-expert |
| [DEBT-v3-S3](story-debt-v3-S3-simplificacao.md) | S3 | Simplificacao Real: Deletar Codigo | 60h | @architect + @dev |

**Total: 3 stories, 115h, R$17.250, 18 dias uteis**

---

## Documentos de Referencia

- Assessment completo: [technical-debt-assessment.md](../prd/technical-debt-assessment.md)
- Relatorio executivo: [TECHNICAL-DEBT-REPORT.md](../reports/TECHNICAL-DEBT-REPORT.md)
- Arquitetura: [system-architecture.md](../architecture/system-architecture.md)
- Schema: [SCHEMA.md](../../supabase/docs/SCHEMA.md)
- DB Audit: [DB-AUDIT.md](../../supabase/docs/DB-AUDIT.md)
- Frontend Spec: [frontend-spec.md](../frontend/frontend-spec.md)
- Reviews: [db-specialist-review.md](../reviews/db-specialist-review.md), [ux-specialist-review.md](../reviews/ux-specialist-review.md), [qa-review.md](../reviews/qa-review.md)
