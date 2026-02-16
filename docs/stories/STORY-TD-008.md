# STORY-TD-008: PNCP Client Consolidation -- Inicio

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 1: Seguranca e Correcoes

## Prioridade
P1

## Estimativa
5h

## Descricao

Esta story inicia a consolidacao dos dois HTTP clients duplicados para comunicacao com a API PNCP. O arquivo `pncp_client.py` tem ~1585 linhas com implementacoes sync (`requests`) e async (`httpx`) duplicadas, incluindo logica de retry, rate limiting e error handling repetida em ambas.

**Fase 1 (esta story):** Investigacao e preparacao.

1. **Auditoria de uso do sync client (2h)** -- Verificar todos os code paths que usam `PNCPLegacyAdapter.fetch()` ou qualquer metodo do sync client. Documentar se algum path ativo depende do sync client. Se nenhum path ativo o utiliza, a remocao e segura.

2. **Preparacao para migracacao (2h)** -- Se sync client ainda e usado:
   - Identificar chamadas que precisam ser migradas para async
   - Criar plano de migracacao com testes de regressao
   - Garantir que fallback single-UF funciona com async client

3. **Quick wins de cleanup (1h)** -- Enquanto investiga:
   - Corrigir `_request_count` nunca resetado (SYS-20, LOW) -- implementar reset ou remover
   - Corrigir `asyncio.get_event_loop().time()` deprecated (SYS-21, LOW) -- usar `get_running_loop()`

## Itens de Debito Relacionados
- SYS-02 (CRITICAL): Dual HTTP client implementations (sync + async) -- ~1585 linhas
- SYS-20 (LOW): `_request_count` nunca resetado
- SYS-21 (LOW): `asyncio.get_event_loop().time()` deprecated em Python 3.10+

## Criterios de Aceite

### Auditoria
- [x] Documento de auditoria: lista todos os callers de `PNCPLegacyAdapter.fetch()`
- [x] Documento de auditoria: lista todos os callers de metodos sync do PNCP client
- [x] Classificacao de cada caller: ativo em producao / dead code / test only
- [x] Decisao documentada: remover sync client ou migrar callers para async

### Quick Wins
- [x] `_request_count` corrigido: resetado periodicamente ou removido
- [x] `asyncio.get_event_loop().time()` substituido por `asyncio.get_running_loop().time()`
- [x] Testes existentes continuam passando

### Preparacao
- [x] Se sync client sera removido: lista de testes que precisam atualizar
- [x] Se sync callers serao migrados: PRs de migracao planejados
- [x] Estimativa refinada para TD-009 (conclusao) baseada na investigacao

## Testes Requeridos

- Testes existentes de `pncp_client.py` devem continuar passando
- `grep -r "get_event_loop().time" backend/` retorna zero matches apos fix

## Dependencias
- **Blocks:** STORY-TD-009 (conclusao da consolidacao depende da investigacao aqui)
- **Blocked by:** Nenhuma

## Riscos
- **CR-04:** Eliminacao do sync client pode quebrar fallback single-UF. A auditoria desta story e projetada exatamente para mitigar este risco.
- Se PNCPLegacyAdapter for usado em producao, a migracao sera mais complexa e TD-009 pode precisar de mais horas.

## Rollback Plan
- Quick wins (SYS-20, SYS-21) sao reversiveis trivialmente.
- A investigacao em si nao muda codigo de producao.

## Definition of Done
- [x] Auditoria documentada
- [x] Quick wins implementados e revisados
- [x] Testes passando
- [ ] CI/CD green
- [x] Estimativa refinada para TD-009
