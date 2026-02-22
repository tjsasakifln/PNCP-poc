# TFIX-001: Corrigir acentos ausentes em strings PT-BR (aria-labels e mensagens)

**Status:** Pending
**Prioridade:** Alta
**Estimativa:** 1h
**Arquivos afetados:** 1 componente + 3 test files

## Problema

O componente `EnhancedLoadingProgress.tsx` contém strings em português **sem acentos** (diacríticos), causando falhas em 6+ testes que esperam texto correto.

## Causa Raiz

Ao escrever as strings no componente, os acentos foram omitidos no código-fonte. Não há sanitização — é erro de digitação direta no source code.

### Strings incorretas no componente:

| Linha | Atual (errado) | Correto |
|-------|----------------|---------|
| 57 | `Consultando fontes oficiais de contratacoes publicas` | `Consultando fontes oficiais de contratações públicas` |
| 63 | `Coletando licitacoes dos estados selecionados` | `Coletando licitações dos estados selecionados` |
| 69 | `Aplicando filtros de setor, valor e relevancia` | `Aplicando filtros de setor, valor e relevância` |
| 75 | `Gerando avaliacao estrategica por IA` | `Gerando avaliação estratégica por IA` |
| 107 | `Esta busca esta demorando mais que o normal...` | `Esta busca está demorando mais que o normal...` |
| 116 | `Esta busca esta demorando mais que o normal...` | `Esta busca está demorando mais que o normal...` |
| 280 | `Resultados disponiveis com ressalvas` | `Resultados disponíveis com ressalvas` |
| 281 | `Buscando licitacoes, X% completo` | `Buscando licitações, X% completo` |
| 471 | `serao exibidos quando prontos` | `serão exibidos quando prontos` |

## Testes que serão corrigidos

- `degraded-visual.test.tsx`: 3 falhas (aria-label "disponíveis" e "licitações")
- `EnhancedLoadingProgress.test.tsx`: 3 falhas (aria-label "licitações", overrun "demorando", AC2 "Finalizando busca" text drift)
- `sse-resilience.test.tsx`: 1 falha ("Finalizando busca" — texto mudou, mas componente TAMBÉM tem acento errado)

**Nota:** Os testes AC2 e AC5 do `EnhancedLoadingProgress.test.tsx` também buscam "Finalizando busca" que não existe mais — precisa atualizar esses testes para o texto atual ("progresso em tempo real foi interrompido" / "demorando mais que o normal").

## Critérios de Aceitação

- [ ] AC1: Todas as strings PT-BR em `EnhancedLoadingProgress.tsx` têm acentos corretos
- [ ] AC2: `degraded-visual.test.tsx` — 3 testes passam (15/15 total)
- [ ] AC3: `EnhancedLoadingProgress.test.tsx` — ARIA labels passam
- [ ] AC4: Nenhuma regressão em outros testes

## Solução

Editar `frontend/components/EnhancedLoadingProgress.tsx` corrigindo cada string listada acima.

## Arquivos

- `frontend/components/EnhancedLoadingProgress.tsx` — corrigir strings
