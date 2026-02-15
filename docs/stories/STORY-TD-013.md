# STORY-TD-013: Testes Unitarios para Nova Arquitetura de Busca

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 3: Qualidade e Cobertura

## Prioridade
P2

## Estimativa
16h

## Descricao

Esta story cria testes unitarios abrangentes para a nova arquitetura de busca implementada em TD-012 (SearchContext, reducer, sub-hooks). Tambem reescreve os testes de quarentena que dependiam de SearchForm/SearchResults para funcionar com a nova arquitetura.

**Trabalho (Cluster G.4 do assessment):**

1. **Testes do reducer (4h)** -- O reducer e uma pure function, portanto testavel sem React. Testar todas as actions, edge cases, e estado inicial.

2. **Testes de sub-hooks (6h)** -- `useUFSelection`, `useDateRange`, `useSectorFilter`, `useSearchExecution` -- cada um com testes independentes usando `@testing-library/react-hooks`.

3. **Testes de SearchResults.tsx (6h)** -- Componente core de 678 linhas que anteriormente nao tinha testes (FE-09). Agora que usa Context em vez de 35 props, os testes sao mais limpos.

4. **Reescrita de testes quarantined (incluso)** -- Testes de useSearch e useSearchFilters que permaneceram em quarentena (TD-011) sao reescritos para a nova arquitetura e reativados.

## Itens de Debito Relacionados
- FE-09 (MEDIUM): Sem testes para SearchResults.tsx (678 linhas)
- FE-04 (HIGH): Testes quarantined restantes (que dependiam de SearchForm/SearchResults)
- SYS-01 (LOW): Frontend test coverage abaixo de 60%

## Criterios de Aceite

### Testes do Reducer
- [ ] Teste para cada action type definida no reducer
- [ ] Teste para estado inicial
- [ ] Teste para actions com payload invalido (edge cases)
- [ ] Teste para combinacoes de actions (ex: SET_UF -> SEARCH_START -> SEARCH_COMPLETE)
- [ ] Reducer testado como pure function (sem React, sem mocks)

### Testes de Sub-hooks
- [ ] `useUFSelection`: selecao, desselecao, selecionar todos, limpar
- [ ] `useDateRange`: definir range, validacao de datas, defaults
- [ ] `useSectorFilter`: selecao de setor, mudanca de setor
- [ ] `useSearchExecution`: iniciar busca, cancelar, retry, error handling

### Testes de SearchResults
- [ ] Renderiza resultados corretamente (dados mockados)
- [ ] Estado vazio (0 resultados)
- [ ] Estado de loading
- [ ] Estado de erro
- [ ] Download de Excel (mock)
- [ ] Paginacao (se aplicavel)
- [ ] LicitacaoCard renderiza campos corretos

### Quarentena
- [ ] Testes de useSearch reescritos e movidos de quarentena
- [ ] Testes de useSearchFilters reescritos para sub-hooks
- [ ] `__tests__/quarantine/` tem menos arquivos que antes de TD-011+TD-013

### Metricas
- [ ] Frontend test coverage >= 55% (progresso em direcao ao 60% threshold)
- [ ] Diretorio `buscar/` com coverage >= 70%

## Testes Requeridos

- Todos os novos testes passam no CI
- Coverage do diretorio `buscar/` medido e documentado
- Nenhum teste existente quebrou

## Dependencias
- **Blocks:** Nenhuma diretamente (mas contribui para meta de 60% coverage)
- **Blocked by:** STORY-TD-012 (nova arquitetura deve existir para escrever testes)

## Riscos
- Se TD-012 atrasar, esta story atrasa tambem.
- Testes de hooks com Context podem ser mais complexos que esperado. Usar `renderHook` com wrapper de Provider.

## Rollback Plan
- Testes sao aditivos. Nao ha rollback necessario.
- Se testes forem flaky: marcar como skip temporariamente e investigar.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario)
- [ ] CI/CD green
- [ ] Coverage frontend documentado (antes/depois)
- [ ] Quarentena reduzida (contagem documentada)
