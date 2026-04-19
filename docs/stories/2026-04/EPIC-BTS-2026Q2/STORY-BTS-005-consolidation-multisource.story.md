# STORY-BTS-005 — Consolidation & Multi-Source (19 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1
**Effort:** M (3-5h)
**Agents:** @dev + @qa + @architect (overlap com STORY-CIG-BE-consolidation-helpers-private L-effort)
**Status:** Ready

---

## Contexto

19 testes cobrindo camada de consolidation (dedup, fuzzy matching, multi-source orchestration) + PCP v2 status mapping + circuit breakers específicos por source. **Sobrepõe-se com STORY-CIG-BE-consolidation-helpers-private** (já Ready no epic CI-GREEN); ver se resolver aqui fecha lá também.

Padrão: `ConsolidationService._tokenize_objeto`, `_jaccard`, `_deduplicate`, `_deduplicate_fuzzy`, `_wrap_source` podem ter sido renomeados/inlinados. Testes patcham esses helpers privados.

---

## Arquivos (tests)

- `backend/tests/test_consolidation_multisource.py` (4 failures)
- `backend/tests/test_consolidation_early_return.py` (3 failures)
- `backend/tests/test_multisource_orchestration.py` (1 failure)
- `backend/tests/test_crit054_pcp_status_mapping.py` (3 failures)
- `backend/tests/test_pcp_timeout_isolation.py` (2 failures)
- `backend/tests/test_portal_compras_client.py` (2 failures)
- `backend/tests/test_comprasgov_circuit_breaker.py` (1 failure)
- `backend/tests/test_harden010_comprasgov_disable.py` (3 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_consolidation*.py backend/tests/test_multisource_orchestration.py backend/tests/test_crit054_pcp_status_mapping.py backend/tests/test_pcp_timeout_isolation.py backend/tests/test_portal_compras_client.py backend/tests/test_comprasgov_circuit_breaker.py backend/tests/test_harden010_comprasgov_disable.py -v --timeout=30` exit code 0 (19/19 PASS).
- [ ] AC2: CI verde nesses 8 arquivos.
- [ ] AC3: RCA detalhada. Decidir entre (a) restaurar helpers privados vs (b) reescrever testes para API pública. Se (a) exigir mudança de produção, pair com @architect.
- [ ] AC4: Cobertura não caiu.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] `grep -rn "class ConsolidationService\\|def _tokenize_objeto\\|def _jaccard\\|def _deduplicate\\|def _wrap_source\\|source_health_registry" backend/`
- [ ] Verificar se `STORY-CIG-BE-consolidation-helpers-private` (epic CI-GREEN, Ready) overlapa — coordenar ou mergear stories
- [ ] Para PCP status mapping: confirmar `backend/source_config/pcp_v2_status.py` ou similar não mudou

---

## Dependências

- **Bloqueado por:** BTS-002 (pipeline resilience precisa estar ok antes)
- **Bloqueia:** BTS-006 (search async consome consolidation)
- **Relacionado:** `STORY-CIG-BE-consolidation-helpers-private` (pode ser absorvido)

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 7/10. Gaps: P4 escopo, P7 valor, P8 riscos. Story confirmada Ready. Atenção @dev: coordenar com owner de STORY-CIG-BE-consolidation-helpers-private antes de implementar.
