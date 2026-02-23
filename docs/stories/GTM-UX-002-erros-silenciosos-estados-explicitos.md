# GTM-UX-002: Erros Silenciosos → Estados de Erro Explicitos

## Epic
Root Cause — UX (EPIC-GTM-ROOT)

## Sprint
Sprint 7: GTM Root Cause — Tier 2

## Prioridade
P1

## Estimativa
8h

## Descricao

Historico, Dashboard, Mensagens e Pipeline retornam dados vazios quando a API falha, fazendo o usuario pensar que nao tem dados. O Dashboard mostra zeros em vez de erro durante outage. Sessoes silenciosamente retornam array vazio. O usuario pagante ve dashboard zerado e pensa que o sistema esta "sem dados" — quando na verdade e um erro de comunicacao com o backend.

### Situacao Atual

| Pagina | Comportamento em Erro | Problema |
|--------|-----------------------|----------|
| `/historico` | Mostra "Nenhuma busca salva" | Nao diferencia "sem dados" de "erro de carga" |
| `/dashboard` | Mostra zeros nos graficos | Analytics retorna 200 com zeros em vez de 503 |
| `/mensagens` | Mostra "Sem conversas" | Erro silencioso |
| `/pipeline` | Mostra pipeline vazio | Erro silencioso |
| `/sessions` | Lista vazia | try/catch engole erro, retorna `[]` |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| UX-ISSUE-010 | UX | Dashboard zerado durante outage — usuario pensa que nao tem dados |
| ERROR-015 | QA | Historico engole erros e mostra empty state |
| ERROR-016 | QA | Pipeline engole erros |
| ERROR-017 | QA | Mensagens engole erros |

## Criterios de Aceite

### Historico

- [ ] AC1: Quando `/api/sessions` falha, mostrar error state: "Nao foi possivel carregar seu historico. [Tentar novamente]"
- [ ] AC2: Distinguir visualmente "Nenhuma busca salva" (empty, tom informativo) de "Erro ao carregar" (error, tom warning)

### Dashboard

- [ ] AC3: Quando `/api/analytics` falha, backend retorna 503 (nao 200 com zeros)
- [ ] AC4: Frontend mostra error state em cada card do dashboard: "Dados indisponiveis. [Tentar novamente]"
- [ ] AC5: Cards individuais podem falhar independentemente (1 card com erro, outros funcionando)

### Mensagens

- [ ] AC6: Quando `/api/messages` falha, mostrar error state com retry
- [ ] AC7: Distinguir "Sem conversas" (empty) de "Erro ao carregar" (error)

### Pipeline

- [ ] AC8: Quando `/api/pipeline` falha, mostrar error state com retry
- [ ] AC9: Pipeline em modo leitura durante erro (pode ver colunas, nao pode drag-and-drop)

### Padrao Comum

- [ ] AC10: Componente reutilizavel `ErrorStateWithRetry.tsx` com: icone, mensagem, botao retry, timestamp do erro
- [ ] AC11: Cada pagina com data fetching implementa 3 estados: loading → data | empty | error

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="error-state|historico|dashboard" --no-coverage
cd backend && pytest -k "test_analytics_error" --no-coverage
```

- [ ] T1: Historico mostra error state quando API falha
- [ ] T2: Dashboard mostra error state (nao zeros) quando API falha
- [ ] T3: Backend analytics retorna 503 quando Supabase indisponivel
- [ ] T4: Retry button funciona e recarrega dados
- [ ] T5: Empty state diferente de error state visualmente

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/components/ErrorStateWithRetry.tsx` | Criar — componente reutilizavel |
| `frontend/app/historico/page.tsx` | Modificar — 3 estados (loading/data/error) |
| `frontend/app/dashboard/page.tsx` | Modificar — error state per-card |
| `frontend/app/mensagens/page.tsx` | Modificar — error state |
| `frontend/app/pipeline/page.tsx` | Modificar — error state |
| `backend/routes/analytics.py` | Modificar — retornar 503 em vez de zeros |
| `backend/routes/sessions.py` | Modificar — nao engolir erros |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | GTM-UX-001 | Banner unico complementa error states |
| Paralela | GTM-PROXY-001 | Mensagens sanitizadas complementam |
