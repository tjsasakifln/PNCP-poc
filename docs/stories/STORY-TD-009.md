# STORY-TD-009: PNCP Client Consolidation -- Conclusao

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P1

## Estimativa
11h

## Descricao

Esta story conclui a consolidacao dos HTTP clients PNCP, removendo o sync client e mantendo apenas o async. Baseada na investigacao de TD-008.

**Trabalho principal:**

1. **Migrar callers ativos (se houver) para async (4h)** -- Se TD-008 identificou code paths ativos usando sync client, migra-los para usar `AsyncPNCPClient`.

2. **Remover sync client (4h)** -- Eliminar toda a implementacao sync de `pncp_client.py`:
   - Classe sync e seus metodos
   - Import de `requests`
   - `PNCPLegacyAdapter.fetch()` se nao mais necessario
   - Logica de retry/rate limiting duplicada
   - **Reducao esperada:** ~1585 para ~800 linhas

3. **Atualizar testes (3h)** -- Todos os testes que mockavam sync client precisam ser atualizados para async. Verificar cobertura pos-consolidacao.

**Impacto:** Elimina ~785 linhas de codigo duplicado. Toda mudanca de comportamento PNCP passa a ser aplicada em um unico lugar, reduzindo drasticamente o risco de regressao.

## Itens de Debito Relacionados
- SYS-02 (CRITICAL): Dual HTTP client implementations -- conclusao da remocao do sync client

## Criterios de Aceite

### Consolidacao
- [ ] `import requests` removido de `pncp_client.py`
- [ ] Apenas `AsyncPNCPClient` permanece como implementacao PNCP
- [ ] `pncp_client.py` reduzido para < 900 linhas (de ~1585)
- [ ] Nenhuma referencia a sync client em nenhum arquivo do backend
- [ ] `grep -r "import requests" backend/` retorna zero (ou apenas em requirements.txt)

### Funcionalidade
- [ ] Busca multi-UF funciona corretamente apos consolidacao
- [ ] Busca single-UF funciona corretamente (fallback migrado)
- [ ] Retry logic preservada (exponential backoff + jitter)
- [ ] Rate limiting preservado (10 req/s)
- [ ] Circuit breaker preservado
- [ ] Pagination funciona corretamente

### Testes
- [ ] Todos os testes de `pncp_client.py` atualizados para async
- [ ] Coverage de `pncp_client.py` >= 90%
- [ ] Zero testes fazendo referencia ao sync client

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| REG-T05 | Busca multi-UF funciona apos remocao sync client | E2E | P1 |
| -- | Retry logic funciona com async client | Unitario | P1 |
| -- | Rate limiting respeitado | Unitario | P1 |
| -- | Circuit breaker funciona | Unitario | P1 |
| -- | Pagination completa sem erros | Integracao | P1 |

## Dependencias
- **Blocks:** Nenhuma diretamente (mas facilita manutencao futura de todo o PNCP client)
- **Blocked by:** STORY-TD-008 (investigacao e preparacao)

## Riscos
- **CR-04:** Se a investigacao de TD-008 revelou uso ativo do sync client que nao pode ser migrado facilmente, esta story pode precisar de mais horas ou abordagem diferente.
- Risco de regressao em busca: testar extensivamente com E2E antes de merge.

## Rollback Plan
- Se busca quebrar apos consolidacao: reverter commit inteiro e restaurar sync client.
- Manter branch com sync client por 2 semanas apos deploy como safety net.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao + E2E)
- [ ] CI/CD green
- [ ] Backend coverage >= 96% (manter nivel atual)
- [ ] Documentacao atualizada (arquitetura do PNCP client)
- [ ] Deploy em staging verificado
- [ ] Busca multi-UF e single-UF testadas em producao
