# STORY-TD-011: Unquarantine Testes + E2E Safety Net

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P2

## Estimativa
16h

## Descricao

Esta story reativa testes automatizados que estao em quarentena e cria E2E tests como safety net para o refactor de Search state (TD-012).

**Contexto:** 22 arquivos de teste estao em `frontend/__tests__/quarantine/`, incluindo testes criticos como AuthProvider, useSearch, useSearchFilters, DashboardPage, MensagensPage, ContaPage, LicitacaoCard, LicitacoesPreview. A quarentena foi necessaria por testes falhos, mas significa que fluxos criticos nao tem safety net automatica.

**Estrategia (Cluster G do assessment):**

1. **G.1: Unquarantine testes independentes (8h)** -- Identificar 10-12 testes que NAO dependem de SearchForm/SearchResults (ex: DashboardPage, ContaPage, MensagensPage, LicitacaoCard). Corrigir e mover de volta para `__tests__/`. Estes testes sao independentes do refactor de FE-01/02/03 e podem ser reativados imediatamente.

2. **G.2: E2E Playwright para SearchResults (8h)** -- Criar E2E tests que cobrem o fluxo de busca end-to-end via Playwright. Estes testes sobrevivem ao refactor de componentes (testam comportamento, nao implementacao) e servem como safety net para TD-012.

## Itens de Debito Relacionados
- FE-04 (HIGH): 22 arquivos de teste quarantined em `__tests__/quarantine/`
- FE-09 (MEDIUM): Sem testes para SearchResults.tsx (parcial -- E2E nesta story)

## Criterios de Aceite

### Unquarantine (G.1)
- [ ] 10-12 testes movidos de `__tests__/quarantine/` para `__tests__/`
- [ ] Testes movidos passam no CI
- [ ] Testes que dependem de SearchForm/SearchResults permanecem em quarentena (serao reescritos em TD-013)
- [ ] Inventario: lista de testes reativados e testes que permanecem com razao documentada

### E2E Safety Net (G.2)
- [ ] E2E test: fluxo completo de busca (selecao UF -> data range -> buscar -> resultados)
- [ ] E2E test: download de Excel apos busca
- [ ] E2E test: busca sem resultados mostra empty state
- [ ] E2E test: filtros de busca funcionais (setor, UF, data)
- [ ] E2E tests passam em CI (Chromium + Mobile Safari)
- [ ] E2E tests usam selectors que NAO dependem de implementacao interna (data-testid, texto visivel)

### Metricas
- [ ] Frontend test coverage aumentou em relacao ao baseline (49.46%)
- [ ] Nenhum teste existente quebrou

## Testes Requeridos

- Todos os testes unquarantined devem passar no CI
- E2E Playwright tests devem passar em Chromium e Mobile Safari
- Coverage frontend medido antes e depois

## Dependencias
- **Blocks:** STORY-TD-012 (search state refactor depende dos E2E como safety net)
- **Blocked by:** Nenhuma

## Riscos
- **CR-02:** Se testes unquarantined forem mais complexos de corrigir que estimado, priorizar E2E (G.2) para nao bloquear TD-012.
- Testes de quarentena podem ter dependencias ocultas que requerem mocking extensivo.

## Rollback Plan
- Se testes corrigidos causarem flakiness no CI: mover de volta para quarentena individualmente.
- E2E tests sao aditivos e nao afetam testes existentes.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] Coverage frontend documentado (antes/depois)
- [ ] Inventario de quarentena atualizado
