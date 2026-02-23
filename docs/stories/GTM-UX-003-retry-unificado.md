# GTM-UX-003: Unificar Retry UX (Eliminar Cooldown 30s + Dual Mechanism)

## Epic
Root Cause — UX (EPIC-GTM-ROOT)

## Sprint
Sprint 7: GTM Root Cause — Tier 2

## Prioridade
P1

## Estimativa
6h

## Descricao

Existem 2 mecanismos de retry competindo na pagina de busca: auto-retry do CRIT-008 (10s→20s→30s com countdown circular) e botao manual com cooldown de 30 segundos. O auto-retry sempre diz "O servidor esta reiniciando" para qualquer erro transiente — mesmo quando o servidor NAO esta reiniciando (ex: timeout da fonte PNCP). O cooldown de 30s e excessivo e frustra o usuario.

### Situacao Atual

| Mecanismo | Componente | Problema |
|-----------|-----------|----------|
| Auto-retry CRIT-008 | `useSearch.ts` | Mensagem "servidor reiniciando" para TODO erro transiente |
| Cooldown 30s | `SearchResults.tsx` | 30s e excessivo, frustante |
| Countdown circular | `SearchResults.tsx` | Bonito mas confuso com botao manual |
| Botao "Tentar agora" | `SearchResults.tsx` | Compete com auto-retry |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| UX-ISSUE-001 | UX | Auto-retry diz "reiniciando" para qualquer erro transiente |
| UX-ISSUE-002 | UX | Cooldown 30s excessivo — 5-10s seria adequado |
| UX-ISSUE-003 | UX | Dual mechanism (auto + manual) confunde usuario |

## Criterios de Aceite

### Mecanismo Unico

- [x] AC1: UM unico mecanismo de retry: auto-retry com botao "Tentar agora" integrado
- [x] AC2: Cooldown reduzido: 5s → 10s → 15s (nao 10s→20s→30s)
- [x] AC3: Maximo 3 tentativas automaticas (manter)

### Mensagens Contextuais

- [x] AC4: Erro de timeout PNCP: "A consulta esta demorando mais que o esperado. Tentando novamente..."
- [x] AC5: Erro 502/503/504: "Servico temporariamente indisponivel. Tentando novamente..."
- [x] AC6: Erro de rede: "Sem conexao com o servidor. Verificando..."
- [x] AC7: NUNCA dizer "servidor reiniciando" a menos que health probe confirme restart

### UX Simplificada

- [x] AC8: Countdown numerico simples (nao circular SVG) — "Tentando em 5s... [Tentar agora]"
- [x] AC9: Apos 3 falhas: "Nao foi possivel completar a busca. [Tentar novamente] [Ver resultados parciais]"
- [x] AC10: Se houver resultados parciais, mostrar com banner (nao esconder)
- [x] AC11: Remover cooldown de 30s do botao manual

## Testes Obrigatorios

```bash
cd frontend && npm test -- --testPathPattern="retry-unified|useSearch" --no-coverage
```

- [x] T1: Auto-retry usa mensagem contextual (nao "reiniciando")
- [x] T2: Cooldown 5s→10s→15s (nao 10s→20s→30s)
- [x] T3: Botao "Tentar agora" funciona sem cooldown extra
- [x] T4: Apos 3 falhas mostra opcao de resultados parciais
- [x] T5: Apenas 1 mecanismo de retry ativo

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/buscar/hooks/useSearch.ts` | Modificar — mensagens contextuais, cooldown reduzido |
| `frontend/app/buscar/components/SearchResults.tsx` | Modificar — remover dual mechanism, simplificar UI |
| `frontend/lib/error-messages.ts` | Modificar — adicionar mensagens contextuais por tipo de erro |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | GTM-UX-001 | Banner unico complementa retry |
| Paralela | GTM-PROXY-001 | Erros sanitizados melhoram mensagens de retry |
